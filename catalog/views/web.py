# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple, cast

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormMixin

from catalog.models import Product
from catalog.forms import ProductForm
from django.forms import BaseModelForm

# NOVO: merge idempotente dos vínculos de pessoas em bling_extra["people"]
from catalog.services.people_links import merge_people_links


# -----------------------------
# Utilidades internas
# -----------------------------

def _loads_json_safe(obj: Any) -> Dict[str, Any]:
    """
    Converte obj em dict de forma tolerante (str JSON, dict ou None).
    """
    if not obj:
        return {}
    if isinstance(obj, dict):
        return obj
    try:
        return json.loads(obj)
    except Exception:
        return {}


def _as_dict(obj: Any) -> Dict[str, Any]:
    return _loads_json_safe(obj)


def _dset(d: Dict[str, Any], path: List[str], value: Any) -> None:
    """
    Define 'value' em d[path[0]][path[1]]... criando dicts intermediários.
    """
    cur = d
    for key in path[:-1]:
        if key not in cur or not isinstance(cur.get(key), dict):
            cur[key] = {}
        cur = cur[key]  # type: ignore[assignment]
    cur[path[-1]] = value


# -----------------------------
# Coleta dos dados das abas (somente o necessário para este MVP)
# -----------------------------

def _collect_extras_from_form(form: ProductForm) -> Dict[str, Any]:
    """
    Coleta abas não-model do form para guardar em bling_extra (visual/legado).
    Atenção: vínculos de PESSOAS (IDs) são tratados pelo service merge_people_links().
    Aqui só armazenamos os rótulos/textos das abas (quando fizer sentido) e outros campos.
    """
    cd = form.cleaned_data

    # ============ PEDIDO ============
    pedido = {
        "requisitante": cd.get("pedido_requisitante") or "",
        "cliente": cd.get("pedido_cliente") or "",
        "status": cd.get("pedido_status") or "",
        # executante_* será injetado na view com base no request.user
    }

    # ============ OS ============
    os_tab = {
        "estilo": cd.get("os_estilo") or "",
        "arte": cd.get("os_arte") or "",
        "modelagem": cd.get("os_modelagem") or "",
        "pilotagem": cd.get("os_pilotagem") or "",
        "encaixe": cd.get("os_encaixe") or "",
    }

    # ============ MANUFATURA ============
    manuf_tab = {
        "corte": cd.get("m_corte") or "",
        "costura": cd.get("m_costura") or "",
        "estamparia": cd.get("m_estamparia") or "",
        "bordado": cd.get("m_bordado") or "",
        "lavanderia": cd.get("m_lavanderia") or "",
        "acabamento": cd.get("m_acabamento") or "",
    }

    # ============ MATERIAL / AVIAMENTOS (placeholders MVP) ============
    material_tab = {
        "tecidos": cd.get("material_tecidos") or cd.get("material_tecido_1") or "",
        "observacoes": cd.get("material_obs") or "",
    }

    avi_oficina = {
        "tag": cd.get("aviof_tag") or cd.get("av_oficina_linha_1") or "",
        "extras": [],
    }
    avi_acabamento = {
        "tag": cd.get("avacab_tag") or "",
        "sacola": cd.get("avacab_sacola") or "",
        "extras": [],
    }

    # ============ GRADE ============
    # Já validada/normalizada no form; aqui mantemos a string JSON (ou "{}")
    grade_payload = cd.get("grade_payload") or "{}"

    return {
        "pedido": pedido,
        "os": os_tab,
        "manufatura": manuf_tab,
        "material": material_tab,
        "avi_oficina": avi_oficina,
        "avi_acabamento": avi_acabamento,
        "grade": grade_payload,
    }


# -----------------------------
# Merge + geração de SKUs (mantém comportamento, com robustez extra)
# -----------------------------

