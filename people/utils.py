# people/utils.py
from __future__ import annotations

import re
from typing import Optional

_ONLY_DIGITS_RE = re.compile(r"\D+")

def only_digits(s: Optional[str]) -> str:
    return "" if not s else _ONLY_DIGITS_RE.sub("", s)

def normalize_cpf(s: Optional[str]) -> str:
    return only_digits(s)[:11]  # MVP: só tira máscara/limita

def normalize_cnpj(s: Optional[str]) -> str:
    return only_digits(s)[:14]

def normalize_cep(s: Optional[str]) -> str:
    return only_digits(s)[:8]

def normalize_phone(s: Optional[str]) -> str:
    # MVP: tira não-dígitos e mantém até 13 (ex: 55 + DDD + 9 + 8)
    return only_digits(s)[:13]

def normalize_uf(s: Optional[str]) -> str:
    return "" if not s else s.strip().upper()[:2]
