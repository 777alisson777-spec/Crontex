@echo off
setlocal
REM ------------------------------------------------------------
REM CRONTEX: normaliza templates/estáticos e remove duplicatas
REM Requisitos: salvar este arquivo na RAIZ do projeto (mesma do manage.py)
REM ------------------------------------------------------------

REM vai para a pasta onde o .bat está
pushd "%~dp0"

set "APP=crontex_ui"

echo [1/4] Garantindo subpasta de templates: %APP%\templates\crontex_ui
if not exist "%APP%\templates\crontex_ui" (
  mkdir "%APP%\templates\crontex_ui" 2>nul
)

echo [2/4] Movendo templates para a pasta namespaced...
if exist "%APP%\templates\login.html" move /Y "%APP%\templates\login.html" "%APP%\templates\crontex_ui\login.html" >nul
if exist "%APP%\templates\dashboard.html" move /Y "%APP%\templates\dashboard.html" "%APP%\templates\crontex_ui\dashboard.html" >nul

echo [3/4] Excluindo duplicatas na RAIZ do projeto (se existirem)...
if exist "templates\login.html" del /Q "templates\login.html"
if exist "templates\dashboard.html" del /Q "templates\dashboard.html"

if exist "static\css\crontex.css" del /Q "static\css\crontex.css"
if exist "static\img\logo.jpeg" del /Q "static\img\logo.jpeg"
if exist "static\img_login.jpeg" del /Q "static\img_login.jpeg"
if exist "static\img_logo.jpeg" del /Q "static\img_logo.jpeg"

echo [4/4] Tentando remover pastas vazias na RAIZ...
rd "static\css" 2>nul
rd "static\img" 2>nul
rd "static" 2>nul
rd "templates" 2>nul

echo.
echo Feito! Templates e estaticos normalizados dentro do app: %APP%
echo - Templates em:   %APP%\templates\crontex_ui\ (login.html, dashboard.html)
echo - Estaticos em:   %APP%\static\css\crontex.css  e  %APP%\static\img\logo.jpeg
echo.

popd
endlocal
exit /b 0