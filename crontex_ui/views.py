from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from .forms import SignupForm

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "crontex_ui/dashboard.html"
    login_url = "crontex_ui:login"

class AppLoginView(LoginView):
    template_name = "crontex_ui/login.html"
    redirect_authenticated_user = True

class AppLogoutView(LogoutView):
    next_page = reverse_lazy("crontex_ui:login")

class AppSignupView(CreateView):
    form_class = SignupForm
    template_name = "crontex_ui/signup.html"
    success_url = reverse_lazy("crontex_ui:login")
