@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==================================================
echo QUALITYTRACK - INICIALIZADOR WINDOWS
 echo ==================================================
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo O Python nao foi localizado.
        echo Instale no site: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    set "PYTHON_CMD=python"
)
if not exist .venv\Scripts\python.exe (
    echo [1/3] Criando o ambiente virtual...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :falha
)
call .venv\Scripts\activate.bat
 echo [2/3] Instalando as dependencias (internet necessaria)...
python -m pip install -r requirements.txt
if errorlevel 1 goto :falha
if not exist qualitytrack.sqlite3 (
    echo [3/3] Primeiro uso: vamos criar seu usuario administrador.
    echo Escolha nome, e-mail e senha propria de no minimo 10 caracteres.
    python -m flask --app app init-admin
    if errorlevel 1 goto :falha
)
echo.
echo =============================================
echo  Abra no navegador: http://127.0.0.1:5000
 echo  Para encerrar use CTRL + C nesta janela.
echo =============================================
python -m flask --app app run --host 127.0.0.1 --port 5000
pause
exit /b 0
:falha
echo.
echo Houve um erro. Tire uma foto desta janela e compartilhe na conversa.
pause
exit /b 1
