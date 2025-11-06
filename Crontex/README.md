# Crontex (Django)

MVP do back-end Crontex.

## Requisitos
- Python 3.11+ (ou compatível)
- pip
- Git

## Setup local (Windows / macOS / Linux)
```bash
# clonar
git clone https://github.com/SEU_USUARIO/crontex.git
cd crontex

# criar ambiente virtual
python -m venv .venv
# Windows (CMD):
".venv\Scripts\activate.bat"
# macOS/Linux:
# source .venv/bin/activate

# instalar dependências
python -m pip install --upgrade pip
pip install -r requirements.txt

# configurar ambiente
cp .env.example .env
# edite .env e defina SECRET_KEY (string aleatória)
# exemplo de SECRET_KEY: use https://djecrety.ir/ ou `python -c "import secrets;print(secrets.token_urlsafe(50))"`

# migrar banco e criar admin
python manage.py migrate
python manage.py createsuperuser

# coletar estáticos (se for servir via Nginx/WhiteNoise)
python manage.py collectstatic --noinput

# rodar
python manage.py runserver
