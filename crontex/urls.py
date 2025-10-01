from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("crontex_ui.urls")),           # /entrar/ etc.
    path("", include(("catalog.urls", "catalog"), namespace="catalog")),
    path("", include("django.contrib.auth.urls")),  # /password_reset/ etc. (names: password_reset, _done, _confirm, _complete)
]