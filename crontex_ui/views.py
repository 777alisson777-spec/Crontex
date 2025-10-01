from django.contrib.auth.views import (
    LoginView, LogoutView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
    PasswordChangeView, PasswordChangeDoneView,
)
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone


class AppLoginView(LoginView):
    template_name = "crontex_ui/login.html"
    redirect_authenticated_user = True


class AppLogoutView(LogoutView):
    next_page = reverse_lazy("crontex_ui:login")


class AppSignupView(CreateView):
    template_name = "crontex_ui/signup.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("crontex_ui:login")


class AppPasswordResetView(PasswordResetView):
    template_name = "crontex_ui/password_reset.html"
    email_template_name = "crontex_ui/password_reset_email.txt"
    subject_template_name = "crontex_ui/password_reset_subject.txt"
    success_url = reverse_lazy("crontex_ui:password_reset_done")


class AppPasswordResetDoneView(PasswordResetDoneView):
    template_name = "crontex_ui/password_reset_done.html"


class AppPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "crontex_ui/password_reset_confirm.html"
    success_url = reverse_lazy("crontex_ui:password_reset_complete")


class AppPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "crontex_ui/password_reset_complete.html"


class AppPasswordChangeView(PasswordChangeView):
    template_name = "crontex_ui/password_change.html"
    success_url = reverse_lazy("crontex_ui:password_change_done")


class AppPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "crontex_ui/password_change_done.html"

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "crontex_ui/dashboard.html"

    def get_context_data(self, **kwargs):
        from catalog.models import Produto  # import local evita ciclos
        context = super().get_context_data(**kwargs)

        # KPIs reais de Produto
        context["kpi_produtos_ativos"] = Produto.objects.filter(ativo=True).count()
        context["kpi_produtos_total"] = Produto.objects.count()

        # Últimos 6 produtos criados/atualizados
        context["produtos_recentes"] = (
            Produto.objects
            .order_by("-atualizado_em", "-criado_em")
            .only("id", "nome", "sku", "preco", "estoque", "ativo", "imagem", "atualizado_em")[:6]
        )
        return context
    



