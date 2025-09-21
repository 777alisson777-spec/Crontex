from django.urls import path
from .views import DashboardView, AppLoginView, AppLogoutView

app_name = "crontex_ui"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("entrar/", AppLoginView.as_view(), name="login"),
    path("sair/", AppLogoutView.as_view(), name="logout"),
]