# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import Callable, Iterable, List

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

_DIGIT_RE = re.compile(r"\D+")


def normalize_n_digits(value: str | int | None, n: int) -> str:
    s = "" if value is None else str(value)
    s = _DIGIT_RE.sub("", s)
    if len(s) > n:
        raise ValidationError(_(f"Valor excede {n} dígitos."))
    return s.zfill(n)


def ean13_check_digit(ean12: str | int) -> int:
    s = normalize_n_digits(ean12, 12)
    odd = 0
    even = 0
    for i, ch in enumerate(s, start=1):
        d = ord(ch) - 48
        if i % 2 == 0:
            even += d
        else:
            odd += d
    total = odd + 3 * even
    return (10 - (total % 10)) % 10


def validate_ean13(value: str | int) -> None:
    """
    Valida EAN-13: 13 dígitos numéricos e DV correto.
    Levanta ValidationError em caso de erro.
    """
    s = normalize_n_digits(value, 13)
    if len(s) != 13:
        raise ValidationError(_("EAN-13 deve ter 13 dígitos."))
    base12 = s[:12]
    dv = int(s[12])
    exp = ean13_check_digit(base12)
    if dv != exp:
        raise ValidationError(_("Dígito verificador inválido para EAN-13."))


def validate_unique_eans(
    eans: Iterable[str],
    exists_callable: Callable[[str], bool],
) -> List[str]:
    """
    Retorna a lista de EANs duplicados detectados.
    - Duplicados no próprio lote.
    - Já existentes conforme exists_callable(ean13) -> bool.
    Use em forms/clean() ou no save() antes de persistir variantes.
    """
    dupes: List[str] = []
    seen: set[str] = set()
    for raw in eans:
        if not raw:
            continue
        s = normalize_n_digits(raw, 13)
        if len(s) != 13:
            # formato inválido não entra como duplicado, será pego por validate_ean13
            continue
        if s in seen:
            if s not in dupes:
                dupes.append(s)
            continue
        seen.add(s)
        try:
            if exists_callable(s):
                dupes.append(s)
        except Exception:
            # Não derruba a validação por erro de IO
            pass
    return dupes
