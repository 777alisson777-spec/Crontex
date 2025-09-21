from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("crontex_ui.urls", "crontex_ui"), namespace="crontex_ui")),
]