@echo off
REM ================================
REM  尚米 — 一键启动脚本
REM  双击这个文件就能启动服务
REM ================================

cd /d %~dp0

echo.
echo ╔══════════════════════════════════════╗
echo ║                                      ║
echo ║          🏪  尚  米                  ║
echo ║     商家数据一键导出工具              ║
echo ║                                      ║
echo ║  正在检查环境...                     ║
echo ║                                      ║
echo ╚══════════════════════════════════════╝
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b
)

echo ✅ Python 已安装
echo.

REM 安装需要的包
echo 📦 正在安装依赖包...
python -m pip install fastapi uvicorn openpyxl requests -q
echo ✅ 依赖包安装完成
echo.

REM 检查 API Key 是否已配置
findstr "你的高德API Key填在这里" config.py >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  注意：高德API Key 尚未配置！
    echo    请编辑 config.py，填入你的 Key
    echo.
)

echo 🚀 正在启动尚米服务...
echo.
echo 启动完成后，打开浏览器访问：
echo   http://localhost:8000
echo.
echo （如果用手机访问，连同一个WiFi，访问 http://你电脑IP:8000）
echo.
echo 按 Ctrl+C 停止服务
echo ========================================

python run.py

pause
