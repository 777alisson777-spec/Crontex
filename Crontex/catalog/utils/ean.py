# -*- coding: utf-8 -*-
"""
Utilitários para geração e validação de EAN-13 no backend.

Padrão interno:
[refer(4d)][base(4d)][tam(2d)][cor(2d)] + dígito verificador

APIs expostas:
- normalize_n_digits(value, n) -> str
- ean12_compose(refer4, base4, tam2, cor2) -> str
- ean13_check_digit(ean12) -> int
- ean13_compose(refer4, base4, tam2, cor2) -> str
- parse_code_map(text) -> dict[str, str]
- validate_unique_eans(eans, exists_callable) -> list[str]
"""

import re
from typing import Callable, Dict, Iterable, List


_DIGIT_RE = re.compile(r"\D+")


def normalize_n_digits(value: str | int | None, n: int) -> str:
    """
    Mantém apenas dígitos, corta em n e faz zero-left-pad até n.
    Lança ValueError se exceder n após limpar.
    """
    s = "" if value is None else str(value)
    s = _DIGIT_RE.sub("", s)
    if len(s) > n:
        raise ValueError(f"valor com mais de {n} dígitos: {s!r}")
    return s.zfill(n)


def ean12_compose(refer4: str | int, base4: str | int, tam2: str | int, cor2: str | int) -> str:
    """
    Monta os 12 dígitos base: 4 + 4 + 2 + 2. Todos saneados.
    """
    r = normalize_n_digits(refer4, 4)
    b = normalize_n_digits(base4, 4)
    t = normalize_n_digits(tam2, 2)
    c = normalize_n_digits(cor2, 2)
    return f"{r}{b}{t}{c}"  # 12 dígitos


def ean13_check_digit(ean12: str | int) -> int:
    """
    Calcula o dígito verificador do EAN-13 dado os 12 dígitos base.
    Regra GS1: soma ímpares + 3*soma pares (posições 1..12), dv = (10 - (total % 10)) % 10.
    """
    s = normalize_n_digits(ean12, 12)
    # posições humanas 1..12
    odd = 0
    even = 0
    for i, ch in enumerate(s, start=1):
        d = ord(ch) - 48  # int rápido
        if i % 2 == 0:
            even += d
        else:
            odd += d
    total = odd + 3 * even
    return (10 - (total % 10)) % 10


def ean13_compose(refer4: str | int, base4: str | int, tam2: str | int, cor2: str | int) -> str:
    """
    Retorna o EAN-13 final: ean12 + dv.
    """
    e12 = ean12_compose(refer4, base4, tam2, cor2)
    dv = ean13_check_digit(e12)
    return f"{e12}{dv}"


def parse_code_map(text: str | None) -> Dict[str, str]:
    """
    Converte linhas em um mapa de nome->código 2 dígitos.
    Aceita formatos por linha: "Nome=NN", "Nome:NN" ou "Nome NN".
    Ignora linhas vazias.
    """
    if not text:
        return {}
    out: Dict[str, str] = {}
    for raw in re.split(r"[\r\n,;]+", text):
        t = raw.strip()
        if not t:
            continue
        parts = re.split(r"[:=\s]+", t)
        if len(parts) < 2:
            continue
        name = " ".join(parts[:-1]).strip().lower()
        code = normalize_n_digits(parts[-1], 2)
        if name:
            out[name] = code
    return out


def validate_unique_eans(
    eans: Iterable[str],
    exists_callable: Callable[[str], bool],
) -> List[str]:
    """
    Checa duplicidade. Retorna lista de EANs que já existem no banco segundo exists_callable.
    - exists_callable: função que recebe ean13 (str) e retorna True se já existir.
    """
    seen_db: List[str] = []
    seen_mem: set[str] = set()
    for e in eans:
        if not e:
            continue
        if e in seen_mem:
            # duplicidade dentro do próprio lote
            if e not in seen_db:
                seen_db.append(e)
            continue
        seen_mem.add(e)
        try:
            if exists_callable(e):
                seen_db.append(e)
        except Exception:
            # Fallback defensivo: não derruba a validação por erro externo
            pass
    return seen_db
