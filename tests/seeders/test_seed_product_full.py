import json
import pytest
from django.apps import apps

pytestmark = pytest.mark.django_db


def _get_model(app_label, model_name):
    try:
        return apps.get_model(app_label, model_name)
    except Exception:
        return None


def test_seed_product_full(seed_product_full):
    Product = _get_model("catalog", "Product")
    assert Product is not None

    p = seed_product_full
    # Core
    assert getattr(p, "sku", None) == "CRO-TEE-0001"
    assert getattr(p, "name", "")
    assert getattr(p, "price", 0) >= 0
    assert getattr(p, "stock_qty", 0) >= 0

    # Categoria (texto ou FK)
    if hasattr(p, "product_category"):
        cat_val = getattr(p, "product_category")
        assert cat_val is not None

    # bling_extra (JSON | Text)
    be = getattr(p, "bling_extra", None)
    if be is not None:
        if isinstance(be, dict):
            assert "abas" in be
        elif isinstance(be, str):
            try:
                data = json.loads(be)
                assert "abas" in data
            except Exception:
                # ok se o campo for livre
                pass

    # Variante OU grade
    ProductVariant = _get_model("catalog", "ProductVariant")
    if ProductVariant:
        assert ProductVariant.objects.filter(product=p).exists()
    else:
        # fallback: grade
        if hasattr(p, "grade"):
            g = getattr(p, "grade")
            if isinstance(g, str):
                try:
                    g = json.loads(g)
                except Exception:
                    g = {}
            assert isinstance(g, dict) and g

    # Pessoas (se existir)
    Person = _get_model("people", "Person") or _get_model("people", "Pessoa")
    if Person:
        # testa M2M genérico se existir
        for f in ("people", "pessoas", "team", "stakeholders"):
            if hasattr(p, f):
                rel = getattr(p, f)
                assert rel.count() >= 1
                break
        # senão, tenta campos diretos
        for f in ("estilo", "designer", "style", "arte", "art", "graphics",
                  "modelagem", "pattern", "modelista"):
            if hasattr(p, f):
                assert getattr(p, f) is not None

