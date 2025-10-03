# -*- coding: utf-8 -*-
"""
Seeder DEV completo (todas as abas).
Uso (CMD):
  set DJANGO_SETTINGS_MODULE=crontex.settings
  python -m tests.seeders.seed_dev_product --sku SKU-DEV-UI-ALL --name "Produto Completo DEV (ALL)"
"""
from __future__ import annotations
import argparse
import os
import json
from decimal import Decimal

# garante settings do Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crontex.settings")

import django  # noqa: E402
django.setup()

from catalog.models import Product  # noqa: E402


def payload_extras() -> dict:
    """Campos das abas NÃO-model, empacotados em bling_extra (JSON)."""
    return {
        "pedido": {
            "requisitante": "Alli",
            "cliente": "Cliente Z",
            "status": "em_planejamento",
            "extras": [{"key": "prazo", "val": "15 dias"}],
        },
        "os": {
            "estilo": "Street",
            "arte": "Logo minimal",
            "modelagem": "T-shirt oversize",
            "pilotagem": "Ok",
            "encaixe": "Automático v2",
            "extras": [{"key": "observacao", "val": "usar gabarito X"}],
        },
        "manufatura": {
            "corte": "Laser",
            "costura": "Linha 120 Tex",
            "estamparia": "DTF",
            "bordado": "3D",
            "lavanderia": "Stone light",
            "acabamento": "Rebite + passante",
            "extras": [{"key": "turno", "val": "noturno"}],
        },
        "material": {
            "tecidos": [
                {"tecido": "Algodão 30/1", "obs": "pré-encolhido"},
                {"tecido": "Viscose", "obs": "5% elastano"},
            ]
        },
        "grade": {
            "cabecalho": ["P", "M", "G", "GG"],
            "linhas": [
                {"cor": "Preto", "vals": [10, 10, 10, 11]},
                {"cor": "Branco", "vals": [11, 20, 2, 10]},
            ],
        },
        "aviamentos_oficina": {
            "itens": [
                {"item": "Linha 120 Tex", "qtd_obs": "10 cones"},
                {"item": "Agulha 14", "qtd_obs": "1 caixa"},
            ]
        },
        "aviamentos_acabamento": {
            "sacola": "Plástica 30x40",
            "tag": "Cartão 300g com cordão",
            "extras": [{"item": "Etiqueta borracha", "qtd_obs": "100 un"}],
        },
    }


def run(sku: str, name: str) -> None:
    extras = payload_extras()
    obj, created = Product.objects.get_or_create(
        sku=sku,
        defaults=dict(
            # ===== BLING (model) =====
            name=name,
            unit="UN",
            ncm="61091000",
            origin="",
            price=Decimal("199.90"),
            ipi_fixed=Decimal("0.00"),
            notes="Seed DEV completo para validar todas as abas.",
            status="active",
            stock_qty=Decimal("15"),
            cost_price=Decimal("120.00"),
            supplier_code="FOR-001",
            supplier_name="Fornecedor X",
            location="A1-03",
            bling_extra=json.dumps(extras, ensure_ascii=False),
            external_link="https://exemplo.com/p/SKU-DEV-UI-ALL",
            warranty_months_supplier=0,
            clone_from_parent=False,         # BooleanField ✅
            product_condition="new",
            free_shipping=False,             # BooleanField ✅
            fci_number="",
            video_url="",
            department="Vestuário",
            unit_of_measure="UN",
            purchase_price=Decimal("110.00"),
            icms_st_base_retencao=Decimal("0.00"),
            icms_st_valor_retencao=Decimal("0.00"),
            icms_proprio_substituto=Decimal("0.00"),
            product_category="Camisetas",
            extra_info="",
            cest="1234567",
            gtin="7891234567895",           # EAN-13 válido
            brand="Crontex",
            width_cm=Decimal("30.00"),
            height_cm=Decimal("2.00"),
            length_cm=Decimal("40.00"),
            weight_net=Decimal("0.200"),
            weight_gross=Decimal("0.250"),
            is_active=True,
        ),
    )
    print(("OK criado: " if created else "JA EXISTE: ") + f"{obj.sku} - {obj.name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sku", default="SKU-DEV-UI-4")
    ap.add_argument("--name", default="Produto Completo DEV (ALL)")
    args = ap.parse_args()
    run(args.sku, args.name)
