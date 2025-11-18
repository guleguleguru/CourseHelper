# Research TA Agent - 重建索引脚本

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Research TA Agent - Rebuild Index" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# API Key should be set in config/.env file
# Or set it manually: $env:OPENAI_API_KEY = "your-key-here"

Write-Host "Starting index building..." -ForegroundColor Yellow
Write-Host "(Make sure config/.env contains your OPENAI_API_KEY)" -ForegroundColor Gray
Write-Host ""

# 运行构建
python build_index.py

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Index building completed!" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"



