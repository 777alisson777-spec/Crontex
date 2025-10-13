# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Any, Dict, List

from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt  # troque para ensure_csrf_cookie se preferir
from django.utils.encoding import force_str

from catalog.utils.ean import (
    parse_code_map,
    ean13_compose,
    normalize_n_digits,
)


def _json_body(request: HttpRequest) -> Dict[str, Any]:
    try:
        body = request.body.decode(request.encoding or "utf-8")
        return json.loads(body or "{}")
    except Exception:
        return {}


@csrf_exempt  # se usar CSRF, remova e envie o token pelo header X-CSRFToken
@require_POST
def generate_ean_bulk(request: HttpRequest):
    """
    POST /catalog/api/ean/generate
    Content-Type: application/json
    {
      "referencia": "1234",
      "base": "0456",
      "map_size": "PP=01\nP=02\nM=03\nG=04\nGG=05",
      "map_color": "Preto=01\nBranco=02",
      "sizes": ["PP","P","M"],
      "colors": ["Preto","Branco"]
    }
    -> { "items": [ {tamName, corName, ean13, dv}, ... ] }
    """
    data = _json_body(request)

    ref = normalize_n_digits(force_str(data.get("referencia", "")), 4)
    base = normalize_n_digits(force_str(data.get("base", "")), 4)
    if len(ref) != 4 or len(base) != 4:
        return HttpResponseBadRequest("referencia/base precisam ter 4 dígitos")

    size_map = parse_code_map(force_str(data.get("map_size", "")))
    color_map = parse_code_map(force_str(data.get("map_color", "")))

    sizes = data.get("sizes") or []
    colors = data.get("colors") or []

    if not isinstance(sizes, list) or not isinstance(colors, list):
        return HttpResponseBadRequest("sizes/colors devem ser lista")

    items: List[Dict[str, Any]] = []
    for tam_name in sizes:
        tn = force_str(tam_name).strip()
        tt = size_map.get(tn.lower())
        if not tt:
            items.append({"tamName": tn, "corName": "—", "ean13": None, "dv": None})
            continue
        for cor_name in colors:
            cn = force_str(cor_name).strip()
            cc = color_map.get(cn.lower())
            if not cc:
                items.append({"tamName": tn, "corName": cn, "ean13": None, "dv": None})
                continue
            e13 = ean13_compose(ref, base, tt, cc)
            items.append({
                "tamName": tn,
                "corName": cn,
                "ean13": e13,
                "dv": int(e13[-1]),
            })

    return JsonResponse({"items": items})
