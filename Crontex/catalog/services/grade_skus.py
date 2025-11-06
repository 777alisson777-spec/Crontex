# -*- coding: utf-8 -*-
"""
Fail-safe de geração de SKUs (EAN-13) baseado na grade salva em bling_extra.grade.

Formato EAN-13 acordado:
[ref(4)][base(4)][tam(2)][cor(2)][dv(1)]

Regras:
- Os nomes dos parâmetros são livres. A posição define o papel:
  - 1º parâmetro => "tamanho" (gera cód 2d iniciando em 01)
  - 2º parâmetro => "cor"     (gera cód 2d iniciando em 01)
- Se só existir 1 parâmetro: cor assume "00".
- Se existir 3+ parâmetros: só os 2 primeiros entram no EAN. Os demais ainda
  compõem a grade, mas não alteram o EAN (padrão combinado).
- Valores são autonumerados por ordem de aparição (01, 02, 03…).

Saídas:
- Retorna lista de dicts com: {"combo": {chave: valor, ...}, "sku": "xxxxxxxxxxxxx"}
- Também devolve um dict resumo:
  {
    "ref": "0000", "base": "0000",
    "param_tamanho": "NomeDoParam1" ou "", "param_cor": "NomeDoParam2" ou "",
    "map_tamanho": {"P": "01", "M": "02", ...},
    "map_cor": {"Preto": "01", "Branco": "02", ...}
  }
"""

from __future__ import annotations
from typing import Dict, List, Any, Tuple


def _to_2d(n: int) -> str:
    if n <= 0:
        return "00"
    return f"{n:02d}"[-2:]


def ean13_check_digit12(code12: str) -> str:
    """Calcula dígito verificador para 12 dígitos (retorna 1 char)."""
    if len(code12) != 12 or not code12.isdigit():
        return "0"
    soma = 0
    # índices baseados em 0 da esquerda p/ direita:
    # posições ímpares (1,3,5,...) -> peso 3; pares -> peso 1 (convenção EAN)
    for i, ch in enumerate(code12):
        d = ord(ch) - 48
        peso = 3 if (i % 2 == 1) else 1
        soma += d * peso
    dv = (10 - (soma % 10)) % 10
    return str(dv)


def make_ean13(ref4: str, base4: str, cod_tam2: str, cod_cor2: str) -> str:
    ref4 = (ref4 or "").zfill(4)[-4:]
    base4 = (base4 or "").zfill(4)[-4:]
    cod_tam2 = (cod_tam2 or "00").zfill(2)[-2:]
    cod_cor2 = (cod_cor2 or "00").zfill(2)[-2:]
    base12 = f"{ref4}{base4}{cod_tam2}{cod_cor2}"
    dv = ean13_check_digit12(base12)
    return base12 + dv


def _cartesian(values_by_param: List[List[str]]) -> List[List[str]]:
    combos: List[List[str]] = [[]]
    for arr in values_by_param:
        tmp: List[List[str]] = []
        for prefix in combos:
            for v in (arr or ["—"]):
                tmp.append(prefix + [v])
        combos = tmp
    return combos


def generate_skus_from_grade(
    ref4: str,
    base4: str,
    grade: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Gera SKUs com fail-safe a partir de bling_extra.grade:
    grade = {
        "parametros": [
            {"chave": "tam", "valores": ["P", "M", "G"]},
            {"chave": "cor", "valores": ["Preto", "Branco"]},
            ...  # ignorados no EAN
        ]
    }
    """
    params = list(grade.get("parametros") or [])
    # Normaliza estrutura
    norm: List[Dict[str, Any]] = []
    for p in params:
        chave = str((p or {}).get("chave") or "").strip()
        vals = list((p or {}).get("valores") or [])
        norm.append({"chave": chave, "valores": [str(x).strip() for x in vals if str(x).strip()]})

    # Mapas (autonumeração) dos 2 primeiros parâmetros (tam/cor)
    param_tam = norm[0]["chave"] if len(norm) >= 1 else ""
    param_cor = norm[1]["chave"] if len(norm) >= 2 else ""

    map_tam: Dict[str, str] = {}
    map_cor: Dict[str, str] = {}

    if len(norm) >= 1:
        for idx, v in enumerate(norm[0]["valores"], start=1):
            map_tam[v] = _to_2d(idx)
    if len(norm) >= 2:
        for idx, v in enumerate(norm[1]["valores"], start=1):
            map_cor[v] = _to_2d(idx)

    # Monta combos completos (todos os parâmetros), mas EAN só usa tam/cor
    headers = [p["chave"] or f"param_{i+1}" for i, p in enumerate(norm)]
    values_by_param = [p["valores"] or ["—"] for p in norm] or [["Único"]]
    combos_rows = _cartesian(values_by_param)

    out_rows: List[Dict[str, Any]] = []
    for row in combos_rows:
        combo = {h: row[i] for i, h in enumerate(headers)}
        v_tam = row[0] if len(row) >= 1 else "Único"
        v_cor = row[1] if len(row) >= 2 else "—"

        cod_tam = map_tam.get(v_tam, "00") if map_tam else "00"
        cod_cor = map_cor.get(v_cor, "00") if map_cor else "00"

        sku = make_ean13(ref4, base4, cod_tam, cod_cor)
        out_rows.append({"combo": combo, "sku": sku})

    summary = {
        "ref": (ref4 or "").zfill(4)[-4:],
        "base": (base4 or "").zfill(4)[-4:],
        "param_tamanho": param_tam,
        "param_cor": param_cor,
        "map_tamanho": map_tam,
        "map_cor": map_cor,
    }
    return out_rows, summary


def validate_ean13(ean: str) -> bool:
    if not ean or len(ean) != 13 or not ean.isdigit():
        return False
    dv_calc = ean13_check_digit12(ean[:12])
    return ean[-1] == dv_calc
