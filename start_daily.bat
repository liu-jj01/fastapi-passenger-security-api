@echo off
chcp 65001 >nul

cd /d F:\shixi\api_practice

call .venv\Scripts\activate.bat

echo.
echo 正在检查数据库迁移...
alembic upgrade head

if errorlevel 1 (
    echo.
    echo 数据库迁移失败，请检查错误信息。
    cmd /k
)

echo.
echo 正在启动 FastAPI...
echo 接口文档：http://127.0.0.1:8000/docs
echo 按 Ctrl+C 停止服务，窗口不会关闭。
echo.

fastapi dev main.py

echo.
echo FastAPI 已停止。
echo 当前仍在项目目录和虚拟环境中，可以继续输入命令。
echo 例如：pytest -v、alembic current
echo.

cmd /k