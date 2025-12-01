# User Persona Generator

A Streamlit web application for generating detailed user personas from questionnaire CSV files using Google Gemini 2.5 Flash AI.

## 🎯 Overview

This application analyzes questionnaire CSV files and uses Gemini 2.5 Flash AI to generate comprehensive user personas representing ideal clients/users of a product or service.

## ✨ Features

- **CSV Upload**: Drag & drop or browse to upload questionnaire CSV files
- **Column Selection**: Choose which columns contain questions and answers
- **Smart Parsing**: Automatically detects CSV headers and metadata
- **AI-Powered Analysis**: Uses Gemini 2.5 Flash to analyze questionnaire data
- **Detailed Personas**: Generates comprehensive personas with:
  - Demographics (age, gender, location, income, education, occupation)
  - Psychographics (values, motivations, lifestyle, interests)
  - Goals, challenges, needs, and pain points
  - Behavior patterns
  - Representative quotes
- **Preview & Download**: View personas in the app and download as CSV

## 🚀 Local Development

### Prerequisites

- Python 3.9 or higher
- Gemini API Key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/StefanVaskovic-SD/SD-User-personas.git
   cd SD-User-personas
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   
   Create a `.env` file in the project root:
   ```bash
   echo "GEMINI_API_KEY=your-api-key-here" > .env
   ```
   
   Or set as environment variable:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser:**
   Navigate to `http://localhost:8501`

## 📋 CSV File Format

Your questionnaire CSV should have the following structure:

```
Client Name,Your Client Name
Product Name,Your Product Name
Questionnaire Type,web-design-new
Submitted At,2025-01-01T12:00:00.000

Section,Question,Answer,Files
Company & Business,What is your mission?,Our mission is...,,
Target Audience,Who are your customers?,High-net-worth individuals...,,
...
```

Required columns:
- **Section** (optional): Category/section for each Q&A pair
- **Question**: The question text
- **Answer**: The answer text

## 🚢 Deployment on Render

### Setup

1. **Create a new Web Service on Render:**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure the service:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
   - **Environment:** Python 3

3. **Add Environment Variables:**
   - `GEMINI_API_KEY`: Your Gemini API key
   - `GEMINI_MODEL` (optional): Model name (default: `gemini-2.5-flash`)

4. **Deploy:**
   - Click "Create Web Service"
   - Render will automatically deploy your application

## 📊 Output Format

The generated personas CSV includes:

- Client Name, Product Name
- Persona Name, Persona Type (Primary/Secondary/Tertiary)
- Demographics: Age Range, Gender, Location, Income Level, Net Worth, Education, Occupation, Family Status
- Psychographics: Values, Motivations, Lifestyle, Interests
- Goals, Challenges, Needs, Pain Points
- Behavior: Research Style, Decision Making, Communication Preferences, Online Behavior
- Quote: Representative quote in persona's voice
- Key Characteristics: Summary bullet points

## 🛠️ Project Structure

```
SD-User-personas/
├── app.py                 # Streamlit web application
├── persona_generator.py   # Core parsing and AI generation logic
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env                  # Environment variables (not in git)
└── .gitignore            # Git ignore rules
```

## 📦 Dependencies

- `streamlit>=1.28.0` - Web framework
- `google-generativeai>=0.3.0` - Gemini API client
- `pandas>=1.5.0` - CSV processing
- `python-dotenv>=1.0.0` - Environment variable management

## 🔧 How It Works

1. **CSV Upload**: User uploads questionnaire CSV file
2. **Parsing**: Application parses CSV, extracts metadata and Q&A pairs
3. **Column Selection**: User selects which columns contain questions/answers
4. **AI Analysis**: Gemini 2.5 Flash analyzes all questionnaire data
5. **Persona Generation**: Creates 2-3+ detailed personas based on the data
6. **Export**: Users can preview and download personas as CSV

## 🔑 API Key Setup

1. Visit https://makersuite.google.com/app/apikey
2. Create a new API key
3. Add it to your `.env` file or set as environment variable
4. For Render deployment: Add as environment variable in Render dashboard

## 📝 Usage

1. Upload your questionnaire CSV file
2. Select the columns containing questions and answers
3. Review parsed data
4. Click "Generate Personas"
5. Preview results in the "Preview Results" tab
6. Download the CSV file from the "Download" tab

## 🐛 Troubleshooting

**Problem: No Q&A pairs found**
- Ensure your CSV has a header row with "Question" and "Answer" columns
- Check that the selected columns match your CSV structure

**Problem: API errors**
- Verify your `GEMINI_API_KEY` is set correctly
- Check that you have API quota available
- Ensure you're using a valid API key

## 📄 License

This project is created for internal use.

## 🤝 Support

For questions or issues, contact the development team.
