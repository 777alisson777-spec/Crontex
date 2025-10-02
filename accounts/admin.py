# accounts/admin.py
from django.contrib import admin
from .models import Account, Membership, GlobalUserRole, ServiceToken
from django.contrib import admin

admin.site.site_header = "CRONTEX · Admin"
admin.site.site_title = "CRONTEX"
admin.site.index_title = "Painel Administrativo"

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "plan", "is_active", "created_at")
    list_filter = ("is_active", "plan")
    search_fields = ("name", "slug")
    ordering = ("-created_at",)

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "account", "role", "created_at")
    list_filter = ("role", "account")
    search_fields = ("user__email", "user__username", "account__name", "account__slug")
    autocomplete_fields = ("user", "account")
    ordering = ("-created_at",)

@admin.register(GlobalUserRole)
class GlobalUserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ("user",)
    ordering = ("-created_at",)

@admin.register(ServiceToken)
class ServiceTokenAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "last_used_at")
    list_filter = ("is_active",)
    search_fields = ("name", "key")
    readonly_fields = ("created_at", "last_used_at")
    ordering = ("-created_at",)
