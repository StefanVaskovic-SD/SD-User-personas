#!/usr/bin/env python3
"""
Streamlit Web Application for User Persona Generator
Upload questionnaire CSV files and generate detailed user personas.
"""

import streamlit as st
import pandas as pd
import io
import sys
import base64
from pathlib import Path
from datetime import datetime

# Add current directory to path to import persona_generator
sys.path.insert(0, str(Path(__file__).parent))

# Load fonts as base64
def load_font_base64(font_path):
    """Load font file and return as base64 string"""
    font_file = Path(__file__).parent / font_path
    if font_file.exists():
        with open(font_file, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    return None

# Load fonts
font_regular_b64 = load_font_base64('fonts/SuisseIntl-Regular.woff2')
font_bold_b64 = load_font_base64('fonts/SuisseIntl-Bold.woff2')

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
font_face_css = ""
if font_regular_b64:
    font_face_css += f"""
    @font-face {{
        font-family: 'Suisse Intl';
        src: url(data:font/woff2;base64,{font_regular_b64}) format('woff2');
        font-weight: normal;
        font-style: normal;
        font-display: swap;
    }}
    """
if font_bold_b64:
    font_face_css += f"""
    @font-face {{
        font-family: 'Suisse Intl';
        src: url(data:font/woff2;base64,{font_bold_b64}) format('woff2');
        font-weight: bold;
        font-style: normal;
        font-display: swap;
    }}
    """

css_content = """
<style>
    /* Font faces */
    """ + font_face_css + """
    
    /* Main background - dark theme */
    .stApp {
        background-color: #080808;
        color: #f5f5f7;
        font-family: 'Suisse Intl', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Main content area */
    .main .block-container {
        background-color: #080808;
        color: #f5f5f7;
    }
    
    /* Headers */
    .main-header {
        font-family: 'Suisse Intl', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 3rem;
        font-weight: bold;
        color: #f5f5f7;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-family: 'Suisse Intl', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 1.2rem;
        font-weight: normal;
        color: rgba(245, 245, 247, 0.7);
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Buttons - white */
    .stButton>button {
        font-family: 'Suisse Intl', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        width: 100%;
        background-color: #f5f5f7;
        color: #080808;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: rgba(245, 245, 247, 0.9);
    }
    
    /* Prompt box */
    .prompt-box {
        border: 1px solid rgba(245, 245, 247, 0.15);
        border-left: 4px solid #f5f5f7;
        border-radius: 4px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        white-space: pre-wrap;
        position: relative;
        background-color: rgba(245, 245, 247, 0.03);
        color: #f5f5f7;
    }
    
    /* Sidebar - different shade to separate from main background */
    section[data-testid="stSidebar"] {
        width: 380px !important;
        background-color: #0f0f0f;
        border-right: 1px solid rgba(245, 245, 247, 0.1);
    }
    
    /* Sidebar text */
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] li,
    section[data-testid="stSidebar"] strong {
        color: #f5f5f7 !important;
    }
    
    /* Dividers and borders */
    hr {
        border-color: rgba(245, 245, 247, 0.1);
    }
    
    /* Main text color */
    .stMarkdown, p, li {
        font-family: 'Suisse Intl', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-weight: normal;
        color: #f5f5f7;
    }
    
    /* Headings - bold */
    h1, h2, h3, h4, h5, h6, strong {
        font-family: 'Suisse Intl', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-weight: bold;
        color: #f5f5f7;
    }
    
    /* Success and info boxes */
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: rgba(245, 245, 247, 0.05);
        border: 1px solid rgba(245, 245, 247, 0.15);
        color: #f5f5f7;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: rgba(245, 245, 247, 0.05);
        border: 1px solid rgba(245, 245, 247, 0.15);
        color: #f5f5f7;
        margin: 1rem 0;
    }
    
    /* Streamlit default elements */
    .stSuccess {
        background-color: rgba(245, 245, 247, 0.05);
        border-color: rgba(245, 245, 247, 0.15);
        color: #f5f5f7;
    }
    
    .stInfo {
        background-color: rgba(245, 245, 247, 0.05);
        border-color: rgba(245, 245, 247, 0.15);
        color: #f5f5f7;
    }
    
    .stWarning {
        background-color: rgba(245, 245, 247, 0.05);
        border-color: rgba(245, 245, 247, 0.15);
        color: #f5f5f7;
    }
    
    /* Header - remove default background */
    .stAppHeader {
        background-color: #080808 !important;
        border-bottom: 1px solid rgba(245, 245, 247, 0.1);
    }
</style>
"""

st.markdown(css_content, unsafe_allow_html=True)

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
st.markdown('<div class="sub-header">Generate user personas from the Discovery questionnaire.</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### How to use this tool")
    
    st.markdown("**Step 1: prepare .csv file**")
    st.markdown("""
    - If you haven't used other Studio Direction tools already: take the questions and answers from the questionnaire you have (Word, PDF, email, notes, etc.) and paste that content into an AI chat, upload your questionnaire CSV as an example, and use this prompt:
    """)
    st.markdown("""
    <div class="prompt-box">Could you return this content in a CSV file, where questions are in column A and answers are in column B? Please also add a header row with the column names: "question" and "answer". Use uploaded CSV as an example.</div>
    """, unsafe_allow_html=True)
    st.markdown("""
    - If you already have output from other Studio Direction tools skip this step.
    """)
    
    st.markdown("**Step 2: import data**")
    st.markdown("""
    - Upload the CSV file here in the app.
    """)
    
    st.markdown("**Step 3: download**")
    st.markdown("""
    - Click on "Generate Personas".
    - Download the generated personas CSV.
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
    st.header("Import data")
    
    uploaded_file = st.file_uploader(
        "See instructions on the left and prepare a .csv file (max limit: 200MB).",
        type=['csv']
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        file_path = f"/tmp/{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Find where CSV headers start (skip metadata rows)
        try:
            header_row_index = None
            df = None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    line_upper = line.upper()
                    # Check for both formats:
                    # 1. Full format: Section, Question, Answer
                    # 2. Simple format: Question, Answer (or question, answer)
                    has_question = 'QUESTION' in line_upper
                    has_answer = 'ANSWER' in line_upper
                    
                    # Must have both question and answer columns
                    if has_question and has_answer and ',' in line:
                        # Validate that these are column headers (not part of other words)
                        parts = [p.strip().upper() for p in line.split(',')]
                        question_col_found = any(p == 'QUESTION' for p in parts)
                        answer_col_found = any(p == 'ANSWER' for p in parts)
                        
                        if question_col_found and answer_col_found:
                            header_row_index = i
                            break
            
            # Read CSV file
            if header_row_index is not None:
                # Read CSV starting from header row (if header_row_index > 0, skip rows before it)
                if header_row_index > 0:
                    df = pd.read_csv(file_path, encoding='utf-8', skiprows=range(header_row_index))
                else:
                    df = pd.read_csv(file_path, encoding='utf-8')
            else:
                # Try reading from the start (maybe it's a simple CSV without metadata rows)
                df = pd.read_csv(file_path, encoding='utf-8')
            
            # Validate that CSV has question/answer columns (case-insensitive)
            col_names_lower = [col.lower().strip() for col in df.columns]
            if 'question' in col_names_lower and 'answer' in col_names_lower:
                st.session_state.csv_df = df
                st.session_state.csv_columns = list(df.columns)
            else:
                st.error("❌ Could not find CSV header row with Question/Answer columns. Please ensure your CSV has 'question' and 'answer' columns (or 'Question' and 'Answer').")
                df = None
            
            if df is not None:
                
                st.success(f"✓ CSV file loaded! Total rows: {len(df)}")
                st.info(f"📄 File: {uploaded_file.name} ({uploaded_file.size} bytes)")
                
                # Automatically detect columns (case-insensitive)
                question_col = None
                answer_col = None
                section_col = ''
                
                for col in st.session_state.csv_columns:
                    col_lower = col.lower().strip()
                    if col_lower == 'question':
                        question_col = col
                    elif col_lower == 'answer':
                        answer_col = col
                    elif col_lower == 'section':
                        section_col = col
                
                # Parse questionnaire with auto-detected columns
                if question_col and answer_col:
                    with st.spinner("📋 Parsing questionnaire..."):
                        try:
                            parser = QuestionnaireParser(
                                file_path,
                                section_col=section_col,
                                question_col=question_col,
                                answer_col=answer_col
                            )
                            questionnaire_data = parser.parse()
                            
                            st.session_state.client_info = questionnaire_data['client_info']
                            
                            # Store parsed data in session state for later use
                            st.session_state.questionnaire_data = questionnaire_data
                            
                        except Exception as e:
                            st.error(f"❌ Error parsing questionnaire: {str(e)}")
                            st.exception(e)
                else:
                    st.error("❌ Could not find 'question' and 'answer' columns in CSV file. Please ensure your CSV has these columns.")
        
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            st.exception(e)
        
        # Generate personas section (only show if parsed successfully)
        if 'questionnaire_data' in st.session_state and st.session_state.questionnaire_data:
            questionnaire_data = st.session_state.questionnaire_data
            
            st.markdown("---")
            
            if api_key:
                button_text = "🔄 Regenerate Personas" if st.session_state.personas_generated else "🚀 Generate Personas"
                if st.button(button_text, type="primary", use_container_width=False):
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



