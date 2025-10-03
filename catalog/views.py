# -*- coding: utf-8 -*-
import json
from typing import cast, Any, Dict
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView,TemplateView  
from .models import Product
from .forms import ProductForm


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
    return json.dumps(data, ensure_ascii=False)


def _collect_extras_from_form(form: ProductForm) -> Dict[str, Any]:
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
        obj = cast(Product, self.object)  # hints para Pylance
        extras = _loads_json_safe(getattr(obj, "bling_extra", {}))
        ctx["tab_pedido"] = extras.get("pedido", {})
        ctx["tab_bling"] = obj
        ctx["tab_os"] = extras.get("os", {})
        ctx["tab_manufatura"] = extras.get("manufatura", {})
        ctx["tab_material"] = extras.get("material", {})
        ctx["tab_grade"] = extras.get("grade", {})
        ctx["tab_av_oficina"] = extras.get("aviamentos_oficina", {})
        ctx["tab_av_acab"] = extras.get("aviamentos_acabamento", {})
        return ctx


class ProdutoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    permission_required = "catalog.add_product"
    success_url = reverse_lazy("catalog:produto_list")
    template_name = "catalog/produto_form.html"

    def form_valid(self, form):
        resp = super().form_valid(form)
        obj = cast(Product, self.object)
        current = _loads_json_safe(getattr(obj, "bling_extra", {}))
        current.update(_collect_extras_from_form(form))
        obj.bling_extra = _dump_json(current)
        obj.save(update_fields=["bling_extra"])
        return resp


class ProdutoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    permission_required = "catalog.change_product"
    success_url = reverse_lazy("catalog:produto_list")
    template_name = "catalog/produto_form.html"

    def form_valid(self, form):
        resp = super().form_valid(form)
        obj = cast(Product, self.object)
        current = _loads_json_safe(getattr(obj, "bling_extra", {}))
        current.update(_collect_extras_from_form(form))
        obj.bling_extra = _dump_json(current)
        obj.save(update_fields=["bling_extra"])
        return resp


class ProdutoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Product
    permission_required = "catalog.delete_product"
    success_url = reverse_lazy("catalog:produto_list")
    template_name = "catalog/produto_confirm_delete.html"

class ProdutoImportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "catalog.add_product"
    template_name = "catalog/produto_import.html"
