@echo off
chcp 65001 >nul
echo.
echo ================================================
echo   Research TA Agent - Rebuild Index
echo ================================================
echo.

REM API Key should be set in config/.env file
REM Or set it manually: set OPENAI_API_KEY=your-key-here

echo Starting index building...
echo.
python build_index.py

echo.
echo ================================================
echo   Index building completed!
echo ================================================
echo.
pause



