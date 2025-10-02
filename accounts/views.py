from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .forms import (
    AccountCreateForm,
    AccountSearchForm,
    GlobalUserForm,
    GlobalUserRoleForm,
)
from .models import Account, Membership, GlobalUserRole

User = get_user_model()

# ---------------- Gates globais ----------------
def is_global_staff(user) -> bool:
    """Permitido acessar o dashboard global se for staff."""
    return user.is_authenticated and user.is_staff

def ga(view_cls):
    """Decorator para CBVs exigindo login + staff."""
    return method_decorator([login_required, user_passes_test(is_global_staff)], name="dispatch")(view_cls)

def _can_read_global(user) -> bool:
    """Leitura no global: superuser ou qualquer GlobalUserRole (ADMIN, SYSREAD, AUDITOR)."""
    if not is_global_staff(user):
        return False
    if user.is_superuser:
        return True
    return hasattr(user, "global_role")

def _can_write_global(user) -> bool:
    """Escrita no global: superuser ou GlobalUserRole.ADMIN."""
    if not is_global_staff(user):
        return False
    if user.is_superuser:
        return True
    role = getattr(user, "global_role", None)
    return bool(role and role.role == GlobalUserRole.Role.ADMIN)

# ---------------- Dashboard Global ----------------
@ga
class GlobalDashboardView(View):
    template_name = "accounts/global_dashboard.html"

    def get(self, request):
        # KPIs de contas
        total_accounts = Account.objects.count()
        active_accounts = Account.objects.filter(is_active=True).count()
        per_plan = Account.objects.values("plan").annotate(qty=Count("id")).order_by("plan")

        # KPIs de usuários da plataforma
        users_plat_total = User.objects.count()
        staff_count = User.objects.filter(is_staff=True).count()
        superusers_count = User.objects.filter(is_superuser=True).count()

        # Usuários distintos vinculados a tenants
        users_tenants_distinct = Membership.objects.values("user_id").distinct().count()

        ctx = {
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "per_plan": per_plan,
            "users_plat_total": users_plat_total,
            "staff_count": staff_count,
            "superusers_count": superusers_count,
            "users_tenants_distinct": users_tenants_distinct,
        }
        return render(request, self.template_name, ctx)

# ---------------- Accounts (global) ----------------
@ga
class AccountListView(View):
    template_name = "accounts/account_list.html"

    def get(self, request):
        form = AccountSearchForm(request.GET or None)
        qs = Account.objects.all().order_by("-created_at")
        if form.is_valid():
            q = (form.cleaned_data.get("q") or "").strip()
            if q:
                qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q))
        return render(request, self.template_name, {"accounts": qs, "form": form})

@ga
class AccountCreateView(View):
    template_name = "accounts/account_create.html"

    def get(self, request):
        return render(request, self.template_name, {"form": AccountCreateForm()})

    def post(self, request):
        form = AccountCreateForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})
        acc = form.save()
        messages.success(request, f"Account criada: {acc.name}")
        return redirect("accounts:account_list")

@ga
class ImpersonateStartView(View):
    """Define contexto de account na sessão e redireciona para o dashboard da conta."""
    def post(self, request, slug):
        acc = get_object_or_404(Account, slug=slug, is_active=True)
        request.session["account_slug"] = acc.slug
        messages.info(request, f"Contexto alterado para conta: {acc.name}")
        return redirect(f"/dashboard?account={acc.slug}")

@ga
class ImpersonateStopView(View):
    """Limpa o contexto de account."""
    def post(self, request):
        request.session.pop("account_slug", None)
        messages.info(request, "Saiu do contexto da conta.")
        return redirect("accounts:global_dashboard")

# ---------------- Usuários Globais (CRUD) ----------------
@ga
class GlobalUsersListView(View):
    template_name = "accounts/global_users.html"

    def get(self, request):
        if not _can_read_global(request.user):
            messages.error(request, "Permissão negada.")
            return redirect("accounts:global_dashboard")

        qs = User.objects.all().order_by("-date_joined")
        q = (request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))
        if request.GET.get("is_staff") == "1":
            qs = qs.filter(is_staff=True)
        if request.GET.get("is_superuser") == "1":
            qs = qs.filter(is_superuser=True)
        if request.GET.get("active") == "1":
            qs = qs.filter(is_active=True)

        ctx = {
            "users": qs,
            "q": q,
            "flt_staff": request.GET.get("is_staff") == "1",
            "flt_super": request.GET.get("is_superuser") == "1",
            "flt_active": request.GET.get("active") == "1",
            "can_write": _can_write_global(request.user),
        }
        return render(request, self.template_name, ctx)

@ga
class GlobalUserCreateView(View):
    template_name = "accounts/global_user_form.html"

    def get(self, request):
        if not _can_write_global(request.user):
            messages.error(request, "Permissão negada.")
            return redirect("accounts:global_users")
        return render(request, self.template_name, {
            "uform": GlobalUserForm(),
            "rform": GlobalUserRoleForm(),
            "can_write": True
        })

    def post(self, request):
        if not _can_write_global(request.user):
            messages.error(request, "Permissão negada.")
            return redirect("accounts:global_users")

        uform = GlobalUserForm(request.POST)
        rform = GlobalUserRoleForm(request.POST)
        if not (uform.is_valid() and rform.is_valid()):
            return render(request, self.template_name, {
                "uform": uform,
                "rform": rform,
                "can_write": True
            })

        user = uform.save()
        GlobalUserRole.objects.update_or_create(user=user, defaults={"role": rform.cleaned_data["role"]})
        messages.success(request, f"Usuário criado: {user.username}")
        return redirect("accounts:global_users")

@ga
class GlobalUserUpdateView(View):
    template_name = "accounts/global_user_form.html"

    def get(self, request, user_id: int):
        if not _can_read_global(request.user):
            messages.error(request, "Permissão negada.")
            return redirect("accounts:global_users")

        user = get_object_or_404(User, pk=user_id)
        uform = GlobalUserForm(instance=user)
        role = getattr(user, "global_role", None)
        rform = GlobalUserRoleForm(instance=role) if role else GlobalUserRoleForm()
        return render(request, self.template_name, {
            "uform": uform,
            "rform": rform,
            "target_user": user,
            "can_write": _can_write_global(request.user)
        })

    def post(self, request, user_id: int):
        if not _can_write_global(request.user):
            messages.error(request, "Permissão negada.")
            return redirect("accounts:global_users")

        user = get_object_or_404(User, pk=user_id)
        uform = GlobalUserForm(request.POST, instance=user)
        role_inst = getattr(user, "global_role", None)
        rform = GlobalUserRoleForm(request.POST, instance=role_inst)

        if not (uform.is_valid() and rform.is_valid()):
            return render(request, self.template_name, {
                "uform": uform,
                "rform": rform,
                "target_user": user,
                "can_write": True
            })

        uform.save()
        role_obj = rform.save(commit=False)
        role_obj.user = user
        role_obj.save()
        messages.success(request, f"Usuário atualizado: {user.username}")
        return redirect("accounts:global_users")

@ga
class GlobalUserDeactivateView(View):
    def post(self, request, user_id: int):
        if not _can_write_global(request.user):
            messages.error(request, "Permissão negada.")
            return redirect("accounts:global_users")

        user = get_object_or_404(User, pk=user_id)
        if user.is_superuser:
            messages.error(request, "Não é permitido desativar superuser por aqui.")
            return redirect("accounts:global_users")

        user.is_active = False
        user.save(update_fields=["is_active"])
        messages.success(request, f"Usuário desativado: {user.username}")
        return redirect("accounts:global_users")
