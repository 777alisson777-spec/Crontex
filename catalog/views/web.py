# -*- coding: utf-8 -*-
import json
from itertools import product as cart_product
from typing import Any, Dict, List, Tuple, cast

from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import (
    CreateView,
    UpdateView,
    ListView,
    DetailView,
    DeleteView,
    TemplateView,
)

from catalog.models import Product
from catalog.forms import ProductForm


# ============================== UTIL ==============================
def _loads_json_safe(val: Any) -> Dict[str, Any]:
    """Aceita None/str/dict e devolve dict."""
    if not val:
        return {}
    if isinstance(val, dict):
        return val
    try:
        return json.loads(str(val))
    except Exception:
        return {}


def _dump_json(data: Dict[str, Any]) -> str:
    """Dump bonito e tolerante (utf-8)."""
    return json.dumps(data, ensure_ascii=False)


def _collect_extras_from_form(form: ProductForm) -> Dict[str, Any]:
    """Coleta abas não-model do form para guardar em bling_extra (legado/visual)."""
    cd = form.cleaned_data

    pedido = {
        "requisitante": cd.get("pedido_requisitante") or "",
        "cliente": cd.get("pedido_cliente") or "",
        "status": cd.get("pedido_status") or "",
    }

    os_tab = {
        "estilo": cd.get("os_estilo") or "",
        "arte": cd.get("os_arte") or "",
        "modelagem": cd.get("os_modelagem") or "",
        "pilotagem": cd.get("os_pilotagem") or "",
        "encaixe": cd.get("os_encaixe") or "",
    }

    manuf = {
        "corte": cd.get("m_corte") or "",
        "costura": cd.get("m_costura") or "",
        "estamparia": cd.get("m_estamparia") or "",
        "bordado": cd.get("m_bordado") or "",
        "lavanderia": cd.get("m_lavanderia") or "",
        "acabamento": cd.get("m_acabamento") or "",
    }

    material = {"tecido_1": cd.get("material_tecido_1") or ""}

    # grade_json (nova UI) já é persistido dentro de ProductForm.save() em bling_extra["grade"]
    # Aqui mantemos a estrutura de "abas" que você já tinha:
    grade = {"cabecalho": [], "linhas": []}

    av_oficina = {
        "linha_1": cd.get("av_oficina_linha_1") or "",
        "itens": [],
    }

    av_acab = {
        "sacola": cd.get("avacab_sacola") or "",
        "tag": cd.get("avacab_tag") or "",
        "extras": [],
    }

    return {
        "pedido": pedido,
        "os": os_tab,
        "manufatura": manuf,
        "material": material,
        "grade": grade,
        "aviamentos_oficina": av_oficina,
        "aviamentos_acabamento": av_acab,
    }


# ============================== EAN/GRADES ==============================
def _ean13_check_digit(num12: str) -> str:
    """
    Calcula dígito verificador EAN-13 para uma string de 12 dígitos.
    """
    s = 0
    for i, ch in enumerate(num12):
        d = ord(ch) - 48  # int rápido
        s += d * (3 if (i % 2) else 1)
    dv = (10 - (s % 10)) % 10
    return str(dv)


def _two_digit(i: int) -> str:
    """Formata índice 1-based como '01', '02', ..."""
    return f"{i:02d}"


def _derive_ref_base(obj: Product) -> Tuple[str, str]:
    """
    Política conservadora:
    - REF = primeiros 4 chars do SKU (se não, '0000')
    - BASE = últimos 4 chars numéricos dentro do SKU; fallback '0000'
    Tudo em dígitos apenas; qualquer não-numérico vira '0'.
    """
    sku = (obj.sku or "").strip()
    ref_raw = (sku[:4] or "0000").ljust(4, "0")[:4]
    base_raw = (sku[-4:] or "0000").rjust(4, "0")[:4]

    ref = "".join(ch if ch.isdigit() else "0" for ch in ref_raw)
    base = "".join(ch if ch.isdigit() else "0" for ch in base_raw)
    if len(ref) != 4:
        ref = "0000"
    if len(base) != 4:
        base = "0000"
    return ref, base


