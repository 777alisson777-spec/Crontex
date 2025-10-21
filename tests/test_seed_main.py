# tests/test_seed_main.py
# -*- coding: utf-8 -*-
"""
Seed + Teste E2E do ProductForm (modo criação), com dados únicos,
preenchendo TODOS os campos relevantes do form e validando persistência da grade.

Execução:
    pytest -q tests/test_seed_main.py
Env vars úteis:
    SEED_N=10 pytest -q tests/test_seed_main.py

Dependências:
    - pytest
    - pytest-django
"""

from __future__ import annotations

import json
import os
import random
import string
import time
from typing import Any, Dict, List

import pytest

from catalog.models import Product

# ------------- Config do Seed -------------
N_SEEDS = int(os.getenv("SEED_N", "5"))
PRICE_BASE = 59.90
WEIGHT_BASE = 0.250


# ------------- Helpers -------------

def _uid(prefix: str = "P") -> str:
    tail = "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"{prefix}-{int(time.time())}-{tail}"


def _payload_grade_ok() -> Dict[str, Any]:
    size_vals = [
        {"label": "P", "code": "01"},
        {"label": "M", "code": "02"},
        {"label": "G", "code": "03"},
    ]
    color_vals = [
        {"label": "PRETO", "code": "10"},
        {"label": "BRANCO", "code": "11"},
    ]
    return {
        "parametros": [
            {"chave": "TAM", "role": "size", "valores": size_vals},
            {"chave": "COR", "role": "color", "valores": color_vals},
        ],
        "orientacao": "colunas",
    }


def _form_minimals_for_product(sku: str, name: str) -> Dict[str, Any]:
    return {
        "external_id": "",
        "sku": sku,
        "name": name,
        "unit": "UN",
        "ncm": "61091000",
        "origin": "0",
        "price": f"{PRICE_BASE + random.randint(0, 40):.2f}",
        "ipi_fixed": "0.00",
        "notes": "Seed automático",
        "status": "ATIVO",
        "stock_qty": "10.000",
        "cost_price": "30.00",
        "supplier_code": "FORN-XYZ",
        "supplier_name": "Fornecedor Seed",
        "location": "A1",
        "bling_extra": json.dumps({"fonte": "seed-main"}, ensure_ascii=False),
        "external_link": "",
        "warranty_months_supplier": "0",
        "clone_from_parent": "on",  # BooleanField
        "product_condition": "novo",
        "free_shipping": "",        # BooleanField off
        "fci_number": "",
        "video_url": "",
        "department": "Vestuário",
        "unit_of_measure": "un",
        "purchase_price": "25.00",
        "icms_st_base_retencao": "0.00",
        "icms_st_valor_retencao": "0.00",
        "icms_proprio_substituto": "0.00",
        "product_category": "Camisetas",
        "extra_info": "Gerado via seed main",
        "cest": "1234567",          # ✅ máx 7 chars
        "gtin": "",
        "brand": "MarcaSeed",
        "width_cm": "40.00",
        "height_cm": "60.00",
        "length_cm": "1.00",
        "weight_net": f"{WEIGHT_BASE:.3f}",
        "weight_gross": f"{WEIGHT_BASE + 0.050:.3f}",
        "is_active": "on",          # BooleanField
        # --- Abas form-only (não vão pro model, mas validam UX) ---
        "pedido_requisitante": "User Seed",
        "pedido_cliente": "Cliente Seed",
        "pedido_status": "Novo",
        "os_estilo": "Básico",
        "os_arte": "Tipográfica",
        "os_modelagem": "Regular",
        "os_pilotagem": "OK",
        "os_encaixe": "OK",
        "m_corte": "Terceiro",
        "m_costura": "Interno",
        "m_estamparia": "Silk",
        "m_bordado": "",
        "m_lavanderia": "",
        "m_acabamento": "Vapor",
        "material_tecido_1": "100% Algodão",
        "av_oficina_linha_1": "Linha poliéster",
        "avacab_sacola": "Papel",
        "avacab_tag": "Tag padrão",
    }


def _debug_snapshot(product: Product) -> str:
    be = product.bling_extra or {}
    vg = product.variations_grid or {}
    return (
        f"SKU={product.sku} | name={product.name} | status={product.status}\n"
        f"bling_extra.keys={list(be.keys())} | grade={'grade' in be}\n"
        f"variations_grid.rows={len((vg or {}).get('rows', [])) if vg else 0}"
    )


# ------------- Teste principal -------------

@pytest.mark.django_db
def test_seed_main_preenche_form_e_persiste_grade(client, settings):
    """
    SEED MAIN:
    - Cria N produtos via ProductForm (modo criação).
    - Preenche TODOS os campos (incluindo abas).
    - Persiste grade em bling_extra['grade'].
    - (Opcional) se houver espelho em variations_grid, valida shape.
    """
    from catalog.forms import ProductForm  # import tardio

    created_pks: List[int] = []

    for i in range(N_SEEDS):
        sku = _uid("SKU")
        name = f"Camiseta Seed {i+1}"

        form_data = _form_minimals_for_product(sku, name)
        form_data["grade_payload"] = json.dumps(
            _payload_grade_ok(), ensure_ascii=False, separators=(",", ":")
        )

        form = ProductForm(data=form_data)
        assert form.is_valid(), f"[Form inválido - {sku}] errors={form.errors.as_json()} data={form_data}"

        obj = form.save(commit=True)
        assert isinstance(obj, Product), f"[Save fail - {sku}] retorno não é Product"
        assert obj.pk is not None, f"[{sku}] PK não foi definido após save()."
        created_pks.append(int(obj.pk))

        snap = _debug_snapshot(obj)

        be = obj.bling_extra or {}
        assert isinstance(be, dict), f"[{sku}] bling_extra não é dict | {snap}"
        assert "grade" in be, f"[{sku}] grade NÃO persistiu em bling_extra | {snap}"
        assert isinstance(be["grade"], dict), f"[{sku}] bling_extra['grade'] não é dict | {snap}"
        assert be["grade"].get("parametros"), f"[{sku}] grade.parametros vazio | {snap}"

        vg = (obj.variations_grid or {})
        if vg:
            assert isinstance(vg, dict), f"[{sku}] variations_grid não é dict | {snap}"
            rows = vg.get("rows", [])
            assert isinstance(rows, list), f"[{sku}] variations_grid.rows não é lista | {snap}"
            for r in rows:
                assert isinstance(r.get("name"), str) and r.get("name").strip(), f"[{sku}] row.name inválido | {snap}"
                vals = r.get("values", [])
                assert isinstance(vals, list), f"[{sku}] row.values não é lista | {snap}"

    assert len(created_pks) == N_SEEDS, f"Seed criou {len(created_pks)}/{N_SEEDS} produtos"

    for pk in created_pks:
        p = Product.objects.get(pk=pk)
        be = p.bling_extra or {}
        assert "grade" in be, f"[Reload {p.sku}] grade não persistiu após reload | {_debug_snapshot(p)}"
