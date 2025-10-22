# -*- coding: utf-8 -*-
from __future__ import annotations

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q

from .models import Collaborator, CollaboratorRole

@require_GET
@login_required
def collaborator_search(request):
    """
    Autocomplete de colaboradores:
      GET /people/collaborators/search/?q=<texto>&role=<KEY OPCIONAL>
    Retorna: {"items":[{"id":..., "name":"...", "role_key":"...", "role_label":"..."}]}
    """
    q = (request.GET.get("q") or "").strip()
    role_key = (request.GET.get("role") or "").strip().upper()

    qs = Collaborator.objects.select_related("role").filter(is_active=True)
    if role_key:
        try:
            role = CollaboratorRole.objects.get(key=role_key, is_active=True)
            qs = qs.filter(role=role)
        except CollaboratorRole.DoesNotExist:
            return JsonResponse({"items": []})

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q))

    rows = [{
        "id": c.id,
        "name": c.name,
        "role_key": c.role.key,
        "role_label": c.role.label,
    } for c in qs.order_by("name")[:20]]

    return JsonResponse({"items": rows})


@require_POST
@login_required
@user_passes_test(lambda u: u.is_staff)
def collaborator_role_create(request):
    """
    Cria papel dinâmico (opcional):
      POST key=CHAVE_EM_SLUG  label=Nome do Papel
    """
    key = (request.POST.get("key") or "").strip().upper()
    label = (request.POST.get("label") or "").strip()
    if not key or not label:
        return HttpResponseBadRequest("key e label são obrigatórios.")
    role, _ = CollaboratorRole.objects.get_or_create(key=key, defaults={"label": label, "is_active": True})
    return JsonResponse({"id": role.id, "key": role.key, "label": role.label})
