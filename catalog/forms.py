# -*- coding: utf-8 -*-
from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    """
    Form de Produto com abas:
    - pedido, bling, os, manufatura, material, grade, av-oficina, av-acab
    Campos extras (todas as abas exceto "bling") são apenas de UI por enquanto.
    """

    # --- Metadados/UI ---
    form_uid = forms.CharField(widget=forms.HiddenInput(), required=False, label="")  # ID auto-único no load

    # ===================== ABA: PEDIDO =====================
    pedido_requisitante = forms.CharField(label="Requisitante", max_length=150, required=False)
    pedido_cliente = forms.CharField(label="Cliente", max_length=150, required=False)
    pedido_status = forms.CharField(label="Status", max_length=80, required=False)

    # ===================== ABA: OS =====================
    os_estilo = forms.CharField(label="Estilo", max_length=150, required=False)
    os_arte = forms.CharField(label="Arte", max_length=150, required=False)
    os_modelagem = forms.CharField(label="Modelagem", max_length=150, required=False)
    os_pilotagem = forms.CharField(label="Pilotagem", max_length=150, required=False)
    os_encaixe = forms.CharField(label="Encaixe", max_length=150, required=False)

    # ===================== ABA: MANUFATURA =====================
    m_corte = forms.CharField(label="Corte", max_length=150, required=False)
    m_costura = forms.CharField(label="Costura", max_length=150, required=False)
    m_estamparia = forms.CharField(label="Estamparia", max_length=150, required=False)
    m_bordado = forms.CharField(label="Bordado", max_length=150, required=False)
    m_lavanderia = forms.CharField(label="Lavanderia", max_length=150, required=False)
    m_acabamento = forms.CharField(label="Acabamento", max_length=150, required=False)

    # ===================== ABA: MATERIAL =====================
    material_tecido_1 = forms.CharField(label="Tecido 1", max_length=150, required=False)

    # ===================== ABA: GRADE =====================
    # Gestão dinâmica via HTML/JS (sem fields fixos agora)

    # ===================== ABA: AVIAMENTOS (OFICINA) =====================
    av_oficina_linha_1 = forms.CharField(label="Linha 1", max_length=200, required=False)

    # ===================== ABA: AVIAMENTOS (ACABAMENTO) =====================
    avacab_sacola = forms.CharField(label="Sacola", max_length=150, required=False)
    avacab_tag = forms.CharField(label="Tag", max_length=150, required=False)

    class Meta:
        model = Product
        # ===== ABA: BLING (somente campos do model) =====
        fields = [
            "external_id",
            "sku",
            "name",
            "unit",
            "ncm",
            "origin",
            "price",
            "ipi_fixed",
            "notes",
            "status",
            "stock_qty",
            "cost_price",
            "supplier_code",
            "supplier_name",
            "location",
            "bling_extra",
            "external_link",
            "warranty_months_supplier",
            "clone_from_parent",
            "product_condition",
            "free_shipping",
            "fci_number",
            "video_url",
            "department",
            "unit_of_measure",
            "purchase_price",
            "icms_st_base_retencao",
            "icms_st_valor_retencao",
            "icms_proprio_substituto",
            "product_category",
            "extra_info",
            "cest",
            "gtin",
            "brand",
            "width_cm",
            "height_cm",
            "length_cm",
            "weight_net",
            "weight_gross",
            "is_active",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "extra_info": forms.Textarea(attrs={"rows": 3}),
            "bling_extra": forms.Textarea(attrs={"rows": 3}),
            "price": forms.NumberInput(attrs={"step": "0.01"}),
            "ipi_fixed": forms.NumberInput(attrs={"step": "0.01"}),
            "stock_qty": forms.NumberInput(attrs={"step": "0.001"}),
            "cost_price": forms.NumberInput(attrs={"step": "0.01"}),
            "purchase_price": forms.NumberInput(attrs={"step": "0.01"}),
            "icms_st_base_retencao": forms.NumberInput(attrs={"step": "0.01"}),
            "icms_st_valor_retencao": forms.NumberInput(attrs={"step": "0.01"}),
            "icms_proprio_substituto": forms.NumberInput(attrs={"step": "0.01"}),
            "width_cm": forms.NumberInput(attrs={"step": "0.01"}),
            "height_cm": forms.NumberInput(attrs={"step": "0.01"}),
            "length_cm": forms.NumberInput(attrs={"step": "0.01"}),
            "weight_net": forms.NumberInput(attrs={"step": "0.001"}),
            "weight_gross": forms.NumberInput(attrs={"step": "0.001"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Classe visual padrão
        for field in self.fields.values():
            base = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (base + " input").strip()
        # Placeholders úteis
        self.fields["sku"].widget.attrs.setdefault("placeholder", "Ex.: CAM-001-BR-PP")
        self.fields["ncm"].widget.attrs.setdefault("placeholder", "Ex.: 61091000")
        self.fields["gtin"].widget.attrs.setdefault("placeholder", "EAN/GTIN")
        self.fields["product_category"].widget.attrs.setdefault("placeholder", "Categoria interna")
