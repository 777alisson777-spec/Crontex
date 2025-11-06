# -*- coding: utf-8 -*-
import re
from django.core.exceptions import ValidationError

def validate_ncm(value: str):
    """
    NCM deve ter exatamente 8 dígitos numéricos.
    """
    if not value:
        return
    v = str(value).strip()
    if not re.fullmatch(r"\d{8}", v):
        raise ValidationError("NCM deve ter 8 dígitos numéricos.")

def _gtin_checksum_ok(gtin_digits: str) -> bool:
    """
    Valida GTIN-8/12/13/14 pelo dígito verificador (módulo 10).
    """
    digits = [int(c) for c in gtin_digits if c.isdigit()]
    n = len(digits)
    if n not in (8, 12, 13, 14):
        return False
    base = digits[:-1]
    check = digits[-1]
    # Peso 3 e 1 alternados da direita para a esquerda
    s = 0
    weight = 3
    for d in reversed(base):
        s += d * weight
        weight = 1 if weight == 3 else 3
    dv = (10 - (s % 10)) % 10
    return dv == check

def validate_gtin(value: str):
    """
    Aceita GTIN-8/12/13/14 com ou sem máscara. Checa comprimento e dígito.
    """
    if not value:
        return
    v = re.sub(r"\D", "", str(value))
    if not _gtin_checksum_ok(v):
        raise ValidationError("GTIN/EAN inválido.")

def validate_nonnegative(value):
    """
    Não permite números negativos. Aceita None.
    """
    if value is None:
        return
    try:
        if float(value) < 0:
            raise ValidationError("Valor não pode ser negativo.")
    except (TypeError, ValueError):
        raise ValidationError("Valor numérico inválido.")
