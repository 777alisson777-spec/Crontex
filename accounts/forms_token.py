# accounts/forms_token.py
from django import forms
from .models import ServiceToken, Account

class ServiceTokenCreateForm(forms.ModelForm):
    """
    Criação de token técnico.
    - Gera a chave automaticamente na view e mostra UMA VEZ.
    - 'account' é opcional: None = token global.
    - 'scopes' como JSON (lista de strings).
    """
    scopes_json = forms.CharField(
        required=False,
        label="Escopos (JSON)",
        widget=forms.Textarea(attrs={"placeholder": '["accounts:read", "products:write"]', "rows": 3}),
        help_text="Lista JSON de escopos. Vazio = sem escopos."
    )

    class Meta:
        model = ServiceToken
        fields = ["name", "account", "is_active"]

    def clean_scopes_json(self):
        import json
        raw = self.cleaned_data.get("scopes_json") or ""
        if not raw.strip():
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise forms.ValidationError("JSON inválido")
        if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
            raise forms.ValidationError("Forneça uma lista de strings")
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.scopes = self.cleaned_data.get("scopes_json", [])
        if commit:
            obj.save()
        return obj


class ServiceTokenUpdateForm(forms.ModelForm):
    """
    Edição de metadados do token.
    Não altera a chave. Use a ação de rotação em fluxo próprio se necessário.
    """
    scopes_json = forms.CharField(
        required=False,
        label="Escopos (JSON)",
        widget=forms.Textarea(attrs={"placeholder": '["accounts:read", "products:write"]', "rows": 3}),
    )

    class Meta:
        model = ServiceToken
        fields = ["name", "account", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preenche textarea com o JSON atual
        import json
        self.fields["scopes_json"].initial = json.dumps(self.instance.scopes or [])

    def clean_scopes_json(self):
        import json
        raw = self.cleaned_data.get("scopes_json") or "[]"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise forms.ValidationError("JSON inválido")
        if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
            raise forms.ValidationError("Forneça uma lista de strings")
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.scopes = self.cleaned_data.get("scopes_json", [])
        if commit:
            obj.save()
        return obj


class ServiceTokenSearchForm(forms.Form):
    """Filtro simples por nome, status e escopo de account."""
    q = forms.CharField(required=False, label="Buscar", widget=forms.TextInput(
        attrs={"placeholder": "nome do token"}
    ))
    is_active = forms.ChoiceField(
        required=False,
        choices=(("", "Todos"), ("1", "Ativos"), ("0", "Inativos")),
        label="Status",
    )
    account = forms.ModelChoiceField(
        required=False,
        queryset=Account.objects.all(),
        empty_label="Todas",
        label="Account",
    )
