# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any
import io

import pandas as pd

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView

from .models import Product
from .forms import ProductForm
from .schema import FIELD_BY_HEADER, is_required_present


# ---------- List / CRUD ----------

class ProductListView(LoginRequiredMixin, ListView):
    template_name = "catalog/produto_list.html"
    paginate_by = 20

    def get_queryset(self):
        q = (self.request.GET.get("q") or "").strip()
        qs = Product.objects.all()
        if q:
            qs = qs.filter(
                Q(sku__icontains=q) |
                Q(name__icontains=q) |
                Q(ncm__icontains=q) |
                Q(product_category__icontains=q) |
                Q(brand__icontains=q)
            )
        return qs.order_by("sku")


class ProductCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "catalog.add_product"
    template_name = "catalog/produto_form.html"
    form_class = ProductForm
    success_url = reverse_lazy("catalog:produto_list")


class ProductUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "catalog.change_product"
    template_name = "catalog/produto_form.html"
    form_class = ProductForm
    queryset = Product.objects.all()
    success_url = reverse_lazy("catalog:produto_list")


class ProductDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = "catalog.delete_product"
    template_name = "catalog/produto_confirm_delete.html"
    queryset = Product.objects.all()
    success_url = reverse_lazy("catalog:produto_list")


# ---------- Importação ----------

class ImportForm(forms.Form):
    file = forms.FileField(help_text="Envie .xlsx ou .csv no layout do Bling.")


class ProductImportView(PermissionRequiredMixin, FormView):
    permission_required = "catalog.add_product"
    template_name = "catalog/produto_import.html"
    form_class = ImportForm
    success_url = reverse_lazy("catalog:produto_list")

    NUMERIC_FIELDS = {
        "price", "ipi_fixed", "stock_qty", "cost_price",
        "purchase_price", "icms_st_base_retencao",
        "icms_st_valor_retencao", "icms_proprio_substituto",
        "width_cm", "height_cm", "length_cm",
        "weight_net", "weight_gross",
    }

    BOOL_FIELDS_TRUE = {"1", "true", "t", "sim", "yes", "y"}

    def form_valid(self, form: ImportForm) -> HttpResponse:
        f = form.cleaned_data["file"]
        fname = f.name.lower()

        buf = io.BytesIO(f.read())
        if fname.endswith(".csv"):
            df = pd.read_csv(buf, sep=";", dtype=str).fillna("")
        else:
            df = pd.read_excel(buf, engine="openpyxl", dtype=str).fillna("")

        headers = list(df.columns)
        if not is_required_present(headers):
            messages.error(self.request, "Headers obrigatórios ausentes: Código e Descrição.")
            return redirect("catalog:produto_list")

        rename_map = {h: FIELD_BY_HEADER[h] for h in headers if h in FIELD_BY_HEADER}
        df = df.rename(columns=rename_map)

        created = updated = errors = 0

        for line_no, (_, row) in enumerate(df.iterrows(), start=2):
            try:
                payload: dict[str, Any] = {}

                for _, model_key in rename_map.items():
                    val = row.get(model_key, "")
                    payload[model_key] = val

                for k in self.NUMERIC_FIELDS:
                    if k in payload:
                        v = str(payload[k]).strip()
                        if v == "":
                            payload[k] = None
                        else:
                            v = v.replace(".", "").replace(",", ".")
                            try:
                                payload[k] = Decimal(v)
                            except (InvalidOperation, ValueError):
                                raise ValueError(f"{k}: valor numérico inválido '{row.get(k)}'")

                if "clone_from_parent" in payload:
                    payload["clone_from_parent"] = str(payload["clone_from_parent"]).lower() in self.BOOL_FIELDS_TRUE
                if "free_shipping" in payload:
                    payload["free_shipping"] = str(payload["free_shipping"]).lower() in self.BOOL_FIELDS_TRUE
                if "is_active" in payload:
                    payload["is_active"] = str(payload["is_active"]).lower() in self.BOOL_FIELDS_TRUE

                extras: dict[str, Any] = {}
                for original_header in headers:
                    if original_header not in FIELD_BY_HEADER:
                        val = row.get(original_header, "")
                        if val not in ("", None):
                            extras[original_header] = val
                if extras:
                    payload["bling_extra"] = {**(payload.get("bling_extra") or {}), **extras}

                sku = (payload.get("sku") or "").strip()
                name = (payload.get("name") or "").strip()
                if not sku or not name:
                    raise ValueError("SKU e Descrição são obrigatórios.")

                _, created_flag = Product.objects.update_or_create(
                    sku=sku,
                    defaults=payload,
                )
                created += int(created_flag)
                updated += int(not created_flag)

            except Exception as exc:
                errors += 1
                messages.warning(self.request, f"Linha {line_no}: {exc}")

        messages.success(
            self.request,
            f"Import concluído. Criados: {created}. Atualizados: {updated}. Erros: {errors}."
        )
        return redirect("catalog:produto_list")
