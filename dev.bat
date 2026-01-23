@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo =========================================
echo  admin_template 启动菜单
echo =========================================
echo  1. 启动前端（web / dev:antd）
echo  2. 启动后端（backend / uvicorn）
echo -----------------------------------------
echo.

set /p CHOICE=请输入选项（1/2）：

if "%CHOICE%"=="1" goto START_FRONTEND
if "%CHOICE%"=="2" goto START_BACKEND

echo.
echo 输入无效，已退出。
goto END

:START_FRONTEND
cd /d "%ROOT%web"
echo.
echo 当前目录：%CD%

if not exist "node_modules" (
  echo.
  echo 未检测到 web\node_modules，可能尚未安装前端依赖。
  echo 建议先执行：cd web ^&^& pnpm install
  echo.
)

echo 启动前端：npm run dev:antd
npm run dev:antd
goto END

:START_BACKEND
cd /d "%ROOT%backend"
echo.
echo 当前目录：%CD%

if not exist ".venv\\Scripts\\python.exe" (
  echo.
  echo 未检测到 backend\.venv，正在安装后端依赖（uv sync --all-groups）...
  uv sync --all-groups
  if errorlevel 1 (
    echo.
    echo 后端依赖安装失败，请检查网络或 uv 配置后重试。
    goto END
  )
)

echo 启动后端：uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
goto END

:END
echo.
pause
endlocal

