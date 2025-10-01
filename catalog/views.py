# catalog/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Produto
from .forms import ProdutoForm

class ProdutoListView(LoginRequiredMixin, ListView):
    template_name = "catalog/produto_list.html"
    model = Produto
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status")
        if q:
            qs = qs.filter(Q(nome__icontains=q) | Q(sku__icontains=q))
        if status in {"ativos", "inativos"}:
            qs = qs.filter(ativo=(status == "ativos"))
        return qs

class ProdutoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "catalog.add_produto"
    template_name = "catalog/produto_form.html"
    form_class = ProdutoForm
    success_url = reverse_lazy("catalog:produto_list")

class ProdutoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "catalog.change_produto"
    template_name = "catalog/produto_form.html"
    form_class = ProdutoForm
    model = Produto
    success_url = reverse_lazy("catalog:produto_list")

class ProdutoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "catalog.delete_produto"
    template_name = "catalog/produto_confirm_delete.html"
    model = Produto
    success_url = reverse_lazy("catalog:produto_list")

class ProdutoDetailView(LoginRequiredMixin, DetailView):
    template_name = "catalog/produto_detail.html"
    model = Produto
