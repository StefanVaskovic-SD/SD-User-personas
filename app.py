#!/usr/bin/env python3
"""
Streamlit Web Application for User Persona Generator
Upload questionnaire CSV files and generate detailed user personas.
"""

import streamlit as st
import pandas as pd
import io
import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path to import persona_generator
sys.path.insert(0, str(Path(__file__).parent))

from persona_generator import (
    QuestionnaireParser,
    GeminiPersonaGenerator,
    PersonaCSVExporter
)

# Page config
st.set_page_config(
    page_title="User Persona Generator",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'personas_generated' not in st.session_state:
    st.session_state.personas_generated = False
if 'personas_data' not in st.session_state:
    st.session_state.personas_data = None
if 'client_info' not in st.session_state:
    st.session_state.client_info = None
if 'csv_data' not in st.session_state:
    st.session_state.csv_data = None
if 'csv_columns' not in st.session_state:
    st.session_state.csv_columns = []
if 'csv_df' not in st.session_state:
    st.session_state.csv_df = None
if 'selected_columns' not in st.session_state:
    st.session_state.selected_columns = {'section': None, 'question': None, 'answer': None}
if 'switch_to_results' not in st.session_state:
    st.session_state.switch_to_results = False

# Header
st.markdown('<div class="main-header">👤 User Persona Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload questionnaire CSV and generate detailed user personas using Gemini AI</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📖 Instructions")
    st.markdown("""
    1. **If you ALREADY have a questionnaire CSV:**
       - Upload your questionnaire CSV file.
       - Then continue from step 4.
    2. **If you DO NOT have a questionnaire CSV:**
       - Take the questions and answers from your existing questionnaire (Word, PDF, email, notes, etc.).
       - Paste that content into an AI chat, upload your questionnaire CSV as an example, and use this prompt (you can copy–paste it):
         > Could you return this content in a CSV file, where questions are in column A and answers are in column B? Please also add a header row with the column names: "question" and "answer". Use uploaded CSV as an example.
       - Download and save the CSV file that the AI returns.
    3. **Upload** the CSV file here in the app.
    4. **Click** on "Generate Personas".
    5. **Download** the generated personas CSV.
    """)

# Load API key from .env file
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY', '')

# Main content
tab1, tab2, tab3 = st.tabs(["📤 Upload & Generate", "📊 Preview Results", "📥 Download"])

# Auto-switch to results tab if personas were just generated
if st.session_state.get('switch_to_results', False):
    st.session_state.switch_to_results = False  # Reset flag
    # Inject JavaScript to click on tab2 after page loads
    st.markdown("""
    <script>
    setTimeout(function() {
        try {
            // Try multiple selectors for Streamlit tabs
            var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
            if (tabs && tabs.length > 1) {
                tabs[1].click();
                return;
            }
            // Alternative selector
            tabs = window.parent.document.querySelectorAll('[role="tablist"] button');
            if (tabs && tabs.length > 1) {
                tabs[1].click();
            }
        } catch(e) {
            console.log('Tab switching error:', e);
        }
    }, 500);
    </script>
    """, unsafe_allow_html=True)

with tab1:
    st.header("Upload Questionnaire CSV")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload your questionnaire CSV file"
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        file_path = f"/tmp/{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Find where CSV headers start (skip metadata rows)
        try:
            header_row_index = None
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if 'Section' in line and 'Question' in line and 'Answer' in line:
                        header_row_index = i
                        break
            
            if header_row_index is None:
                st.error("❌ Could not find CSV header row with Section/Question/Answer columns")
            else:
                # Read CSV starting from header row (header_row_index is the row number, skip rows before it)
                df = pd.read_csv(file_path, encoding='utf-8', skiprows=range(header_row_index))
                st.session_state.csv_df = df
                st.session_state.csv_columns = list(df.columns)
                
                st.success(f"✓ CSV file loaded! Total rows: {len(df)}")
                st.info(f"📄 File: {uploaded_file.name} ({uploaded_file.size} bytes)")
                
                # Show data preview
                with st.expander("🔍 Data Preview", expanded=False):
                    st.dataframe(df.head(10), width='stretch')
                
                st.markdown("---")
                
                # Column selection
                st.markdown("### Select Columns")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    question_col = st.selectbox(
                        "Column with questions:",
                        options=st.session_state.csv_columns,
                        index=st.session_state.csv_columns.index('Question') if 'Question' in st.session_state.csv_columns else 0,
                        help="Column containing questions (e.g., 'Question')"
                    )
                
                with col2:
                    answer_col = st.selectbox(
                        "Column with answers:",
                        options=st.session_state.csv_columns,
                        index=st.session_state.csv_columns.index('Answer') if 'Answer' in st.session_state.csv_columns else 1 if len(st.session_state.csv_columns) > 1 else 0,
                        help="Column containing answers (e.g., 'Answer')"
                    )
                
                st.markdown("---")
                
                # Parse questionnaire with selected columns
                if question_col and answer_col:
                    with st.spinner("📋 Parsing questionnaire..."):
                        try:
                            # Find section column if exists
                            section_col = 'Section' if 'Section' in st.session_state.csv_columns else ''
                            
                            parser = QuestionnaireParser(
                                file_path,
                                section_col=section_col,
                                question_col=question_col,
                                answer_col=answer_col
                            )
                            questionnaire_data = parser.parse()
                            
                            st.session_state.client_info = questionnaire_data['client_info']
                            
                            st.success(f"✓ Successfully parsed!")
                            
                            # Display client info
                            col1, col2 = st.columns(2)
                            with col1:
                                st.info(f"**Client:** {questionnaire_data['client_info'].get('Client Name', 'N/A')}")
                            with col2:
                                st.info(f"**Product:** {questionnaire_data['client_info'].get('Product Name', 'N/A')}")
                            
                            st.info(f"📝 Found {len(questionnaire_data['all_qa'])} Q&A pairs")
                            st.info(f"👥 Found {len(questionnaire_data['persona_qa'])} persona-related Q&A pairs")
                            
                            # Store parsed data in session state for later use
                            st.session_state.questionnaire_data = questionnaire_data
                            
                        except Exception as e:
                            st.error(f"❌ Error parsing questionnaire: {str(e)}")
                            st.exception(e)
                else:
                    st.warning("⚠️ Please select columns for questions and answers")
        
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            st.exception(e)
        
        # Generate personas section (only show if parsed successfully)
        if 'questionnaire_data' in st.session_state and st.session_state.questionnaire_data:
            questionnaire_data = st.session_state.questionnaire_data
            
            st.markdown("---")
            st.markdown("### Generate Personas")
            
            if api_key:
                if st.button("🚀 Generate Personas", type="primary", use_container_width=False):
                    with st.spinner("🤖 Generating personas using Gemini AI... This may take 30-60 seconds..."):
                            try:
                                generator = GeminiPersonaGenerator(api_key=api_key)
                                personas = generator.generate_personas(questionnaire_data)
                                
                                if personas and len(personas) > 0:
                                    st.session_state.personas_generated = True
                                    st.session_state.personas_data = personas
                                    st.session_state.client_info = questionnaire_data['client_info']
                                    
                                    # Create CSV in memory
                                    csv_buffer = io.StringIO()
                                    exporter = PersonaCSVExporter("")
                                    
                                    # Convert to DataFrame for preview and download
                                    rows = []
                                    for persona in personas:
                                        base_row = {
                                            'Client Name': questionnaire_data['client_info'].get('Client Name', ''),
                                            'Product Name': questionnaire_data['client_info'].get('Product Name', ''),
                                            'Persona Name': persona.get('persona_name', ''),
                                            'Persona Type': persona.get('persona_type', ''),
                                        }
                                        
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
                                        
                                        psycho = persona.get('psychographics', {})
                                        base_row.update({
                                            'Values': '; '.join(psycho.get('values', [])) if isinstance(psycho.get('values'), list) else psycho.get('values', ''),
                                            'Motivations': '; '.join(psycho.get('motivations', [])) if isinstance(psycho.get('motivations'), list) else psycho.get('motivations', ''),
                                            'Lifestyle': psycho.get('lifestyle', ''),
                                            'Interests': '; '.join(psycho.get('interests', [])) if isinstance(psycho.get('interests'), list) else psycho.get('interests', ''),
                                        })
                                        
                                        base_row.update({
                                            'Goals': '; '.join(persona.get('goals', [])) if isinstance(persona.get('goals'), list) else persona.get('goals', ''),
                                            'Challenges': '; '.join(persona.get('challenges', [])) if isinstance(persona.get('challenges'), list) else persona.get('challenges', ''),
                                            'Needs': '; '.join(persona.get('needs', [])) if isinstance(persona.get('needs'), list) else persona.get('needs', ''),
                                            'Pain Points': '; '.join(persona.get('pain_points', [])) if isinstance(persona.get('pain_points'), list) else persona.get('pain_points', ''),
                                        })
                                        
                                        behavior = persona.get('behavior', {})
                                        base_row.update({
                                            'Research Style': behavior.get('research_style', ''),
                                            'Decision Making': behavior.get('decision_making', ''),
                                            'Communication Preferences': behavior.get('communication_preferences', ''),
                                            'Online Behavior': behavior.get('online_behavior', ''),
                                        })
                                        
                                        base_row.update({
                                            'Quote': persona.get('quote', ''),
                                            'Key Characteristics': '; '.join(persona.get('key_characteristics', [])) if isinstance(persona.get('key_characteristics'), list) else persona.get('key_characteristics', ''),
                                        })
                                        
                                        rows.append(base_row)
                                    
                                    df = pd.DataFrame(rows)
                                    csv_string = df.to_csv(index=False)
                                    st.session_state.csv_data = csv_string
                                    
                                    st.success(f"✅ Successfully generated {len(personas)} persona(s)!")
                                    st.balloons()
                                    # Set flag to switch to results tab
                                    st.session_state.switch_to_results = True
                                    st.rerun()  # Refresh page and switch to results tab
                                else:
                                    st.error("❌ Failed to generate personas. The API returned an empty response. Please try again or check your API quota.")
                                    st.info("💡 **Tips:**\n- Check if your Gemini API key is valid\n- Verify you have API quota available\n- Try again in a few moments if you hit rate limits")
                                    
                            except Exception as e:
                                error_msg = str(e).lower()
                                if 'rate limit' in error_msg or 'quota' in error_msg:
                                    st.error("❌ **Rate Limit Exceeded**: The API rate limit has been reached. Please wait a few minutes and try again.")
                                elif 'timeout' in error_msg:
                                    st.error("❌ **Timeout Error**: The request took too long. Please try again with a smaller dataset or check your internet connection.")
                                elif 'api key' in error_msg or 'authentication' in error_msg:
                                    st.error("❌ **Authentication Error**: Please check your Gemini API key in the environment variables.")
                                else:
                                    st.error(f"❌ **Error generating personas**: {str(e)}")
                                
                                st.exception(e)
                                st.info("💡 If this error persists, please check the logs for more details.")
            else:
                st.warning("⚠️ Please provide Gemini API key in the sidebar to generate personas.")

with tab2:
    st.header("Preview Generated Personas")
    
    if st.session_state.personas_generated and st.session_state.personas_data:
        personas = st.session_state.personas_data
        
        st.success(f"✅ {len(personas)} persona(s) generated successfully!")
        
        # Display each persona
        for idx, persona in enumerate(personas, 1):
            with st.expander(f"👤 {persona.get('persona_name', f'Persona {idx}')} - {persona.get('persona_type', 'N/A')}", expanded=(idx == 1)):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📊 Demographics")
                    demo = persona.get('demographics', {})
                    st.markdown(f"- **Age:** {demo.get('age_range', 'N/A')}")
                    st.markdown(f"- **Gender:** {demo.get('gender', 'N/A')}")
                    st.markdown(f"- **Location:** {demo.get('location', 'N/A')}")
                    st.markdown(f"- **Income:** {demo.get('income_level', 'N/A')}")
                    st.markdown(f"- **Net Worth:** {demo.get('net_worth', 'N/A')}")
                    st.markdown(f"- **Education:** {demo.get('education', 'N/A')}")
                    st.markdown(f"- **Occupation:** {demo.get('occupation', 'N/A')}")
                    st.markdown(f"- **Family:** {demo.get('family_status', 'N/A')}")
                
                with col2:
                    st.markdown("### 🧠 Psychographics")
                    psycho = persona.get('psychographics', {})
                    st.markdown(f"- **Values:** {', '.join(psycho.get('values', [])) if isinstance(psycho.get('values'), list) else psycho.get('values', 'N/A')}")
                    st.markdown(f"- **Lifestyle:** {psycho.get('lifestyle', 'N/A')}")
                    st.markdown(f"- **Interests:** {', '.join(psycho.get('interests', [])) if isinstance(psycho.get('interests'), list) else psycho.get('interests', 'N/A')}")
                
                st.markdown("### 🎯 Goals")
                goals = persona.get('goals', [])
                if isinstance(goals, list):
                    for goal in goals:
                        st.markdown(f"- {goal}")
                else:
                    st.markdown(f"- {goals}")
                
                st.markdown("### ⚠️ Challenges")
                challenges = persona.get('challenges', [])
                if isinstance(challenges, list):
                    for challenge in challenges:
                        st.markdown(f"- {challenge}")
                else:
                    st.markdown(f"- {challenges}")
                
                st.markdown("### 💡 Needs")
                needs = persona.get('needs', [])
                if isinstance(needs, list):
                    for need in needs:
                        st.markdown(f"- {need}")
                else:
                    st.markdown(f"- {needs}")
                
                st.markdown("### 💬 Quote")
                quote = persona.get('quote', 'N/A')
                st.markdown(f"> {quote}")
                
                st.markdown("### ✨ Key Characteristics")
                characteristics = persona.get('key_characteristics', [])
                if isinstance(characteristics, list):
                    for char in characteristics:
                        st.markdown(f"- {char}")
                else:
                    st.markdown(f"- {characteristics}")
    else:
        st.info("👆 Upload a questionnaire CSV and generate personas to see preview here.")

with tab3:
    st.header("Download Results")
    
    if st.session_state.csv_data:
        st.success("✅ Personas are ready for download!")
        
        client_name = st.session_state.client_info.get('Client Name', 'unknown') if st.session_state.client_info else 'unknown'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"personas_{client_name.replace(' ', '_')}_{timestamp}.csv"
        
        st.download_button(
            label="📥 Download Personas CSV",
            data=st.session_state.csv_data,
            file_name=filename,
            mime="text/csv",
            type="primary",
            use_container_width=False
        )
        
        st.markdown("---")
        
        # Show preview as table
        df = pd.read_csv(io.StringIO(st.session_state.csv_data))
        st.dataframe(df, width='stretch')
    else:
        st.info("👆 Generate personas first to download the CSV file.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 2rem;'>"
    "User Persona Generator | Powered by Gemini AI"
    "</div>",
    unsafe_allow_html=True
)

