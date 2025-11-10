# -*- coding: utf-8 -*-
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin: força login via /entrar/
    path("admin/login/", RedirectView.as_view(url="/entrar/?next=/admin/"), name="admin_login_redirect"),
    path("admin/", admin.site.urls),

    # Apps (UI -> people -> catalog)
    path("", include("crontex_ui.urls")),                 # /entrar/, /sair/, etc.
    path("people/", include("people.urls")),
    path("", include(("catalog.urls", "catalog"), namespace="catalog")),

    # Global + auth built-in
    path("", include("accounts.urls")),
    path("", include("django.contrib.auth.urls")),
]

# Dev-only: serve media local
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
