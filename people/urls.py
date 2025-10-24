# people/urls.py
# Rotas públicas do app "people".
# Mantém as rotas já existentes e adiciona uma mini-API para autocomplete:
#   - /people/api/search/ : busca paginada por contato (q, page)
#   - /people/api/get/    : obtém contato por ID (hidratar valor inicial)
# Obs.: as views contact_search_api e contact_get_api serão adicionadas no próximo passo.

from django.urls import path
from . import views

app_name = "people"

urlpatterns = [
    # CRUD básico
    path("", views.ContactListView.as_view(), name="list"),
    path("novo/", views.ContactCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ContactDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.ContactUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.ContactDeleteView.as_view(), name="delete"),

    # Import/Export
    path("export.csv", views.export_contacts_csv, name="export_csv"),
    path("importar/", views.import_contacts_view, name="import"),
    path("import-template.csv", views.download_import_template, name="import_template"),

    # Diagnóstico / utilitários
    path("ping/", views.ping, name="ping"),
    path("index/", views.index, name="index"),

    # === API de Autocomplete (para integração com 'catalog') ===
    # Retorna JSON no formato:
    #   /people/api/search/?q=<termo>&page=1
    #   -> {"results":[{"id":1,"text":"Nome","subtitle":"email/phone"}], "pagination":{"more":false}}
    #   /people/api/get/?id=<pk>
    #   -> {"id":1,"text":"Nome","subtitle":"..."}
    path("api/search/", views.contact_search_api, name="api_search"),
    path("api/get/", views.contact_get_api, name="api_get"),
]
