# -*- coding: utf-8 -*-
from typing import cast
from django.contrib.auth.views import (
    LoginView, LogoutView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
    PasswordChangeView, PasswordChangeDoneView,
)
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from catalog.models import Product

# URLs tipadas p/ Pylance
URL_LOGIN = cast(str, reverse_lazy("crontex_ui:login"))
URL_PWD_RESET_DONE = cast(str, reverse_lazy("crontex_ui:password_reset_done"))
URL_PWD_RESET_COMPLETE = cast(str, reverse_lazy("crontex_ui:password_reset_complete"))
URL_PWD_CHANGE_DONE = cast(str, reverse_lazy("crontex_ui:password_change_done"))

class AppLoginView(LoginView):
    template_name = "crontex_ui/login.html"
    redirect_authenticated_user = True

class AppLogoutView(LogoutView):
    next_page = URL_LOGIN

class AppSignupView(CreateView):
    template_name = "crontex_ui/signup.html"
    form_class = UserCreationForm
    success_url = URL_LOGIN

class AppPasswordResetView(PasswordResetView):
    template_name = "crontex_ui/password_reset.html"
    email_template_name = "crontex_ui/password_reset_email.txt"
    subject_template_name = "crontex_ui/password_reset_subject.txt"
    success_url = URL_PWD_RESET_DONE

class AppPasswordResetDoneView(PasswordResetDoneView):
    template_name = "crontex_ui/password_reset_done.html"

class AppPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "crontex_ui/password_reset_confirm.html"
    success_url = URL_PWD_RESET_COMPLETE

class AppPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "crontex_ui/password_reset_complete.html"

class AppPasswordChangeView(PasswordChangeView):
    template_name = "crontex_ui/password_change.html"
    success_url = URL_PWD_CHANGE_DONE

class AppPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "crontex_ui/password_change_done.html"

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "crontex_ui/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpi_produtos_ativos"] = Product.objects.filter(is_active=True).count()
        ctx["kpi_produtos_total"] = Product.objects.count()
        try:
            qs = Product.objects.order_by("-updated_at", "-created_at")[:6]
            if not qs:
                raise AttributeError
        except Exception:
            qs = Product.objects.order_by("-id")[:6]
        ctx["produtos_recentes"] = qs
        return ctx
