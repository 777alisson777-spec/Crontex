from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.base import RedirectView

urlpatterns = [
    path("admin/login/", RedirectView.as_view(url="/entrar/?next=/admin/"), name="admin_login_redirect"),
    path("admin/", admin.site.urls),
    path("", include("crontex_ui.urls")),           # /entrar/ etc.
    path("", include(("catalog.urls", "catalog"), namespace="catalog")),
    path("", include("accounts.urls")),  # /global/* (dashboard global)
    path("", include("django.contrib.auth.urls")),  # /password_reset/ etc. (names: password_reset, _done, _confirm, _complete)
]