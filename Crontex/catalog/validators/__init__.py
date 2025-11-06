# -*- coding: utf-8 -*-
"""
Pacote validators compatível com imports antigos:
from catalog.validators import validate_gtin, validate_ncm, validate_nonnegative
E expõe também validate_ean13.
"""

import re
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# ====== legacy validators (mantidos aqui para evitar .base) ======

_GTIN_RE = re.compile(r"^\d{8}$|^\d{12}$|^\d{13}$|^\d{14}$")
_ONLY_DIGITS = re.compile(r"\D+")

def _check_digit_mod10(body: str) -> int:
    """
    Calcula DV para GTIN/EAN (mod-10 Luhn-like GS1).
    body: string numérica SEM o dígito final.
    """
    s = _ONLY_DIGITS.sub("", body)
    total = 0
    # pesos 3 e 1 alternados da direita para a esquerda (padrão GS1)
    for i, ch in enumerate(reversed(s), start=1):
        d = ord(ch) - 48
        weight = 3 if (i % 2 == 1) else 1
        total += d * weight
    return (10 - (total % 10)) % 10

def validate_gtin(value):
    """
    Aceita GTIN-8/12/13/14 com DV correto.
    """
    s = _ONLY_DIGITS.sub("", str(value) if value is not None else "")
    if not _GTIN_RE.match(s):
        raise ValidationError(_("GTIN deve ter 8, 12, 13 ou 14 dígitos."))
    body, dv = s[:-1], int(s[-1])
    exp = _check_digit_mod10(body)
    if dv != exp:
        raise ValidationError(_("Dígito verificador inválido para GTIN."))

def validate_ncm(value):
    """
    NCM: exatamente 8 dígitos.
    """
    s = _ONLY_DIGITS.sub("", str(value) if value is not None else "")
    if len(s) != 8:
        raise ValidationError(_("NCM deve ter 8 dígitos numéricos."))

def validate_nonnegative(value):
    """
    Número >= 0.
    """
    try:
        v = Decimal(value)
    except Exception:
        raise ValidationError(_("Valor numérico inválido."))
    if v < 0:
        raise ValidationError(_("Valor não pode ser negativo."))

# ====== EAN-13 específico ======
from .ean import validate_ean13  # noqa: E402,F401
