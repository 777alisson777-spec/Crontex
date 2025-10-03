# tests/test_produto_minimo.py
import pytest
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from catalog.models import Product

@pytest.mark.django_db
def test_criar_produto_minimo_via_form(client):
    u = User.objects.create_user("qa", password="x")
    u.user_permissions.add(Permission.objects.get(codename="add_product"))
    client.login(username="qa", password="x")

    url = reverse("catalog:produto_create")
    resp = client.post(url, {"sku": "SKU-TEST-1", "name": "Produto Teste"}, follow=True)

    assert resp.status_code == 200
    assert Product.objects.filter(sku="SKU-TEST-1").exists()