def _generate_grade_skus(obj: Product) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Gera SKUs EAN-13 a partir de bling_extra["grade"].
    Espera estrutura:
      {
        "parametros": [
          {"chave": "tam", "valores": ["P","M","G"]},
          {"chave": "cor", "valores": ["Preto","Branco"]}
        ]
      }

    Regras:
    - Considera, no máximo, DOIS parâmetros para o EAN-13 (tam e cor).
    - Mapeia cada valor para código sequencial de 2 dígitos (01..99) por parâmetro.
    - Monta base de 12 dígitos: [REF(4)][BASE(4)][TAM(2)][COR(2)] e calcula DV.
    - Se existir apenas 1 parâmetro, o segundo vira '00'.
    - Se houver mais de 2 parâmetros, os extras são ignorados para o EAN, mas permanecem no combo.

    Retorna:
      (rows, meta)
      rows = [{ "combo": {chave1:val1, chave2:val2, ...}, "sku": "ean13" }, ...]
      meta = {"ref":..., "base":..., "param_tamanho": chave1, "param_cor": chave2, "warn": "...(opcional)"}
    """
    extra = _loads_json_safe(getattr(obj, "bling_extra", {}))
    grade = extra.get("grade") or {}
    parametros = grade.get("parametros") or []

    rows: List[Dict[str, Any]] = []
    meta: Dict[str, Any] = {}

    if not isinstance(parametros, list) or len(parametros) == 0:
        return rows, meta

    # Ordena parâmetros na ordem que o usuário informou
    params_norm = []
    for p in parametros:
        chave = (p.get("chave") or "").strip()
        valores = [str(v).strip() for v in (p.get("valores") or []) if str(v).strip()]
        if not chave:
            continue
        params_norm.append({"chave": chave, "valores": valores})

    if len(params_norm) == 0:
        return rows, meta

    # Até dois parâmetros para codificação
    p1 = params_norm[0]
    p2 = params_norm[1] if len(params_norm) > 1 else {"chave": "", "valores": []}

    meta["param_tamanho"] = p1["chave"]
    meta["param_cor"] = p2.get("chave") or ""
    if len(params_norm) > 2:
        meta["warn"] = "Mais de 2 parâmetros informados; somente os 2 primeiros foram usados no EAN-13."

    # Mapas de valor -> código 2d (01..)
    map1 = {v: _two_digit(i + 1) for i, v in enumerate(p1["valores"])} or {"—": "00"}
    map2 = {v: _two_digit(i + 1) for i, v in enumerate(p2.get("valores", []))} or {"—": "00"}

    ref, base = _derive_ref_base(obj)
    meta["ref"] = ref
    meta["base"] = base

    # Produto cartesiano de TODOS os parâmetros (para exibir combo completo),
    # mas só p1/p2 entram no código do EAN.
    axes = [p["valores"] if p["valores"] else ["—"] for p in params_norm]
    all_combos = list(cart_product(*axes))  # tuples de valores, na ordem dos params_norm

    for combo_vals in all_combos:
        combo_dict = {params_norm[i]["chave"]: combo_vals[i] for i in range(len(params_norm))}
        # códigos 2d
        v1 = combo_dict.get(p1["chave"], "—")
        v2 = combo_dict.get(p2.get("chave", ""), "—") if p2.get("chave") else "—"
        c1 = map1.get(v1, "00")
        c2 = map2.get(v2, "00")

        base12 = f"{ref}{base}{c1}{c2}"
        dv = _ean13_check_digit(base12)
        ean13 = f"{base12}{dv}"

        rows.append({"combo": combo_dict, "sku": ean13})

    return rows, meta


def _merge_and_generate_skus(obj: Product, form: ProductForm) -> None:
    """
    Mescla abas auxiliares ao bling_extra e injeta:
      - grade_skus: lista de {combo, sku}
      - grade_skus_meta: metadados para exibição
    """
    # 1) base atual
    current = _loads_json_safe(getattr(obj, "bling_extra", {}))

    # 2) merge abas não-model
    current.update(_collect_extras_from_form(form))

    # 3) garante que 'grade' salva pelo form permaneça dict
    if isinstance(current.get("grade"), str):
        try:
            current["grade"] = json.loads(current["grade"])
        except Exception:
            current["grade"] = {}

    # 4) gera SKUs
    rows, meta = _generate_grade_skus(obj)
    current["grade_skus"] = rows
    current["grade_skus_meta"] = meta

    # 5) persiste
    obj.bling_extra = current
    obj.save(update_fields=["bling_extra"])


# ============================== VIEWS ==============================
class ProdutoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Product
    permission_required = "catalog.view_product"
    template_name = "catalog/produto_list.html"
    context_object_name = "object_list"


class ProdutoDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Product
    permission_required = "catalog.view_product"
    template_name = "catalog/produto_detail.html"
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = cast(Product, self.object)
        extras = _loads_json_safe(getattr(obj, "bling_extra", {}))

        ctx["tab_pedido"] = extras.get("pedido", {})
        ctx["tab_bling"] = obj
        ctx["tab_os"] = extras.get("os", {})
        ctx["tab_manufatura"] = extras.get("manufatura", {})
        ctx["tab_material"] = extras.get("material", {})
        ctx["tab_grade"] = extras.get("grade", {})
        ctx["tab_av_oficina"] = extras.get("aviamentos_oficina", {})
        ctx["tab_av_acab"] = extras.get("aviamentos_acabamento", {})

        # Nova: grade + SKUs gerados no servidor (para render no detalhe)
        ctx["tab_grade_skus"] = extras.get("grade_skus", [])
        ctx["tab_grade_skus_meta"] = extras.get("grade_skus_meta", {})

        return ctx


class ProdutoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    permission_required = "catalog.add_product"
    success_url = reverse_lazy("catalog:produto_list")
    template_name = "catalog/produto_form.html"

    def form_valid(self, form: ProductForm):
        # salva model + bling_extra.grade via ProductForm.save()
        resp = super().form_valid(form)
        obj = cast(Product, self.object)

        # Mescla extras e gera grade_skus
        _merge_and_generate_skus(obj, form)

        return resp


class ProdutoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    permission_required = "catalog.change_product"
    success_url = reverse_lazy("catalog:produto_list")
    template_name = "catalog/produto_form.html"

    def form_valid(self, form: ProductForm):
        resp = super().form_valid(form)
        obj = cast(Product, self.object)

        _merge_and_generate_skus(obj, form)

        return resp


class ProdutoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Product
    permission_required = "catalog.delete_product"
    success_url = reverse_lazy("catalog:produto_list")
    template_name = "catalog/produto_confirm_delete.html"


class ProdutoImportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "catalog.add_product"
    template_name = "catalog/produto_import.html"
