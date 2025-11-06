# -*- coding: utf-8 -*-
import pytest
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from catalog.models import Product


@pytest.mark.django_db
def test_fluxo_criar_e_ver_no_lista(client):
    # user com permissões mínimas
    u = User.objects.create_user("qa_list", password="x")
    u.user_permissions.add(Permission.objects.get(codename="add_product"))
    u.user_permissions.add(Permission.objects.get(codename="view_product"))
    client.login(username="qa_list", password="x")

    create_url = reverse("catalog:produto_create")
    list_url = reverse("catalog:produto_list")

    payload = {
        "sku": "SKU-LIST-001",
        "name": "Produto Para Lista",
        "price": "29.90",
        "stock_qty": "3",
        "form_uid": "uid-list-1",
    }

    # cria
    resp = client.post(create_url, payload, follow=True)
    assert resp.status_code == 200
    assert Product.objects.filter(sku="SKU-LIST-001").exists()

    # abre lista e valida presença
    resp_list = client.get(list_url)
    assert resp_list.status_code == 200
    html = resp_list.content.decode("utf-8")
    assert "SKU-LIST-001" in html
    assert "Produto Para Lista" in html

    # sanity dos valores salvos
    p = Product.objects.get(sku="SKU-LIST-001")
    assert p.price == Decimal("29.90")
    assert p.stock_qty == Decimal("3")
