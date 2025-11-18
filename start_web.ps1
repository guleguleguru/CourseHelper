# Research TA Agent - Web 界面启动脚本 (PowerShell)

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Research TA Agent - Web Interface" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# API Key should be set in config/.env file
# Or set it manually: $env:OPENAI_API_KEY = "your-key-here"

Write-Host "Starting web server..." -ForegroundColor Yellow
Write-Host "(Make sure config/.env contains your OPENAI_API_KEY)" -ForegroundColor Gray
Write-Host ""

# 启动 Streamlit
streamlit run app.py



