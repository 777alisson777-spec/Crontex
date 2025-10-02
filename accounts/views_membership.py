# accounts/views_membership.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .models import Membership
from .forms_membership import MembershipForm, MembershipSearchForm
from .permissions import require_account_context, require_roles

def av(view_cls):
    """Auth + contexto de account obrigatório."""
    return method_decorator([login_required, require_account_context], name="dispatch")(view_cls)

def _roles(request):
    return set(
        Membership.objects.filter(user=request.user, account=request.account)
        .values_list("role", flat=True)
    )

@av
class MembershipListView(View):
    template_name = "accounts/membership_list.html"

    def get(self, request):
        form = MembershipSearchForm(request.GET or None)
        qs = (
            Membership.objects.filter(account=request.account)
            .select_related("user")
            .order_by("-created_at")
        )
        if form.is_valid():
            q = (form.cleaned_data.get("q") or "").strip()
            role = form.cleaned_data.get("role") or ""
            if q:
                qs = qs.filter(Q(user__username__icontains=q) | Q(user__email__icontains=q))
            if role:
                qs = qs.filter(role=role)
        can_write = (
            Membership.Role.OWNER in _roles(request) or Membership.Role.ADMIN in _roles(request)
        )
        return render(
            request,
            self.template_name,
            {"memberships": qs, "form": form, "can_write": can_write},
        )

@av
class MembershipCreateView(View):
    template_name = "accounts/membership_form.html"

    @method_decorator(require_roles(Membership.Role.OWNER, Membership.Role.ADMIN))
    def get(self, request):
        return render(request, self.template_name, {"form": MembershipForm()})

    @method_decorator(require_roles(Membership.Role.OWNER, Membership.Role.ADMIN))
    def post(self, request):
        form = MembershipForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        user = form.cleaned_data["user"]
        role = form.cleaned_data["role"]

        obj, created = Membership.objects.get_or_create(
            user=user, account=request.account, defaults={"role": role}
        )
        if not created:
            obj.role = role
            obj.save(update_fields=["role"])
            messages.success(request, f"Papel atualizado: {user} → {role}")
        else:
            messages.success(request, f"Membro adicionado: {user} ({role})")
        return redirect(f"/account/members?account={request.account.slug}")

@av
class MembershipUpdateView(View):
    template_name = "accounts/membership_form.html"

    @method_decorator(require_roles(Membership.Role.OWNER, Membership.Role.ADMIN))
    def get(self, request, member_id: int):
        m = get_object_or_404(Membership, id=member_id, account=request.account)
        form = MembershipForm(instance=m)
        return render(request, self.template_name, {"form": form, "member": m})

    @method_decorator(require_roles(Membership.Role.OWNER, Membership.Role.ADMIN))
    def post(self, request, member_id: int):
        m = get_object_or_404(Membership, id=member_id, account=request.account)
        form = MembershipForm(request.POST, instance=m)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "member": m})
        form.save()
        messages.success(request, f"Membro atualizado: {m.user} ({m.role})")
        return redirect(f"/account/members?account={request.account.slug}")

@av
class MembershipDeleteView(View):
    @method_decorator(require_roles(Membership.Role.OWNER, Membership.Role.ADMIN))
    def post(self, request, member_id: int):
        m = get_object_or_404(Membership, id=member_id, account=request.account)
        # Pylance não reconhece .user_id em análise estática; em Django existe.
        if m.user_id == request.user.id and m.role == Membership.Role.OWNER:  # type: ignore[attr-defined]
            messages.error(request, "Owner não pode remover a si mesmo.")
            return redirect(f"/account/members?account={request.account.slug}")
        m.delete()
        messages.success(request, "Membro removido.")
        return redirect(f"/account/members?account={request.account.slug}")
