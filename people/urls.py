from django.urls import path
from .views import collaborator_search, collaborator_role_create

app_name = "people"

urlpatterns = [
    path("collaborators/search/", collaborator_search, name="collaborator_search"),
    path("collaborators/roles/create/", collaborator_role_create, name="collaborator_role_create"),
]
