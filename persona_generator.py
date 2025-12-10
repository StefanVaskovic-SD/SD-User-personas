#!/usr/bin/env python3
"""
User Persona Generator Tool
Analyzes questionnaire CSV files using Gemini 2.5 Flash to generate comprehensive user personas.
"""

import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
import google.generativeai as genai
from datetime import datetime

# Try to load .env file if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class QuestionnaireParser:
    """Parses questionnaire CSV files and extracts relevant information."""
    
    def __init__(self, csv_path: str, section_col: str = 'Section', question_col: str = 'Question', answer_col: str = 'Answer'):
        self.csv_path = csv_path
        self.client_info = {}
        self.questions_answers = []
        self.persona_section = []
        self.section_col = section_col
        self.question_col = question_col
        self.answer_col = answer_col
        
    def parse(self) -> Dict:
        """Parse the CSV file and extract structured data."""
        import io
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            # Read all lines first
            all_lines = f.readlines()
            
            # Extract metadata from first few rows (before CSV headers)
            header_row_index = None
            for i, line in enumerate(all_lines):
                # Look for the header row - must contain both QUESTION and ANSWER (exact column names)
                line_upper = line.upper()
                # Check if line contains both "QUESTION" and "ANSWER" as separate words/columns
                has_question = (self.question_col and self.question_col.upper() in line_upper) or 'QUESTION' in line_upper
                has_answer = (self.answer_col and self.answer_col.upper() in line_upper) or 'ANSWER' in line_upper
                
                # Must have both QUESTION and ANSWER, and avoid false positives like "QUESTIONNAIRE"
                if has_question and has_answer:
                    # Double check - make sure it's not just "QUESTIONNAIRE TYPE" or similar
                    if ',' in line:  # Should be a CSV line with columns
                        parts = [p.strip().upper() for p in line.split(',')]
                        # Check if QUESTION and ANSWER are actual column headers (not part of other words)
                        if any('QUESTION' == p or (self.question_col and self.question_col.upper() == p) for p in parts) and \
                           any('ANSWER' == p or (self.answer_col and self.answer_col.upper() == p) for p in parts):
                            header_row_index = i
                            break
                
                # Extract metadata from rows before headers
                if ',' in line and header_row_index is None:
                    parts = line.strip().split(',', 1)
                    if len(parts) == 2:
                        key, value = parts
                        self.client_info[key.strip()] = value.strip()
            
            if header_row_index is None:
                # If no header found, try reading from start
                header_row_index = 0
            
            # Create CSV content starting from header row
            csv_content = ''.join(all_lines[header_row_index:])
            
            # Read questions and answers using DictReader
            reader = csv.DictReader(io.StringIO(csv_content))
            
            # Debug: Get available column names
            available_columns = reader.fieldnames if reader.fieldnames else []
            
            # Map column names to actual CSV column names (case-insensitive)
            section_col_name = None
            question_col_name = None
            answer_col_name = None
            
            for col in available_columns:
                if col:
                    col_lower = col.strip().lower()
                    if self.section_col and col_lower == self.section_col.lower():
                        section_col_name = col
                    if self.question_col and col_lower == self.question_col.lower():
                        question_col_name = col
                    if self.answer_col and col_lower == self.answer_col.lower():
                        answer_col_name = col
            
            for row in reader:
                # Use mapped column names
                section = row.get(section_col_name, '').strip() if section_col_name else ''
                question = row.get(question_col_name, '').strip() if question_col_name else ''
                answer = row.get(answer_col_name, '').strip() if answer_col_name else ''
                
                # Skip empty rows
                if not question or not answer:
                    continue
                
                # If no section column, use empty string or 'General'
                if not section:
                    section = 'General'
                
                self.questions_answers.append({
                    'section': section,
                    'question': question,
                    'answer': answer
                })
                
                # Extract persona-related sections
                if section and ('Persona' in section or 'Audience' in section or 'Customer' in section):
                    self.persona_section.append({
                        'section': section,
                        'question': question,
                        'answer': answer
                    })
        
        return {
            'client_info': self.client_info,
            'all_qa': self.questions_answers,
            'persona_qa': self.persona_section
        }
    
    def get_columns(self) -> List[str]:
        """Get list of column names from CSV file."""
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader.fieldnames) if reader.fieldnames else []


