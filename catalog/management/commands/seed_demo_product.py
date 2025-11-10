from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps

class Command(BaseCommand):
    help = "Seed: cria 1 produto completo + 1 variante (idempotente)."

    def handle(self, *args, **options):
        Product = apps.get_model("catalog", "Product")
        Variant = apps.get_model("catalog", "ProductVariant")

        sku = "CRO-TEE-0001"
        with transaction.atomic():
            p, created = Product.objects.get_or_create(
                sku=sku,
                defaults=dict(
                    name="Camiseta Crontex Logo",
                    price=79.90,
                    stock_qty=25,
                    product_category="Camisetas",
                    bling_extra={
                        "abas": ["Pedido", "OS", "Bling", "Manufatura", "Material", "Grade", "Aviamentos"],
                        "source": "seed-demo",
                    },
                    variations_grid={
                        "colors": [{"name": "Preto", "code": "PR"}],
                        "sizes": [{"name": "S", "code": "S"}],
                        "schema": "color_size",
                    },
                ),
            )

            v, v_created = Variant.objects.get_or_create(
                product=p,
                sku=f"{sku}-S-PR",
                defaults=dict(
                    size_name="S",
                    size_code="S",
                    color_name="Preto",
                    color_code="PR",
                    ean13="",
                    stock_qty=p.stock_qty or 0,
                    price_override=p.price or 0,   # NOT NULL
                    desc_short="Camiseta S/Preto",
                    desc_medium="Camiseta Crontex logo, tamanho S, cor Preto.",
                    image_real_url="",
                ),
            )

        self.stdout.write(self.style.SUCCESS(
            f"OK - Product[{p.id}] {'created' if created else 'existing'} | "
            f"Variant[{v.id}] {'created' if v_created else 'existing'}"
        ))
