import json
import pytest
from django.db import transaction
from django.apps import apps


def _get_model(app_label, model_name):
    try:
        return apps.get_model(app_label, model_name)
    except Exception:
        return None


@pytest.fixture
def seed_product_full(db):
    """
    Cria 1 produto completo aderente ao schema Crontex_IA:
      - Product (sku, name, price, stock_qty, product_category=char, bling_extra JSON, variations_grid JSON)
      - ProductVariant (S/Preto) com fields: size_name, color_name, size_code, color_code, sku, ean13, stock_qty, price_override
    Idempotente pelo SKU.
    """
    Product = _get_model("catalog", "Product")
    Variant = _get_model("catalog", "ProductVariant")
    assert Product is not None, "catalog.Product não encontrado"
    assert Variant is not None, "catalog.ProductVariant não encontrado"

    sku = "CRO-TEE-0001"
    product = Product.objects.filter(sku=sku).first()
    if product:
        return product

    with transaction.atomic():
        # Product base
        product = Product.objects.create(
            sku=sku,
            name="Camiseta Crontex Logo",
            price=79.90,
            stock_qty=25,
            product_category="Camisetas",
            bling_extra={
                "abas": ["Pedido", "OS", "Bling", "Manufatura", "Material", "Grade", "Aviamentos"],
                "source": "test-seeder",
            },
            # fallback seguro: JSON mínimo de variações
            variations_grid={
                "colors": [{"name": "Preto", "code": "PR"}],
                "sizes": [{"name": "S", "code": "S"}],
                "schema": "color_size",
            },
        )

        # Variant S/Preto
        Variant.objects.get_or_create(
            product=product,
            sku=f"{sku}-S-PR",
            defaults={
                "size_name": "S",
                "size_code": "S",
                "color_name": "Preto",
                "color_code": "PR",
                "ean13": "",
                "stock_qty": product.stock_qty or 0,
                "price_override": product.price or 0,   
                "desc_short": "Camiseta S/Preto",
                "desc_medium": "Camiseta Crontex logo, tamanho S, cor Preto.",
                "image_real_url": "",
            },
        )

        return product
