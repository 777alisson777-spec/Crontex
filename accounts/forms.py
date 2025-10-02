from django import forms
from django.contrib.auth import get_user_model
from .models import Account, GlobalUserRole

# Alias do modelo de usuário da plataforma
AuthUser = get_user_model()

class AccountCreateForm(forms.ModelForm):
    """Form de criação/edição de Account no painel global."""
    class Meta:
        model = Account
        fields = ["name", "slug", "plan", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Nome da empresa"}),
            "slug": forms.TextInput(attrs={"placeholder": "ex: patrickhf"}),
            "plan": forms.TextInput(attrs={"placeholder": "basic | pro | enterprise"}),
        }

class AccountSearchForm(forms.Form):
    """Busca simples por nome ou slug."""
    q = forms.CharField(
        required=False,
        label="Buscar",
        widget=forms.TextInput(attrs={"placeholder": "nome ou slug"})
    )

class GlobalUserForm(forms.ModelForm):
    """CRUD mínimo de usuário global. is_superuser fica fora daqui."""
    class Meta:
        model = AuthUser
        fields = ["username", "email", "is_active", "is_staff"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "username"}),
            "email": forms.EmailInput(attrs={"placeholder": "email@dominio"}),
        }

class GlobalUserRoleForm(forms.ModelForm):
    """Atribuição de papel global (ADMIN | SYSREAD | AUDITOR)."""
    class Meta:
        model = GlobalUserRole
        fields = ["role"]
