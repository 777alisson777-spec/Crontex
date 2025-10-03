# -*- coding: utf-8 -*-
from django.urls import path
from .views import (
    ProdutoListView,
    ProdutoCreateView,
    ProdutoDetailView,
    ProdutoUpdateView,
    ProdutoDeleteView,
    ProdutoImportView,
)

app_name = "catalog"

urlpatterns = [
    path("produtos/", ProdutoListView.as_view(), name="produto_list"),
    path("produtos/novo/", ProdutoCreateView.as_view(), name="produto_create"),
    path("produtos/<int:pk>/", ProdutoDetailView.as_view(), name="produto_detail"),
    path("produtos/<int:pk>/editar/", ProdutoUpdateView.as_view(), name="produto_update"),
    path("produtos/<int:pk>/excluir/", ProdutoDeleteView.as_view(), name="produto_delete"),
    path("produtos/importar/", ProdutoImportView.as_view(), name="produto_import"),
]
