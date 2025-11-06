# accounts/forms_membership.py
from django import forms
from django.contrib.auth import get_user_model
from .models import Membership

AuthUser = get_user_model()

class MembershipForm(forms.ModelForm):
    """
    Usado para criar/editar vínculo de usuário à account atual.
    O campo 'account' não aparece: vem de request.account na view.
    """
    user = forms.ModelChoiceField(
        queryset=AuthUser.objects.all(),
        widget=forms.Select(attrs={"data-behavior": "autocomplete"}),
        label="Usuário",
    )

    class Meta:
        model = Membership
        fields = ["user", "role"]  # 'account' setado na view

class MembershipSearchForm(forms.Form):
    """Filtro simples por username/email e papel."""
    q = forms.CharField(required=False, label="Buscar", widget=forms.TextInput(
        attrs={"placeholder": "username ou email"}
    ))
    role = forms.ChoiceField(
        required=False,
        choices=(("", "Todos"),) + tuple((r, r.title()) for r, _ in Membership.Role.choices),
        label="Papel",
    )
