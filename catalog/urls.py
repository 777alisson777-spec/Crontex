# -*- coding: utf-8 -*-
from django.urls import path
from django.views.generic import DetailView
from .models import Product
from .views import (
    ProductListView as ProdutoListView,
    ProductCreateView as ProdutoCreateView,
    ProductUpdateView as ProdutoUpdateView,
    ProductDeleteView as ProdutoDeleteView,
    ProductImportView as ProdutoImportView,
)

app_name = "catalog"

urlpatterns = [
    path("produtos/", ProdutoListView.as_view(), name="produto_list"),
    path("produtos/novo/", ProdutoCreateView.as_view(), name="produto_create"),
    path(
        "produtos/<int:pk>/",
        DetailView.as_view(model=Product, template_name="catalog/produto_detail.html"),
        name="produto_detail",
    ),
    path("produtos/<int:pk>/editar/", ProdutoUpdateView.as_view(), name="produto_update"),
    path("produtos/<int:pk>/excluir/", ProdutoDeleteView.as_view(), name="produto_delete"),
    path("produtos/importar/", ProdutoImportView.as_view(), name="produto_import"),
]
