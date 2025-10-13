# -*- coding: utf-8 -*-
from __future__ import annotations

from django import template

register = template.Library()


@register.filter(name="get_item")
def get_item(mapping, key):
    """
    Acessa mapping[key] com fallback seguro.
    Uso no template: {{ row.attrs|get_item:p.chave|default:"—" }}
    """
    try:
        if isinstance(mapping, dict):
            return mapping.get(key, "")
        # Ex.: JSONField vindo como None ou outro tipo
        return ""
    except Exception:
        return ""


@register.filter(name="get_nested")
def get_nested(mapping, dotted_path: str):
    """
    Acessa chaves aninhadas por 'a.b.c'. Ex.: {{ obj|get_nested:"bling_extra.grade.parametros" }}
    Mantém fallback silencioso em caso de buracos.
    """
    try:
        if not isinstance(mapping, dict):
            return ""
        cur = mapping
        for part in str(dotted_path).split("."):
            if not isinstance(cur, dict):
                return ""
            cur = cur.get(part, "")
        return cur
    except Exception:
        return ""
