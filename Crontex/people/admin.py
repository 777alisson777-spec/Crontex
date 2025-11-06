# people/admin.py
from django.contrib import admin
from .models import Contact, Address, Category

class AddressInline(admin.TabularInline):
    model = Address
    extra = 0

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "person_kind", "email", "phone", "status", "created_at")
    list_filter = ("person_kind", "status", "is_cliente", "is_fornecedor", "is_colaborador", "is_parceiro", "categories")
    search_fields = ("name", "cnpj", "cpf", "email", "phone")
    inlines = [AddressInline]
    autocomplete_fields = ("categories",)
    list_per_page = 25
    fieldsets = (
        ("Identificação", {"fields": (
            "name", "fantasy_name", "person_kind",
            ("is_cliente","is_fornecedor","is_colaborador","is_parceiro"),
            "categories",
        )}),
        ("Documentos", {"fields": (("cpf","cnpj"), ("rg","ie","ie_isento"))}),
        ("Contato", {"fields": (("email","phone","phone_alt"),)}),
        ("Status", {"fields": ("status","notes","is_deleted")}),
        ("Auditoria", {"fields": (("created_at","updated_at"),), "classes": ("collapse",)}),
    )
    readonly_fields = ("created_at","updated_at")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
