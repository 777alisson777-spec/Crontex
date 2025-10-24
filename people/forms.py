# people/forms.py
from __future__ import annotations

from typing import Any, Dict, Optional, Union
from django import forms
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from django.http import QueryDict

from .models import Contact, Address, PersonKind
from .utils import (
    normalize_cpf,
    normalize_cnpj,
    normalize_phone,
    normalize_cep,
    normalize_uf,
)


# ---------- helpers de estilo ----------
def _apply_crontex_styles(bound_form: forms.BaseForm) -> None:
    """
    Aplica classes padrão 'input' (Crontex) em TODOS os campos, salvo checkboxes.
    Mantém outras classes existentes (concatena).
    """
    for name, field in bound_form.fields.items():
        w = field.widget
        # Checkbox mantém nativo; os demais ganham 'input'
        is_checkbox = isinstance(w, (forms.CheckboxInput, forms.CheckboxSelectMultiple))
        base_class = w.attrs.get("class", "").strip()
        if not is_checkbox:
            w.attrs["class"] = ("input " + base_class).strip()
        # placeholder amigável (não intrusivo)
        ph_map = {
            "name": "Nome / Razão social",
            "fantasy_name": "Nome fantasia",
            "email": "email@dominio.com",
            "phone": "(11) 99999-9999",
            "phone_alt": "(11) 0000-0000",
            "cpf": "Somente números",
            "cnpj": "Somente números",
            "rg": "Documento RG",
            "ie": "Inscrição estadual",
            "cep": "00000-000",
            "street": "Rua/Av.",
            "number": "Número",
            "complement": "Apto/Bloco/etc",
            "district": "Bairro",
            "city": "Cidade",
            "uf": "UF",
            "country": "País",
            "notes": "Observações",
        }
        if name in ph_map and not w.attrs.get("placeholder"):
            w.attrs["placeholder"] = ph_map[name]
        # selects e textarea também recebem 'input' (acima) + ajustes leves
        if isinstance(w, forms.Textarea):
            w.attrs.setdefault("rows", 3)
        if isinstance(w, (forms.SelectMultiple,)):
            # tamanho default melhor que 2
            w.attrs.setdefault("size", 6)


class ContactForm(forms.ModelForm):
    """
    MVP: todos os campos opcionais. Se preenchidos, normaliza e valida coerência.
    """
    class Meta:
        model = Contact
        fields = [
            "name", "fantasy_name", "person_kind",
            "is_cliente", "is_fornecedor", "is_colaborador", "is_parceiro",
            "categories",
            "cpf", "cnpj", "rg", "ie", "ie_isento",
            "email", "phone", "phone_alt",
            "status", "notes",
        ]
        widgets = {
            # ainda definimos widgets “sem classe”; a classe vem no __init__
            "notes": forms.Textarea(),
            "categories": forms.SelectMultiple(),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        _apply_crontex_styles(self)

    def clean(self):
        cleaned = super().clean()
        # normalização leve
        cleaned["cpf"] = normalize_cpf(cleaned.get("cpf"))
        cleaned["cnpj"] = normalize_cnpj(cleaned.get("cnpj"))
        cleaned["phone"] = normalize_phone(cleaned.get("phone"))
        cleaned["phone_alt"] = normalize_phone(cleaned.get("phone_alt"))

        # coerência PF/PJ
        kind = cleaned.get("person_kind")
        cpf = cleaned.get("cpf") or ""
        cnpj = cleaned.get("cnpj") or ""
        ie = (cleaned.get("ie") or "").strip()
        ie_isento = bool(cleaned.get("ie_isento"))

        if kind == PersonKind.FISICA and cnpj:
            self.add_error("cnpj", "Pessoa Física não deve informar CNPJ.")
        if kind == PersonKind.JURIDICA and cpf:
            self.add_error("cpf", "Pessoa Jurídica não deve informar CPF.")
        if ie_isento and ie:
            self.add_error("ie", "Com 'IE Isento' marcado, deixe o campo IE em branco.")
        return cleaned


class AddressForm(forms.ModelForm):
    """Form do endereço com normalização de CEP e UF + estilos Crontex."""
    class Meta:
        model = Address
        fields = [
            "label", "cep", "street", "number", "complement",
            "district", "city", "uf", "country",
        ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        _apply_crontex_styles(self)

    def clean(self):
        cleaned = super().clean()
        cleaned["cep"] = normalize_cep(cleaned.get("cep"))
        cleaned["uf"] = normalize_uf(cleaned.get("uf"))
        return cleaned


# Classe do formset (usando AddressForm)
AddressFormSet = inlineformset_factory(
    parent_model=Contact,
    model=Address,
    form=AddressForm,
    fields=[
        "label", "cep", "street", "number", "complement",
        "district", "city", "uf", "country",
    ],
    extra=1,
    can_delete=True,
)


def build_address_formset(
    *,
    data: Optional[Union[QueryDict, Dict[str, Any]]] = None,
    files: Optional[Union[QueryDict, Dict[str, Any]]] = None,
    instance: Optional[Contact] = None,
    prefix: Optional[str] = None,
) -> BaseInlineFormSet:
    """
    Constrói o formset de endereços com assinatura clara para o analisador estático.
    Aceita QueryDict (request.POST/FILES) ou dict normal.
    """
    return AddressFormSet(data=data, files=files, instance=instance, prefix=prefix)


# Upload para importação CSV
class ContactImportForm(forms.Form):
    file = forms.FileField(
        label="Arquivo CSV",
        help_text="CSV com ; (padrão) ou , (auto-detect). UTF-8 recomendado."
    )
