# accounts/views_token.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .models import ServiceToken
from .forms_token import ServiceTokenCreateForm, ServiceTokenUpdateForm, ServiceTokenSearchForm

# Somente staff global. Escrita recomendada para Global Admin/superuser via menu.
def is_global_staff(user) -> bool:
    return user.is_authenticated and user.is_staff

def ga(view_cls):
    return method_decorator([login_required, user_passes_test(is_global_staff)], name="dispatch")(view_cls)

@ga
class ServiceTokenListView(View):
    template_name = "accounts/token_list.html"

    def get(self, request):
        form = ServiceTokenSearchForm(request.GET or None)
        qs = ServiceToken.objects.all().order_by("-created_at")
        if form.is_valid():
            q = (form.cleaned_data.get("q") or "").strip()
            if q:
                qs = qs.filter(Q(name__icontains=q))
            status = form.cleaned_data.get("is_active") or ""
            if status == "1":
                qs = qs.filter(is_active=True)
            elif status == "0":
                qs = qs.filter(is_active=False)
            acc = form.cleaned_data.get("account")
            if acc:
                qs = qs.filter(account=acc)
        return render(request, self.template_name, {"tokens": qs, "form": form})

@ga
class ServiceTokenCreateView(View):
    template_name = "accounts/token_form.html"

    def get(self, request):
        return render(request, self.template_name, {"form": ServiceTokenCreateForm(), "show_secret": False})

    def post(self, request):
        form = ServiceTokenCreateForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "show_secret": False})

        # Gera chave única e armazena hash
        token_obj = form.save(commit=False)
        raw_key = ServiceToken.generate_key()
        token_obj.set_key(raw_key)
        token_obj.save()
        messages.success(request, f"Token criado: {token_obj.name}. Copie a chave agora, ela não será mostrada novamente.")
        # Exibir somente 1x
        return render(request, self.template_name, {"form": ServiceTokenCreateForm(), "show_secret": True, "raw_key_once": raw_key})

@ga
class ServiceTokenUpdateView(View):
    template_name = "accounts/token_form.html"

    def get(self, request, token_id: str):
        token = get_object_or_404(ServiceToken, pk=token_id)
        form = ServiceTokenUpdateForm(instance=token)
        return render(request, self.template_name, {"form": form, "token": token, "show_secret": False})

    def post(self, request, token_id: str):
        token = get_object_or_404(ServiceToken, pk=token_id)
        form = ServiceTokenUpdateForm(request.POST, instance=token)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "token": token, "show_secret": False})
        form.save()
        messages.success(request, "Token atualizado.")
        return redirect("accounts:token_list")

@ga
class ServiceTokenRotateView(View):
    """
    Rotaciona a chave do token. Mostra a nova APENAS uma vez.
    """
    template_name = "accounts/token_rotate.html"

    def post(self, request, token_id: str):
        token = get_object_or_404(ServiceToken, pk=token_id, is_active=True)
        new_key = ServiceToken.generate_key()
        token.set_key(new_key)
        token.save(update_fields=["key_hash"])
        messages.success(request, "Chave rotacionada. Copie agora.")
        return render(request, self.template_name, {"token": token, "raw_key_once": new_key})

@ga
class ServiceTokenDeactivateView(View):
    def post(self, request, token_id: str):
        token = get_object_or_404(ServiceToken, pk=token_id)
        token.is_active = False
        token.save(update_fields=["is_active"])
        messages.success(request, "Token desativado.")
        return redirect("accounts:token_list")