class GeminiPersonaGenerator:
    """Uses Gemini 2.5 Flash to generate user personas from questionnaire data."""
    
    def __init__(self, api_key: Optional[str] = None):
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY environment variable not set. "
                    "Please set it or pass api_key parameter."
                )
        
        genai.configure(api_key=api_key)
        # Using Gemini 2.5 Flash model
        model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        self.model = genai.GenerativeModel(model_name)
    
    def generate_personas(self, questionnaire_data: Dict, max_retries: int = 3) -> List[Dict]:
        """Generate comprehensive user personas using Gemini with retry logic."""
        
        # Build prompt with all relevant information
        prompt = self._build_prompt(questionnaire_data)
        
        # Retry logic for API calls
        last_exception = None
        for attempt in range(max_retries):
            try:
                # Generate response with timeout handling
                generation_config = {
                    'temperature': 0.7,
                    'max_output_tokens': 8192,
                }
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                # Check if response has text
                if not hasattr(response, 'text') or not response.text:
                    raise ValueError("Empty response from API")
                
                # Parse JSON response
                try:
                    # Extract JSON from markdown if present
                    text = response.text.strip()
                    
                    # Try to find JSON in markdown code blocks
                    if '```json' in text:
                        text = text.split('```json')[1].split('```')[0].strip()
                    elif '```' in text:
                        # Try to extract from any code block
                        parts = text.split('```')
                        for i, part in enumerate(parts):
                            if '{' in part and '[' in part:
                                text = part.strip()
                                break
                    
                    # Try to find JSON object/array boundaries
                    if not text.startswith('{') and not text.startswith('['):
                        # Look for first { or [
                        start_idx = min(
                            text.find('{') if '{' in text else len(text),
                            text.find('[') if '[' in text else len(text)
                        )
                        if start_idx < len(text):
                            text = text[start_idx:]
                    
                    # Try to find the end of JSON (might be incomplete)
                    if text.count('{') > text.count('}'):
                        # Incomplete JSON - try to close it
                        text += '}' * (text.count('{') - text.count('}'))
                    if text.count('[') > text.count(']'):
                        text += ']' * (text.count('[') - text.count(']'))
                    
                    personas_data = json.loads(text)
                    
                    # Handle both direct list and wrapped in object
                    if isinstance(personas_data, list):
                        return personas_data
                    elif isinstance(personas_data, dict):
                        return personas_data.get('personas', [])
                    else:
                        raise ValueError(f"Unexpected response format: {type(personas_data)}")
                        
                except json.JSONDecodeError as e:
                    # Log the error for debugging
                    print(f"JSON parsing error (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"Response text (first 500 chars): {response.text[:500]}")
                    
                    # If this is the last attempt, try fallback parser
                    if attempt == max_retries - 1:
                        return self._parse_text_response(response.text)
                    # Otherwise, wait and retry
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()
                
                # Check if it's a retryable error
                retryable_errors = ['rate limit', 'quota', 'timeout', '503', '429', '500', '502']
                is_retryable = any(err in error_msg for err in retryable_errors)
                
                print(f"API error (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1 and is_retryable:
                    # Wait before retrying (exponential backoff)
                    wait_time = 2 ** attempt
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Non-retryable error or last attempt
                    raise Exception(f"Failed to generate personas after {attempt + 1} attempts: {str(e)}")
        
        # If we get here, all retries failed
        if last_exception:
            raise Exception(f"Failed to generate personas: {str(last_exception)}")
        raise Exception("Failed to generate personas: Unknown error")
    
    def _build_prompt(self, data: Dict) -> str:
        """Build comprehensive prompt for Gemini."""
        
        client_name = data['client_info'].get('Client Name', 'Unknown')
        product_name = data['client_info'].get('Product Name', 'Unknown')
        
        # Collect all relevant information
        all_text = []
        all_text.append(f"CLIENT: {client_name}")
        all_text.append(f"PRODUCT: {product_name}\n")
        
        # Add all questions and answers
        all_text.append("QUESTIONNAIRE DATA:\n")
        for qa in data['all_qa']:
            all_text.append(f"Section: {qa['section']}")
            all_text.append(f"Q: {qa['question']}")
            all_text.append(f"A: {qa['answer']}\n")
        
        questionnaire_text = "\n".join(all_text)
        
        prompt = f"""You are an expert user research and UX strategist. Analyze the following questionnaire data and create comprehensive User Personas.

{questionnaire_text}

Based on this questionnaire, create detailed user personas that represent the ideal clients/users for this product/service.

For each persona, provide:
1. Persona Name - A memorable, descriptive name
2. Persona Type - Primary, Secondary, or Tertiary
3. Demographics - Age range, gender, location, income level, education, occupation
4. Psychographics - Values, motivations, lifestyle, interests
5. Goals - What they want to achieve
6. Challenges - Problems they face
7. Needs - What they need from the product/service
8. Pain Points - Specific frustrations
9. Behavior - How they behave, research, make decisions
10. Quote - A representative quote in their voice
11. Key Characteristics - 5-7 bullet points summarizing them

Return your response as a JSON object with this structure:
{{
  "personas": [
    {{
      "persona_name": "Name",
      "persona_type": "Primary/Secondary/Tertiary",
      "demographics": {{
        "age_range": "35-55",
        "gender": "Mixed (60% M, 40% F)",
        "location": "Primary: UK, Germany, Middle East",
        "income_level": "€200,000+ annual",
        "net_worth": "€1M+",
        "education": "University degree or higher",
        "occupation": "Business owners, C-level executives",
        "family_status": "Married/partnered, often with children"
      }},
      "psychographics": {{
        "values": ["value1", "value2"],
        "motivations": ["motivation1", "motivation2"],
        "lifestyle": "Description",
        "interests": ["interest1", "interest2"]
      }},
      "goals": [
        "Goal 1",
        "Goal 2"
      ],
      "challenges": [
        "Challenge 1",
        "Challenge 2"
      ],
      "needs": [
        "Need 1",
        "Need 2"
      ],
      "pain_points": [
        "Pain point 1",
        "Pain point 2"
      ],
      "behavior": {{
        "research_style": "Description",
        "decision_making": "Description",
        "communication_preferences": "Description",
        "online_behavior": "Description"
      }},
      "quote": "\"A representative quote in their voice\"",
      "key_characteristics": [
        "Characteristic 1",
        "Characteristic 2",
        "Characteristic 3"
      ]
    }}
  ]
}}

Identify at least 2-3 distinct personas based on the questionnaire data. Be thorough and specific."""
        
        return prompt
    
    def _parse_text_response(self, text: str) -> List[Dict]:
        """Fallback parser for text responses when JSON parsing fails."""
        print("Warning: Using fallback text parser. JSON format preferred.")
        
        # Try to extract JSON-like structures from text
        try:
            # Try to find JSON objects
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, text, re.DOTALL)
            
            if matches:
                # Try to parse the largest match (likely the full response)
                largest_match = max(matches, key=len)
                try:
                    data = json.loads(largest_match)
                    if isinstance(data, dict) and 'personas' in data:
                        return data['personas']
                    elif isinstance(data, list):
                        return data
                except json.JSONDecodeError:
                    pass
            
            # If no valid JSON found, return empty list
            print(f"Could not extract valid JSON from response. Response length: {len(text)}")
            return []
        except Exception as e:
            print(f"Error in fallback parser: {e}")
            return []


class PersonaCSVExporter:
    """Exports personas to CSV format."""
    
    def __init__(self, output_path: str):
        self.output_path = output_path
    
    def export(self, personas: List[Dict], client_info: Dict):
        """Export personas to CSV file."""
        
        if not personas:
            print("No personas to export.")
            return
        
        # Flatten persona data for CSV
        rows = []
        
        for persona in personas:
            base_row = {
                'Client Name': client_info.get('Client Name', ''),
                'Product Name': client_info.get('Product Name', ''),
                'Persona Name': persona.get('persona_name', ''),
                'Persona Type': persona.get('persona_type', ''),
            }
            
            # Demographics
            demo = persona.get('demographics', {})
            base_row.update({
                'Age Range': demo.get('age_range', ''),
                'Gender': demo.get('gender', ''),
                'Location': demo.get('location', ''),
                'Income Level': demo.get('income_level', ''),
                'Net Worth': demo.get('net_worth', ''),
                'Education': demo.get('education', ''),
                'Occupation': demo.get('occupation', ''),
                'Family Status': demo.get('family_status', ''),
            })
            
            # Psychographics
            psycho = persona.get('psychographics', {})
            base_row.update({
                'Values': '; '.join(psycho.get('values', [])) if isinstance(psycho.get('values'), list) else psycho.get('values', ''),
                'Motivations': '; '.join(psycho.get('motivations', [])) if isinstance(psycho.get('motivations'), list) else psycho.get('motivations', ''),
                'Lifestyle': psycho.get('lifestyle', ''),
                'Interests': '; '.join(psycho.get('interests', [])) if isinstance(psycho.get('interests'), list) else psycho.get('interests', ''),
            })
            
            # Goals, Challenges, Needs, Pain Points
            base_row.update({
                'Goals': '; '.join(persona.get('goals', [])) if isinstance(persona.get('goals'), list) else persona.get('goals', ''),
                'Challenges': '; '.join(persona.get('challenges', [])) if isinstance(persona.get('challenges'), list) else persona.get('challenges', ''),
                'Needs': '; '.join(persona.get('needs', [])) if isinstance(persona.get('needs'), list) else persona.get('needs', ''),
                'Pain Points': '; '.join(persona.get('pain_points', [])) if isinstance(persona.get('pain_points'), list) else persona.get('pain_points', ''),
            })
            
            # Behavior
            behavior = persona.get('behavior', {})
            base_row.update({
                'Research Style': behavior.get('research_style', ''),
                'Decision Making': behavior.get('decision_making', ''),
                'Communication Preferences': behavior.get('communication_preferences', ''),
                'Online Behavior': behavior.get('online_behavior', ''),
            })
            
            # Quote and Characteristics
            base_row.update({
                'Quote': persona.get('quote', ''),
                'Key Characteristics': '; '.join(persona.get('key_characteristics', [])) if isinstance(persona.get('key_characteristics'), list) else persona.get('key_characteristics', ''),
            })
            
            rows.append(base_row)
        
        # Write to CSV
        if rows:
            fieldnames = list(rows[0].keys())
            
            with open(self.output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            print(f"✓ Successfully exported {len(rows)} persona(s) to {self.output_path}")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate User Personas from Questionnaire CSV using Gemini 2.5 Flash'
    )
    parser.add_argument(
        'input_csv',
        type=str,
        help='Path to input questionnaire CSV file'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Path to output CSV file (default: personas_<timestamp>.csv)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='Gemini API key (or set GEMINI_API_KEY env variable)'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_csv):
        print(f"Error: Input file not found: {args.input_csv}")
        sys.exit(1)
    
    # Set output path
    if args.output is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = Path(args.input_csv).stem
        output_dir = Path(args.input_csv).parent
        args.output = str(output_dir / f"personas_{base_name}_{timestamp}.csv")
    
    print(f"📋 Parsing questionnaire: {args.input_csv}")
    
    # Parse questionnaire
    parser = QuestionnaireParser(args.input_csv)
    questionnaire_data = parser.parse()
    
    print(f"✓ Found {len(questionnaire_data['all_qa'])} Q&A pairs")
    print(f"✓ Found {len(questionnaire_data['persona_qa'])} persona-related Q&A pairs")
    
    # Generate personas
    print(f"\n🤖 Generating personas using Gemini 2.5 Flash...")
    try:
        generator = GeminiPersonaGenerator(api_key=args.api_key)
        personas = generator.generate_personas(questionnaire_data)
        
        if not personas:
            print("Error: No personas generated. Please check the API response.")
            sys.exit(1)
        
        print(f"✓ Generated {len(personas)} persona(s)")
        
    except Exception as e:
        print(f"Error generating personas: {e}")
        sys.exit(1)
    
    # Export to CSV
    print(f"\n💾 Exporting to CSV: {args.output}")
    exporter = PersonaCSVExporter(args.output)
    exporter.export(personas, questionnaire_data['client_info'])
    
    print(f"\n✅ Complete! Personas saved to: {args.output}")


if __name__ == '__main__':
    main()

