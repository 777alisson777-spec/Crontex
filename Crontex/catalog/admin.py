# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku", "name", "price", "stock_qty",
        "product_category", "ncm", "gtin",
        "is_active", "updated_at",
    )
    search_fields = (
        "sku", "name", "product_category",
        "ncm", "gtin", "brand", "supplier_code", "supplier_name",
    )
    list_filter = ("is_active", "product_category", "brand", "status")
    readonly_fields = ("created_at", "updated_at")
