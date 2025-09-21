from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView
from django.urls import reverse_lazy

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "crontex_ui/dashboard.html"   # usa a subpasta namespaced
    login_url = "crontex_ui:login"

class AppLoginView(LoginView):
    template_name = "crontex_ui/login.html"
    redirect_authenticated_user = True

class AppLogoutView(LogoutView):
    next_page = reverse_lazy("crontex_ui:login")