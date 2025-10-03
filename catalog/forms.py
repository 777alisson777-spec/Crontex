# -*- coding: utf-8 -*-
from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            # Bling básicos
            "external_id", "sku", "name", "unit", "ncm", "origin",
            "price", "ipi_fixed", "notes", "status", "stock_qty",
            "cost_price", "supplier_code", "supplier_name", "location",
            # Extras consolidados
            "bling_extra",
            # Finais 45–59
            "external_link", "warranty_months_supplier", "clone_from_parent",
            "product_condition", "free_shipping", "fci_number", "video_url",
            "department", "unit_of_measure", "purchase_price",
            "icms_st_base_retencao", "icms_st_valor_retencao",
            "icms_proprio_substituto", "product_category", "extra_info",
            # Catálogo adicionais
            "cest", "gtin", "brand",
            "width_cm", "height_cm", "length_cm",
            "weight_net", "weight_gross",
            "is_active",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "extra_info": forms.Textarea(attrs={"rows": 3}),
            "bling_extra": forms.Textarea(attrs={"rows": 4, "placeholder": "JSON das colunas 16–45"}),
            "status": forms.TextInput(attrs={"placeholder": "ex.: Ativo/Inativo"}),
            "origin": forms.TextInput(attrs={"placeholder": "ex.: Nacional"}),
            "unit": forms.TextInput(attrs={"placeholder": "ex.: UN/KG/LT"}),
        }

    def clean_bling_extra(self):
        data = self.cleaned_data.get("bling_extra")
        # aceita dict ou string JSON-like vazia
        if data in (None, "", {}):
            return {}
        if isinstance(data, dict):
            return data
        raise forms.ValidationError("bling_extra deve ser um objeto JSON (dict).")
