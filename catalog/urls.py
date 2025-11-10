# -*- coding: utf-8 -*-
from django.urls import path
from catalog.views.web import (
    ProdutoListView,
    ProdutoCreateView,
    ProdutoDetailView,
    ProdutoUpdateView,
    ProdutoDeleteView,
    ProdutoImportView,
)
from catalog.views.ean_api import generate_ean_bulk
from catalog.views import web

app_name = "catalog"

urlpatterns = [
    path("produtos/", ProdutoListView.as_view(), name="produto_list"),
    path("produtos/novo/", ProdutoCreateView.as_view(), name="produto_create"),
    path("produtos/<int:pk>/", ProdutoDetailView.as_view(), name="produto_detail"),
    path("produtos/<int:pk>/editar/", ProdutoUpdateView.as_view(), name="produto_update"),
    path("produtos/<int:pk>/excluir/", ProdutoDeleteView.as_view(), name="produto_delete"),
    path("produtos/importar/", web.importar_produtos, name="produto_import"),

    # API utilitária
    path("catalog/api/ean/generate", generate_ean_bulk, name="ean_generate"),
]