def _merge_extras(base: Dict[str, Any], inc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge raso e seguro: não apaga chaves ausentes no incremento.
    Mantém 'grade' como string JSON vinda do form.
    """
    out = dict(base or {})
    for k, v in (inc or {}).items():
        if k == "grade" and isinstance(v, str):
            out[k] = v
            continue
        out[k] = v
    return out


def _normalize_grade_values(values: List[Any]) -> List[str]:
    """
    Normaliza cada item da lista de 'valores' de um parâmetro da grade.
    Aceita itens dicts (label/code) ou strings já normalizadas.
    Retorna lista de sufixos legíveis, priorizando 'code' > 'label' > str(item).
    """
    out: List[str] = []
    for v in values:
        if isinstance(v, dict):
            code = str(v.get("code") or "").strip()
            label = str(v.get("label") or "").strip()
            out.append(code or label or str(v))
        else:
            out.append(str(v))
    return [s for s in out if s]


def _generate_grade_skus(product: Product, form: ProductForm) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Gera grade_skus/grade_skus_meta a partir de bling_extra.grade (string JSON).
    Reaproveita payload já salvo pelo form (ProductForm.save()).
    """
    extras = _loads_json_safe(product.bling_extra)
    grade_raw = extras.get("grade") or "{}"
    try:
        grade = json.loads(grade_raw) if isinstance(grade_raw, str) else (grade_raw or {})
    except Exception:
        grade = {}

    params = (grade.get("parametros") or []) if isinstance(grade, dict) else []
    if not isinstance(params, list) or not params:
        return [], {"params": [], "count": 0}

    # Normaliza lista de listas (uma por parâmetro com valores)
    values_lists: List[List[str]] = []
    for prm in params:
        vals = prm.get("valores") or []
        if isinstance(vals, list) and vals:
            values_lists.append(_normalize_grade_values(vals))

    if not values_lists:
        return [], {"params": params, "count": 0}

    # Produto cartesiano simples
    combos: List[List[str]] = [[]]
    for lst in values_lists:
        combos = [c + [v] for c in combos for v in lst]

    items: List[Dict[str, Any]] = []
    for c in combos:
        suffix = "-".join(c)
        items.append({
            "sku": f"{product.sku}-{suffix}" if product.sku else suffix,
            "attrs": c,
        })

    meta = {"params": params, "count": len(items)}
    return items, meta


def _merge_and_generate_skus(product: Product, form: ProductForm) -> None:
    """
    Atualiza bling_extra com tabs do form, mescla vínculos de pessoas
    e preenche grade_skus/grade_skus_meta.
    """
    current = _loads_json_safe(product.bling_extra)
    inc = _collect_extras_from_form(form)

    # Mescla abas (texto/valores simples)
    merged = _merge_extras(current, inc)

    # Mescla IDs de pessoas em merged["people"] de forma idempotente
    product.bling_extra = merged  # passa estado atual para o service operar
    merge_people_links(product, form.cleaned_data)

    # Gera grade_skus com base no que ficou em bling_extra["grade"]
    grade_items, meta = _generate_grade_skus(product, form)

    # Grava de volta
    extra = _loads_json_safe(product.bling_extra)
    extra["grade_skus"] = grade_items
    extra["grade_skus_meta"] = meta
    product.bling_extra = extra
    product.save(update_fields=["bling_extra"])


def _inject_executante(product: Product, request: HttpRequest) -> None:
    """
    Injeta dados do executante atual (request.user) dentro de bling_extra["pedido"].
    """
    current = _loads_json_safe(getattr(product, "bling_extra", {}))
    pedido = _loads_json_safe(current.get("pedido"))

    u = getattr(request, "user", None)
    if u is not None:
        pedido["executante_id"] = getattr(u, "id", None)
        pedido["executante_username"] = getattr(u, "username", "") or getattr(u, "email", "")
        try:
            pedido["executante_fullname"] = u.get_full_name() or ""
        except Exception:
            pedido["executante_fullname"] = ""

    current["pedido"] = pedido
    product.bling_extra = current
    product.save(update_fields=["bling_extra"])


# -----------------------------
# Views
# -----------------------------

class ProdutoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Product
    permission_required = "catalog.view_product"
    template_name = "catalog/produto_list.html"
    context_object_name = "produtos"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().order_by("-id")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            # MAIS ROBUSTO: usa Q combinando name|sku e preserva ordenação
            qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))
        return qs


class ProdutoDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Product
    permission_required = "catalog.view_product"
    template_name = "catalog/produto_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        obj: Product = cast(Product, self.get_object())
        extras = _loads_json_safe(getattr(obj, "bling_extra", {}))
        ctx["extras"] = extras

        # Abas
        ctx["tab_pedido"] = extras.get("pedido", {})
        ctx["tab_os"] = extras.get("os", {})
        ctx["tab_manufatura"] = extras.get("manufatura", {})
        ctx["tab_material"] = extras.get("material", {})
        ctx["tab_avi_oficina"] = extras.get("avi_oficina", {})
        ctx["tab_avi_acabamento"] = extras.get("avi_acabamento", {})
        ctx["tab_grade"] = extras.get("grade", {})
        ctx["tab_grade_skus"] = extras.get("grade_skus", [])
        ctx["tab_grade_skus_meta"] = extras.get("grade_skus_meta", {})

        return ctx


class ProdutoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    permission_required = "catalog.add_product"
    success_url = reverse_lazy("catalog:produto_list")
    template_name = "catalog/produto_form.html"

    @transaction.atomic
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        resp = super().form_valid(form)
        obj: Product = cast(Product, form.instance)
        _inject_executante(obj, self.request)
        _merge_and_generate_skus(obj, cast(ProductForm, form))
        messages.success(self.request, _("Produto salvo com sucesso."))
        return resp


class ProdutoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    permission_required = "catalog.change_product"
    success_url = reverse_lazy("catalog:produto_list")
    template_name = "catalog/produto_form.html"

    @transaction.atomic
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        resp = super().form_valid(form)
        obj: Product = cast(Product, form.instance)
        _inject_executante(obj, self.request)
        _merge_and_generate_skus(obj, cast(ProductForm, form))
        messages.success(self.request, _("Produto salvo com sucesso."))
        return resp


class ProdutoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Product
    permission_required = "catalog.delete_product"
    success_url = reverse_lazy("catalog:produto_list")
    template_name = "catalog/produto_confirm_delete.html"


class ProdutoImportView(LoginRequiredMixin, PermissionRequiredMixin, FormMixin, ListView):
    model = Product
    permission_required = "catalog.add_product"
    template_name = "catalog/produto_import.html"
    success_url = reverse_lazy("catalog:produto_list")
    form_class = ProductForm  # placeholder para manter layout

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        messages.info(request, _("Importação não implementada no MVP."))
        return redirect(self.success_url)


@require_GET
def collaborator_search_legacy(request: HttpRequest) -> JsonResponse:
    """
    Endpoint legado mantido para compat (caso algum template antigo ainda aponte aqui).
    Recomendação: usar /people/api/search/ (app people) com o nosso front atual.
    """
    return JsonResponse({"items": []})
