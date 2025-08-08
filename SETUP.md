# 🚀 Quick Setup Guide

## 1. Install Dependencies
```bash
uv sync
```

## 2. Set up API Keys
Create a `.env` file with your API keys:
```bash
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

**Get API Keys:**
- OpenAI: https://platform.openai.com/api-keys
- Serper (free): https://serper.dev/

## 3. Launch the App
```bash
uv run streamlit run streamlit_app.py
```

The app will open at: http://localhost:8501

## 4. Test the System
1. Select a sector (e.g., "Technology")
2. Click "🚀 Start Analysis"
3. Wait for the AI agents to complete their work
4. View results in the "📈 Results" tab

That's it! The system will automatically create memory storage and learn from each analysis. 