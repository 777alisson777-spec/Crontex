# catalog/forms.py
from django import forms
from .models import Produto

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ["nome", "sku", "preco", "estoque", "ativo", "imagem"]
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Nome do produto", "class": "control"}),
            "sku": forms.TextInput(attrs={"placeholder": "SKU único", "class": "control", "style": "text-transform:uppercase"}),
            "preco": forms.NumberInput(attrs={"step": "0.01", "min": "0", "class": "control"}),
            "estoque": forms.NumberInput(attrs={"min": "0", "class": "control"}),
            "imagem": forms.ClearableFileInput(attrs={"accept": "image/*", "class": "control"}),
        }

    def clean_sku(self):
        sku = (self.cleaned_data.get("sku") or "").strip().upper()
        return sku
