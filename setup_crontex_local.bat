@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ============================================================
REM Crontex — Setup local end-to-end (Windows CMD)
REM Requisitos: Git, Python (3.13+ de preferência)
REM Uso típico: setup_crontex_local.bat
REM Variáveis opcionais (defina antes de rodar):
REM   SET GIT_URL=https://github.com/777alisson777-spec/Crontex.git
REM   SET BRANCH=Crontex_IA-wt
REM   SET PROJECT_DIR=Crontex
REM   SET PY_EXE=py -3.13
REM   SET RUNSERVER=1  (auto start server no final)
REM   SET SU_USERNAME=admin
REM   SET SU_EMAIL=admin@example.com
REM   SET SU_PASSWORD=admin123
REM ============================================================

REM ---------- Defaults ----------
if not defined GIT_URL set "GIT_URL=https://github.com/777alisson777-spec/Crontex.git"
if not defined BRANCH set "BRANCH=Crontex_IA-wt"
if not defined PROJECT_DIR set "PROJECT_DIR=Crontex"
if not defined PY_EXE set "PY_EXE=py -3.13"
if not defined RUNSERVER set "RUNSERVER=0"

REM ---------- Sanity: Git ----------
where git >NUL 2>&1
if errorlevel 1 (
  echo [ERRO] Git nao encontrado no PATH.
  exit /b 1
)

REM ---------- Sanity: Python ----------
%PY_EXE% -V >NUL 2>&1
if errorlevel 1 (
  echo [WARN] Python 3.13 nao encontrado. Tentando 'python' generico...
  set "PY_EXE=python"
  where python >NUL 2>&1
  if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    exit /b 1
  )
)

REM ---------- Clone/Atualiza repo ----------
if exist "%PROJECT_DIR%\.git" (
  echo [INFO] Repo existe. Atualizando...
  pushd "%PROJECT_DIR%"
  git fetch --all --prune
) else (
  echo [INFO] Clonando repo...
  git clone "%GIT_URL%" "%PROJECT_DIR%"
  if errorlevel 1 (
    echo [ERRO] Falha no clone. Verifique a URL/credenciais.
    exit /b 1
  )
  pushd "%PROJECT_DIR%"
)

REM ---------- Checkout branch (se existir) ----------
git show-ref --heads | findstr /i "refs/heads/%BRANCH%" >NUL
if errorlevel 1 (
  echo [WARN] Branch "%BRANCH%" nao existe local. Tentando remoto...
  git ls-remote --heads origin "%BRANCH%" >NUL 2>&1
  if errorlevel 1 (
    echo [WARN] Branch remoto "%BRANCH%" nao encontrado. Mantendo branch atual.
  ) else (
    git checkout -b "%BRANCH%" origin/%BRANCH%
  )
) else (
  git checkout "%BRANCH%"
)

REM ---------- Venv ----------
if not exist ".venv" (
  echo [INFO] Criando venv...
  %PY_EXE% -m venv .venv
)
call .\.venv\Scripts\activate
if errorlevel 1 (
  echo [ERRO] Falha ao ativar venv.
  popd & exit /b 1
)

REM ---------- Pip upgrade ----------
python -m pip install --upgrade pip >NUL

REM ---------- Requirements ----------
if exist "requirements.txt" (
  echo [INFO] Instalando deps de requirements.txt...
  pip install -r requirements.txt
) else (
  echo [WARN] requirements.txt nao encontrado. Instalando baseline...
  pip install Django==5.2.6 asgiref==3.9.1 sqlparse==0.5.3 tzdata==2025.2 ^
    python-decouple==3.8 dj-database-url==3.0.1 ^
    "openai>=1.50,<2" "requests>=2.32,<3" ^
    "Pillow>=10.4,<11" "psycopg[binary]>=3.2,<4"
)

REM ---------- .env ----------
set "ENV_FILE=.env"
if not exist "%ENV_FILE%" (
  echo [INFO] Criando .env baseline...
  >"%ENV_FILE%" (
    echo DEBUG=True
    echo ALLOWED_HOSTS=127.0.0.1,localhost
    echo TIME_ZONE=America/Sao_Paulo
    echo DATABASE_URL=sqlite:///db.sqlite3
    echo OPENAI_API_KEY=
  )
)

REM ---------- SECRET_KEY ----------
for /f "usebackq delims=" %%K in (`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2^>NUL`) do set "SECRET_KEY_VAL=%%K"
if not defined SECRET_KEY_VAL (
  echo [ERRO] Nao consegui gerar SECRET_KEY (Django ausente?). Abortando.
  popd & exit /b 1
)

REM remove SECRET_KEY antigo e reescreve
>"%ENV_FILE%.tmp" (
  for /f "usebackq delims=" %%L in ("%ENV_FILE%") do (
    set "LINE=%%L"
    echo(!LINE!| findstr /B /C:"SECRET_KEY=" >NUL
    if errorlevel 1 echo %%L
  )
  echo SECRET_KEY=%SECRET_KEY_VAL%
)
move /Y "%ENV_FILE%.tmp" "%ENV_FILE%" >NUL

REM ---------- Django checks ----------
echo [INFO] Validando Django...
python manage.py check
if errorlevel 1 (
  echo [ERRO] Django check falhou.
  popd & exit /b 1
)

REM ---------- Migrações ----------
echo [INFO] Migrações...
python manage.py makemigrations
python manage.py migrate
if errorlevel 1 (
  echo [ERRO] migrate falhou.
  popd & exit /b 1
)

REM ---------- Superuser (non-interativo) ----------
if not defined SU_USERNAME set "SU_USERNAME=admin"
if not defined SU_EMAIL set "SU_EMAIL=admin@example.com"
if not defined SU_PASSWORD set "SU_PASSWORD=admin123"

echo [INFO] Criando/atualizando superuser "%SU_USERNAME%"...
python manage.py shell -c "from django.contrib.auth import get_user_model; U=get_user_model(); u,created=U.objects.get_or_create(username='%SU_USERNAME%', defaults={'email':'%SU_EMAIL%'}); u.email='%SU_EMAIL%'; u.is_staff=True; u.is_superuser=True; u.set_password('%SU_PASSWORD%'); u.save(); print('created' if created else 'updated')" || (
  echo [WARN] Nao foi possivel criar via shell. Tente 'python manage.py createsuperuser' manualmente.
)

REM ---------- Coleta de estáticos (não bloqueante) ----------
echo [INFO] collectstatic (best-effort)...
python manage.py collectstatic --noinput >NUL 2>&1
if errorlevel 1 echo [WARN] collectstatic nao aplicavel no dev (ok).

REM ---------- URLs-chave ----------
echo.
echo [OK] Setup completo.
echo     Admin:  http://127.0.0.1:8000/admin/
echo     Root:   http://127.0.0.1:8000/
echo     User:   %SU_USERNAME%  |  Pass: %SU_PASSWORD%
echo.

REM ---------- Runserver opcional ----------
if "%RUNSERVER%"=="1" (
  echo [INFO] Subindo server (Ctrl+C para parar)...
  python manage.py runserver
) else (
  echo [TIP] Para iniciar: call .venv\Scripts\activate ^&^& python manage.py runserver
)

popd
endlocal
exit /b 0
