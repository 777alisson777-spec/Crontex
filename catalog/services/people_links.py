# catalog/services/people_links.py
# -*- coding: utf-8 -*-
"""
Merge idempotente dos vínculos de PESSOAS do formulário de Produto
dentro do JSON `bling_extra`, sem pisar nas outras chaves (ex.: grade).

Estrutura gravada (exemplo):
bling_extra = {
  "grade": { ... },
  "people": {
    "pedido": {
      "requisitante_id": 123,
      "cliente_id": 456
    },
    "os": {
      "estilo_id": null,
      "arte_id": null,
      "modelagem_id": null,
      "pilotagem_id": null,
      "encaixe_id": null
    },
    "manufatura": {
      "corte_id": null,
      "costura_id": null,
      "estamparia_id": null,
      "bordado_id": null,
      "lavanderia_id": null,
      "acabamento_id": null
    }
  }
}

Somente os campos presentes em cleaned_data são considerados.
IDs vazios (None/"") limpam o valor anterior.
"""

from __future__ import annotations
from typing import Any, Dict, Optional


def _ensure_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


# Mapeamento: (section, json_key) -> nome do campo *_id no form.cleaned_data
PEOPLE_FIELDS = [
    ("pedido",     "requisitante_id", "pedido_requisitante_id"),
    ("pedido",     "cliente_id",      "pedido_cliente_id"),

    # Se você decidir validar/criar estes *_id depois, já ficará plug-and-play:
    ("os",         "estilo_id",       "os_estilo_id"),
    ("os",         "arte_id",         "os_arte_id"),
    ("os",         "modelagem_id",    "os_modelagem_id"),
    ("os",         "pilotagem_id",    "os_pilotagem_id"),
    ("os",         "encaixe_id",      "os_encaixe_id"),

    ("manufatura", "corte_id",        "m_corte_id"),
    ("manufatura", "costura_id",      "m_costura_id"),
    ("manufatura", "estamparia_id",   "m_estamparia_id"),
    ("manufatura", "bordado_id",      "m_bordado_id"),
    ("manufatura", "lavanderia_id",   "m_lavanderia_id"),
    ("manufatura", "acabamento_id",   "m_acabamento_id"),
]


def _norm_int_or_none(v: Any) -> Optional[int]:
    """
    Normaliza valores vindos do form:
    - None/"": retorna None
    - "123"/123: retorna int(123)
    - Qualquer outra coisa inválida: retorna None
    """
    if v is None:
        return None
    if v == "":
        return None
    try:
        i = int(v)
        return i if i > 0 else None
    except Exception:
        return None


def merge_people_links(product, cleaned_data: Dict[str, Any]) -> None:
    """
    Mescla os campos *_id de pessoas em product.bling_extra["people"].
    Não salva o model — responsabilidade do chamador (`product.save()`).

    Regras:
    - Apenas chaves presentes em cleaned_data são processadas.
    - Valores None limpam o que havia antes.
    - Não mexe em outras chaves do bling_extra (merge profundo/limitado).
    """
    extra = _ensure_dict(getattr(product, "bling_extra", {}))
    people = _ensure_dict(extra.get("people"))

    # Garante as seções de primeiro nível
    for section in ("pedido", "os", "manufatura"):
        people.setdefault(section, {})

    # Aplica cada campo se existir no cleaned_data
    for section, key_json, field_name in PEOPLE_FIELDS:
        if field_name not in cleaned_data:
            # se o form ainda não expõe esse *_id, ignore silenciosamente
            continue
        val = _norm_int_or_none(cleaned_data.get(field_name))
        # set/clear no dicionário
        people[section][key_json] = val

    extra["people"] = people
    product.bling_extra = extra
