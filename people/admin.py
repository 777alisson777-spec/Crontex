from django.contrib import admin
from .models import Collaborator, CollaboratorRole

@admin.register(CollaboratorRole)
class CollaboratorRoleAdmin(admin.ModelAdmin):
    list_display = ("label", "key", "is_active")
    list_filter = ("is_active",)
    search_fields = ("label", "key")

@admin.register(Collaborator)
class CollaboratorAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "email", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("name", "email")
