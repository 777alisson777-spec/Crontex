from django.urls import path
from .views import (
    AppLoginView, AppLogoutView, AppSignupView,
    AppPasswordResetView, AppPasswordResetDoneView,
    AppPasswordResetConfirmView, AppPasswordResetCompleteView,
    AppPasswordChangeView, AppPasswordChangeDoneView, DashboardView,
    
)

app_name = "crontex_ui"

urlpatterns = [
    path("entrar/", AppLoginView.as_view(), name="login"),
    path("sair/", AppLogoutView.as_view(), name="logout"),
    path("criar-conta/", AppSignupView.as_view(), name="signup"),

    path("senha/resetar/", AppPasswordResetView.as_view(), name="password_reset"),
    path("senha/resetar/enviado/", AppPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("senha/resetar/<uidb64>/<token>/", AppPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("senha/resetar/concluido/", AppPasswordResetCompleteView.as_view(), name="password_reset_complete"),

    path("senha/alterar/", AppPasswordChangeView.as_view(), name="password_change"),
    path("senha/alterada/", AppPasswordChangeDoneView.as_view(), name="password_change_done"),
    path("", DashboardView.as_view(), name="dashboard")
]
