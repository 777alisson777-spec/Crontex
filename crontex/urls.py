# -*- coding: utf-8 -*-
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    # Admin com redirect custom para /entrar/ (sem duplicar names)
    path("admin/login/", RedirectView.as_view(url="/entrar/?next=/admin/"), name="admin_login_redirect"),
    path("admin/", admin.site.urls),

    # Apps do projeto (ordem: UI -> people -> catalog -> accounts -> auth)
    path("", include("crontex_ui.urls")),  # /entrar/, /sair/, etc. (front/autenticação custom)
    path("people/", include(("people.urls", "people"), namespace="people")),
    path("", include(("catalog.urls", "catalog"), namespace="catalog")),

    # Admin global e autenticação adicional
    path("", include("accounts.urls")),              # /global/* (dashboard global)
    path("", include("django.contrib.auth.urls")),   # /password_reset/ etc.
]
