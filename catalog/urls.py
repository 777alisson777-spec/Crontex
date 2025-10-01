# catalog/urls.py
from django.urls import path
from .views import (
    ProdutoListView, ProdutoCreateView, ProdutoUpdateView,
    ProdutoDeleteView, ProdutoDetailView
)

app_name = "catalog"  # ← obrigatório para usar namespace

urlpatterns = [
    path("produtos/", ProdutoListView.as_view(), name="produto_list"),
    path("produtos/novo/", ProdutoCreateView.as_view(), name="produto_create"),
    path("produtos/<int:pk>/", ProdutoDetailView.as_view(), name="produto_detail"),
    path("produtos/<int:pk>/editar/", ProdutoUpdateView.as_view(), name="produto_update"),
    path("produtos/<int:pk>/excluir/", ProdutoDeleteView.as_view(), name="produto_delete"),
]
