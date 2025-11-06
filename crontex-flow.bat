@echo off
setlocal ENABLEDELAYEDEXPANSION

:: ===========================
:: CONFIG (edite se precisar)
:: ===========================
:: Caminho do repo (usa a pasta atual por padrão)
set REPO_PATH=%CD%

:: Remotos
set ORIGIN=origin

:: Branch base (fonte de verdade)
set BASE=dev.crontex

:: Python/Django
set PYTHON=python
set DJANGO_SETTINGS=crontex.settings

:: Deploy (dev server)
set DEPLOY_HOST=deploy@54.233.94.203
set DEPLOY_APP_DIR=/srv/dev/app

:: ===========================
:: Router
:: ===========================
if "%~1"=="" goto :help
if /I "%~1"=="help" goto :help
if /I "%~1"=="start" goto :start
if /I "%~1"=="cont" goto :cont
if /I "%~1"=="test" goto :test
if /I "%~1"=="publish" goto :publish
if /I "%~1"=="sync-base" goto :syncbase
if /I "%~1"=="deploy-dev" goto :deploydev

echo [x] Comando inválido. Use: help
exit /b 1

:help
echo.
echo Uso:
echo   crontex-flow start ^<feature^>        - cria branch a partir de %BASE% e faz primeiro push
echo   crontex-flow cont ^<feature^>         - continua feature existente (fetch/switch/pull)
echo   crontex-flow test                     - roda pytest (-q) com --ds=%DJANGO_SETTINGS%
echo   crontex-flow publish ^<feature^> [m]  - add/commit/push da feature para %ORIGIN% (msg opcional)
echo   crontex-flow sync-base                - atualiza sua %BASE% local a partir do GitHub
echo   crontex-flow deploy-dev               - (dev) git pull no servidor e pronto
echo.
echo Padrão: base = %BASE% ; PR sempre contra %BASE% ; nada de editar no servidor.
exit /b 0

:start
:: start <feature>
if "%~2"=="" ( echo [x] Informe o nome da feature. & exit /b 1 )
set FEATURE=%~2
pushd "%REPO_PATH%" || ( echo [x] REPO_PATH inválido. & exit /b 1 )

git fetch --all --prune || goto :gitfail
git switch %BASE% || goto :gitfail
git pull --ff-only %ORIGIN% %BASE% || goto :gitfail
git switch -c %FEATURE% || goto :gitfail
git push -u %ORIGIN% %FEATURE% || goto :gitfail

echo [ok] Feature criada: %FEATURE%
popd & exit /b 0

:cont
:: cont <feature>
if "%~2"=="" ( echo [x] Informe a feature. & exit /b 1 )
set FEATURE=%~2
pushd "%REPO_PATH%" || ( echo [x] REPO_PATH inválido. & exit /b 1 )

git fetch --all --prune || goto :gitfail
git switch %FEATURE% || goto :gitfail
git pull --ff-only %ORIGIN% %FEATURE% || goto :gitfail

echo [ok] Ambiente atualizado para %FEATURE%.
popd & exit /b 0

:test
pushd "%REPO_PATH%" || ( echo [x] REPO_PATH inválido. & exit /b 1 )
set DJANGO_SETTINGS_MODULE=%DJANGO_SETTINGS%
set PYTHONPATH=%REPO_PATH%
echo [i] Rodando testes...
%PYTHON% -m pytest -q
set CODE=%ERRORLEVEL%
if %CODE% NEQ 0 ( echo [x] Testes falharam. Code=%CODE% & popd & exit /b %CODE% )
echo [ok] Testes OK.
popd & exit /b 0

:publish
:: publish <feature> [commit message]
if "%~2"=="" ( echo [x] Informe a feature. & exit /b 1 )
set FEATURE=%~2
set MSG=%~3
if "%MSG%"=="" set MSG=chore: sync feature

pushd "%REPO_PATH%" || ( echo [x] REPO_PATH inválido. & exit /b 1 )
git fetch --all --prune || goto :gitfail
git switch %FEATURE% || goto :gitfail
git status
git add -A
git commit -m "%MSG%"
if %ERRORLEVEL% NEQ 0 echo [!] Nada para commitar. Seguindo para push...
git push -u %ORIGIN% %FEATURE% || goto :gitfail
echo [ok] Publicado em %ORIGIN%/%FEATURE%.
popd & exit /b 0

:syncbase
pushd "%REPO_PATH%" || ( echo [x] REPO_PATH inválido. & exit /b 1 )
git fetch --all --prune || goto :gitfail
git switch %BASE% || goto :gitfail
git pull --ff-only %ORIGIN% %BASE% || goto :gitfail
echo [ok] %BASE% local alinhado com %ORIGIN%.
popd & exit /b 0

:deploydev
:: Pull no servidor dev (requer chave SSH configurada no seu PC)
echo [i] Atualizando servidor dev...
ssh %DEPLOY_HOST% "set -e; cd %DEPLOY_APP_DIR%; git fetch --all --prune; git checkout %BASE%; git pull --ff-only %ORIGIN% %BASE%; echo '[ok] dev.crontex atualizado.'"
exit /b %ERRORLEVEL%

:gitfail
echo [x] Falha em comando git. Cheque o output acima.
popd
exit /b 1
