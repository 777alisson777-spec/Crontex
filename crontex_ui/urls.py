from django.urls import path
from django.contrib.auth import views as auth_views
from .views import DashboardView, AppLoginView, AppLogoutView, AppSignupView

app_name = "crontex_ui"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("entrar/", AppLoginView.as_view(), name="login"),
    path("sair/", AppLogoutView.as_view(), name="logout"),
    path("signup/", AppSignupView.as_view(), name="signup"),

    # reset de senha
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html"
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
