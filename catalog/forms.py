# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from django import forms
from django.core.exceptions import ValidationError

from .models import Product


# =========================
# Helpers internos (validação do payload da Grade)
# =========================

def _as_dict(val: Any) -> Dict[str, Any]:
    if isinstance(val, dict):
        return val
    if not val:
        return {}
    try:
        return json.loads(str(val))
    except Exception:
        return {}


def _norm(s: Any) -> str:
    return str(s or "").strip()


def _is_code2(v: str) -> bool:
    return len(v) == 2 and v.isdigit()


def _extract_params(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    ps = payload.get("parametros")
    return ps if isinstance(ps, list) else []


def _validate_grade_payload_struct(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Normaliza e valida grade_payload:
      {
        "parametros": [
          {"chave":"TAM","role":"size","valores":[{"label":"P","code":"02"}, ...]},
          {"chave":"COR","role":"color","valores":[{"label":"PRETO","code":"02"}, ...]},
          {"chave":"OUTRO","role":"attr","valores":[{"label":"X"}, {"label":"Y"}]}
        ],
        "orientacao": "colunas" | "linhas"
      }

    Regras:
      - role ∈ {size,color,attr}
      - no máx. 1 size e 1 color
      - se role ∈ {size,color}, values precisam de code 2 dígitos, únicos dentro do parâmetro
      - valores sempre têm "label" (string não vazia)
    """
    issues: List[str] = []
    out: Dict[str, Any] = {
        "parametros": [],
        "orientacao": payload.get("orientacao") if payload.get("orientacao") in ("colunas", "linhas") else "colunas",
    }

    params = _extract_params(payload)
    size_count = 0
    color_count = 0

    for p in params:
        if not isinstance(p, dict):
            continue
        chave = _norm(p.get("chave")) or ""
        role = (_norm(p.get("role")) or "attr").lower()
        if role not in ("size", "color", "attr"):
            role = "attr"

        if role == "size":
            size_count += 1
        elif role == "color":
            color_count += 1

        raw_vals = p.get("valores") or []
        vals_norm: List[Dict[str, Any]] = []
        seen_codes: set[str] = set()

        if isinstance(raw_vals, list):
            for v in raw_vals:
                if not isinstance(v, dict):
                    continue
                label = _norm(v.get("label"))
                if not label:
                    continue
                item: Dict[str, Any] = {"label": label}
                if role in ("size", "color"):
                    code = _norm(v.get("code"))
                    if not _is_code2(code):
                        issues.append(f"Código inválido em '{chave}' → '{label}'. Esperado 2 dígitos (00..99).")
                    else:
                        if code in seen_codes:
                            issues.append(f"Código duplicado '{code}' em '{chave}'.")
                        seen_codes.add(code)
                        item["code"] = code
                vals_norm.append(item)

        out["parametros"].append({
            "chave": chave,
            "role": role,
            "valores": vals_norm,
        })

    if size_count > 1:
        issues.append("Mais de um parâmetro marcado como SIZE.")
    if color_count > 1:
        issues.append("Mais de um parâmetro marcado como COLOR.")

    return out, issues


# =========================
# Form
# =========================

class ProductForm(forms.ModelForm):
    """
    Form de Produto com abas:
    - pedido, bling, os, manufatura, material, grade, av-oficina, av-acab
    """

    # --- Metadados/UI ---
    form_uid = forms.CharField(widget=forms.HiddenInput(), required=False, label="")

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

    # ===================== ABA: GRADE (payload dinâmico vindo do JS) =====================
    grade_payload = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_grade_payload", "autocomplete": "off"}),
        label="",
        help_text="JSON serializado pela aba Grade (preenchido via JS).",
    )

    # ===================== ABA: AVIAMENTOS =====================
    av_oficina_linha_1 = forms.CharField(label="Linha 1", max_length=200, required=False)
    avacab_sacola = forms.CharField(label="Sacola", max_length=150, required=False)
    avacab_tag = forms.CharField(label="Tag", max_length=150, required=False)

    class Meta:
        model = Product
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

    # ----------------- init -----------------

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

        # Pré-carregar grade_payload a partir de bling_extra.grade (edição)
        try:
            inst = getattr(self, "instance", None)
            extra = getattr(inst, "bling_extra", None) if inst else None
            extra_dict = _as_dict(extra)
            grade = extra_dict.get("grade")
            if isinstance(grade, dict) and grade:
                self.fields["grade_payload"].initial = json.dumps(
                    grade, ensure_ascii=False, separators=(",", ":")
                )
        except Exception:
            # fail-silent para não bloquear o form por dados legados
            pass

    # ----------------- clean -----------------

    def clean_grade_payload(self) -> str:
        """
        Valida e normaliza o JSON da Grade. Retorna string JSON compacta ou vazio.
        """
        raw = (self.cleaned_data.get("grade_payload") or "").strip()
        if not raw:
            return ""

        try:
            obj = json.loads(raw)
        except Exception:
            raise ValidationError("grade_payload inválido (JSON malformado).")

        if not isinstance(obj, dict):
            raise ValidationError("Estrutura da grade inválida.")

        norm, issues = _validate_grade_payload_struct(obj)

        if issues:
            # concatena mensagens amigáveis; 1 erro por linha
            raise ValidationError("\n".join(issues))

        # retorna JSON compactado e normalizado
        return json.dumps(norm, ensure_ascii=False, separators=(",", ":"))

    # ----------------- save -----------------

    def save(self, commit: bool = True) -> Product:
        """
        Persistência idempotente da Grade dentro de bling_extra (sem gerar SKUs aqui).
        - Garante dict em bling_extra.
        - Merge sem pisar outras chaves (pedido, os, etc).
        - Limpa 'grade' se payload vier vazio.
        """
        instance: Product = super().save(commit=False)

        # Base bling_extra -> dict
        extra = instance.bling_extra
        if not extra:
            extra = {}
        elif isinstance(extra, str):
            try:
                extra = json.loads(extra)
            except Exception:
                extra = {}

        raw = (self.cleaned_data.get("grade_payload") or "").strip()
        payload: Optional[Dict[str, Any]] = None
        if raw:
            try:
                payload = json.loads(raw)
            except Exception:
                payload = None

        # Decide se limpa ou atualiza
        def _is_empty_grade(p: Optional[Dict[str, Any]]) -> bool:
            if not p or not isinstance(p, dict):
                return True
            params = _extract_params(p)
            # Sem parâmetros ou todos sem valores => vazio
            if not params:
                return True
            for prm in params:
                vals = prm.get("valores") or []
                if isinstance(vals, list) and len(vals) > 0:
                    return False
            return True

        if _is_empty_grade(payload):
            if isinstance(extra, dict):
                extra.pop("grade", None)
        else:
            if not isinstance(extra, dict):
                extra = {}
            extra["grade"] = payload

            # Não geramos SKUs aqui; o views/web.py chama o service e popula 'grade_skus'

        instance.bling_extra = extra

        if commit:
            instance.save()
            self.save_m2m()

        return instance
