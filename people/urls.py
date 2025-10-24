# people/urls.py
from django.urls import path
from . import views

app_name = "people"

urlpatterns = [
    path("", views.ContactListView.as_view(), name="list"),
    path("novo/", views.ContactCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ContactDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.ContactUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.ContactDeleteView.as_view(), name="delete"),

    path("export.csv", views.export_contacts_csv, name="export_csv"),
    path("importar/", views.import_contacts_view, name="import"),
    path("import-template.csv", views.download_import_template, name="import_template"),

    # diagnóstico
    path("ping/", views.ping, name="ping"),
    path("index/", views.index, name="index"),
]
