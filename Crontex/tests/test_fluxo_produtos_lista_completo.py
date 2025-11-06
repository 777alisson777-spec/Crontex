# -*- coding: utf-8 -*-
import pytest
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from catalog.models import Product


@pytest.mark.django_db
def test_fluxo_criar_produto_completo_e_listar(client):
    u = User.objects.create_user("qa_full", password="x")
    u.user_permissions.add(Permission.objects.get(codename="add_product"))
    u.user_permissions.add(Permission.objects.get(codename="view_product"))
    client.login(username="qa_full", password="x")

    create_url = reverse("catalog:produto_create")
    list_url = reverse("catalog:produto_list")

    payload = {
        "sku": "SKU-FULL-001",
        "name": "Produto Completo",
        "price": "199.90",
        "cost_price": "120.00",
        "purchase_price": "110.00",
        "stock_qty": "15",
        "ncm": "61091000",
        "gtin": "7891234567895",
        "ipi_fixed": "0.00",
        "width_cm": "30.00",
        "height_cm": "2.00",
        "length_cm": "40.00",
        "weight_net": "0.200",
        "weight_gross": "0.250",
        "product_category": "Camisetas",
        "department": "Vestuário",
        "brand": "Crontex",
        "unit": "UN",
        "unit_of_measure": "UN",
        "supplier_code": "FOR-001",
        "supplier_name": "Fornecedor X",
        "location": "A1-03",
        "external_link": "https://exemplo.com/p/SKU-FULL-001",
        "notes": "Teste criação completa",
        "form_uid": "uid-full-1",
    }

    resp = client.post(create_url, payload, follow=True)
    # Diagnóstico: se falhar, mostra os erros do form na resposta
    if not Product.objects.filter(sku="SKU-FULL-001").exists():
        try:
            ctx_forms = [c.get("form") for c in resp.context if c and "form" in c]
            err = ctx_forms[0].errors.as_json() if ctx_forms and ctx_forms[0] else "(sem form na context)"
        except Exception:
            err = "(sem context)"
        raise AssertionError(f"Produto não foi criado. Status={resp.status_code}. Form errors={err}")

    p = Product.objects.get(sku="SKU-FULL-001")
    assert p.name == "Produto Completo"
    assert p.price == Decimal("199.90")
    assert p.stock_qty == Decimal("15")

    rlist = client.get(list_url)
    assert rlist.status_code == 200
    html = rlist.content.decode("utf-8")
    assert "SKU-FULL-001" in html
    assert "Produto Completo" in html
