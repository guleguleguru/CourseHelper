@echo off
chcp 65001 >nul
echo.
echo ================================================
echo   Research TA Agent - Web Interface
echo ================================================
echo.

REM API Key should be set in config/.env file
REM Or set it manually: set OPENAI_API_KEY=your-key-here

echo Starting web server...
echo.
streamlit run app.py
