# -*- coding: utf-8 -*-
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from catalog.validators import validate_gtin, validate_ncm, validate_nonnegative
from catalog.validators.ean import validate_ean13

class Product(models.Model):
    # Bling básicos
    external_id = models.CharField("ID", max_length=50, blank=True, db_index=True)  # 01
    sku = models.CharField("Código", max_length=64, unique=True, db_index=True)     # 02
    name = models.CharField("Descrição", max_length=255)                             # 03
    unit = models.CharField("Unidade", max_length=10, blank=True)                    # 04
    ncm = models.CharField("NCM", max_length=8, blank=True, validators=[validate_ncm])  # 05
    origin = models.CharField("Origem", max_length=50, blank=True)                   # 06

    price = models.DecimalField("Preço", max_digits=12, decimal_places=2, default=Decimal("0"), blank=True, validators=[validate_nonnegative])  # 07
    ipi_fixed = models.DecimalField("Valor IPI fixo", max_digits=12, decimal_places=2, default=Decimal("0"), blank=True, validators=[validate_nonnegative])  # 08
    notes = models.TextField("Observações", blank=True)                              # 09
    status = models.CharField("Situação", max_length=30, blank=True)                 # 10
    stock_qty = models.DecimalField("Estoque", max_digits=12, decimal_places=3, default=Decimal("0"), blank=True, validators=[validate_nonnegative])  # 11
    cost_price = models.DecimalField("Preço de custo", max_digits=12, decimal_places=2, default=Decimal("0"), blank=True, validators=[validate_nonnegative])  # 12
    supplier_code = models.CharField("Cód no fornecedor", max_length=100, blank=True)  # 13
    supplier_name = models.CharField("Fornecedor", max_length=150, blank=True)         # 14
    location = models.CharField("Localização", max_length=150, blank=True)             # 15

    # Colunas 16–45 preservadas em JSON até promoção para campos dedicados
    bling_extra = models.JSONField("Extras Bling (colunas 16–45)", default=dict, blank=True)

    # Colunas finais (45–59)
    external_link = models.URLField("Link Externo", max_length=500, blank=True)      # 45
    warranty_months_supplier = models.IntegerField("Meses Garantia no Fornecedor", default=0, blank=True)  # 46
    clone_from_parent = models.BooleanField("Clonar dados do pai", default=False)     # 47
    product_condition = models.CharField("Condição do produto", max_length=30, blank=True)  # 48
    free_shipping = models.BooleanField("Frete Grátis", default=False)               # 49
    fci_number = models.CharField("Número FCI", max_length=36, blank=True)           # 50
    video_url = models.URLField("Vídeo", max_length=500, blank=True)                 # 51
    department = models.CharField("Departamento", max_length=100, blank=True)        # 52
    unit_of_measure = models.CharField("Unidade de medida", max_length=20, blank=True)  # 53
    purchase_price = models.DecimalField("Preço de compra", max_digits=12, decimal_places=2, default=Decimal("0"), blank=True, validators=[validate_nonnegative])  # 54
    icms_st_base_retencao = models.DecimalField("Valor base ICMS ST p/ retenção", max_digits=14, decimal_places=2, default=Decimal("0"), blank=True, validators=[validate_nonnegative])  # 55
    icms_st_valor_retencao = models.DecimalField("Valor ICMS ST p/ retenção", max_digits=14, decimal_places=2, default=Decimal("0"), blank=True, validators=[validate_nonnegative])      # 56
    icms_proprio_substituto = models.DecimalField("Valor ICMS próprio do substituto", max_digits=14, decimal_places=2, default=Decimal("0"), blank=True, validators=[validate_nonnegative])  # 57
    product_category = models.CharField("Categoria do produto", max_length=150, blank=True)  # 58
    extra_info = models.TextField("Informações Adicionais", blank=True)              # 59

    #grid
    variations_grid = models.JSONField(default=dict, blank=True)  # {"rows":[{"name":"Cor","values":["Azul","Verde"]}]}
    
    # Campos catálogo adicionais
    cest = models.CharField("CEST", max_length=7, blank=True)
    gtin = models.CharField("GTIN/EAN", max_length=14, blank=True, validators=[validate_gtin])
    brand = models.CharField("Marca", max_length=100, blank=True)
    width_cm = models.DecimalField("Largura (cm)", max_digits=10, decimal_places=2, default=Decimal("0"), blank=True, validators=[validate_nonnegative])
    height_cm = models.DecimalField("Altura (cm)", max_digits=10, decimal_places=2, default=Decimal("0"), blank=True, validators=[validate_nonnegative])
    length_cm = models.DecimalField("Profundidade (cm)", max_digits=10, decimal_places=2, default=Decimal("0"), blank=True, validators=[validate_nonnegative])
    weight_net = models.DecimalField("Peso líquido (kg)", max_digits=10, decimal_places=3, default=Decimal("0"), blank=True, validators=[validate_nonnegative])
    weight_gross = models.DecimalField("Peso bruto (kg)", max_digits=10, decimal_places=3, default=Decimal("0"), blank=True, validators=[validate_nonnegative])
    is_active = models.BooleanField("Ativo", default=True)

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["ncm"]),
            models.Index(fields=["gtin"]),
            models.Index(fields=["product_category"]),
        ]
        ordering = ["sku"]
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        return f"{self.sku} - {self.name}"
    
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)

    # nomes livres para UX
    size_name = models.CharField("Tamanho (nome)", max_length=50, blank=True)
    color_name = models.CharField("Cor (nome)", max_length=50, blank=True)

    # códigos normalizados de 2 dígitos (para compor EAN)
    size_code = models.CharField("Tamanho (código 2d)", max_length=2, blank=True)
    color_code = models.CharField("Cor (código 2d)", max_length=2, blank=True)

    # identificação
    sku = models.CharField("SKU variante", max_length=80, blank=True, unique=True)
    ean13 = models.CharField("EAN-13", max_length=13, blank=True, unique=True, validators=[validate_ean13])

    # dados opcionais da variante
    stock_qty = models.DecimalField("Estoque", max_digits=12, decimal_places=3, default=Decimal("0"), blank=True, validators=[validate_nonnegative])
    price_override = models.DecimalField("Preço override", max_digits=12, decimal_places=2, default=Decimal("0"), blank=True, validators=[validate_nonnegative])

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    # ao final dos campos já existentes
    image_real_url   = models.CharField(max_length=500, blank=True, null=True)  # ex: /media/mockups/sku_realista.jpg
    desc_short       = models.CharField(max_length=240, blank=True, null=True)
    desc_medium      = models.TextField(blank=True, null=True)


    class Meta:
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["ean13"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["product", "size_name", "color_name"], name="uniq_variant_by_names_per_product"),
        ]
        verbose_name = "Variante de produto"
        verbose_name_plural = "Variantes de produto"

    def __str__(self):
        prod = getattr(self, "product", None)
        base = getattr(prod, "sku", "—")
        tag = "/".join([s for s in [self.size_name, self.color_name] if s]) or "variante"
        return f"{base} · {tag}"
