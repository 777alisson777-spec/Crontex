
CRONTEX Front-end Kit (Django)

Cores (hex) inferidas das artes:
- Navy principal: #052450
- Navy escuro: #0b2a55
- Texto: #0e2a56
- Laranja (destaque): #ffa31a
- Vermelho (alerta): #e6453a
- Fundo claro: #f7faff
- Linha/traço: #d6dee8

Arquivos gerados:
- static/css/crontex.css
- static/img_logo.jpeg   (logo enviado)
- static/img_login.jpeg  (mock da tela enviada)
- templates/login.html
- templates/dashboard.html

Integração rápida no Django:
1) Em settings.py
   STATIC_URL = 'static/'
   STATICFILES_DIRS = [ BASE_DIR / 'static' ]  # se usar app-level, mova a pasta para o app

2) Em urls.py (use as URLs reais do seu projeto):
   from django.contrib.auth import views as auth_views
   from django.urls import path
   from django.views.generic import TemplateView

   urlpatterns = [
       path('entrar/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
       path('sair/', auth_views.LogoutView.as_view(next_page='/entrar/'), name='logout'),
       path('', TemplateView.as_view(template_name='dashboard.html'), name='home'),
       path('signup/', TemplateView.as_view(template_name='dashboard.html'), name='signup'),  # troque pela view real
       path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
   ]

3) Coloque a pasta 'static' e 'templates' deste kit na raiz do seu projeto ou dentro do app principal.

Ajuste fino:
- Troque as URLs de OAuth para os providers reais.
- Conecte os dados reais nas KPI e tabelas.
