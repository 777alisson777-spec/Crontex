# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from io import TextIOWrapper
from typing import Dict, List, Any, Tuple, Iterable

from django.apps import apps
from django.core.files.uploadedfile import UploadedFile

from crontex.logger import dbg, info, warn

# Mapeamento de headers do Bling -> campos do model Product (tentativas em ordem)
BLING_HEADER_MAP = {
    "Código": ["sku", "codigo", "code"],
    "Descrição": ["name", "nome", "descricao", "description", "titulo"],

    "Unidade": ["unit", "unit_of_measure"],
    "Unidade de Medida": ["unit_of_measure", "unit"],

    "NCM": ["ncm"],
    "Origem": ["origin"],

    "Preço": ["price", "preco", "valor"],
    "Preço de custo": ["cost_price", "preco_custo", "custo"],
    "Preço de Compra": ["purchase_price"],

    "Observações": ["notes"],
    "Situação": ["status"],

    "Estoque": ["stock_qty", "stock", "estoque", "quantity", "qtd"],
    "Localização": ["location"],

    "GTIN/EAN": ["gtin"],
    "Marca": ["brand"],

    "Largura do produto": ["width_cm"],
    "Altura do Produto": ["height_cm"],
    "Profundidade do produto": ["length_cm"],

    "Peso líquido (Kg)": ["weight_net"],
    "Peso bruto (Kg)": ["weight_gross"],

    "Cód. no fornecedor": ["supplier_code"],
    "Fornecedor": ["supplier_name"],

    "Link Externo": ["external_link"],
    "Meses Garantia no Fornecedor": ["warranty_months_supplier"],

    # ICMS/CEST/etc.
    "CEST": ["cest"],
    "Valor base ICMS ST para retenção": ["icms_st_base_retencao"],
    "Valor ICMS ST para retenção": ["icms_st_valor_retencao"],
    "Valor ICMS próprio do substituto": ["icms_proprio_substituto"],

    "Departamento": ["department"],
    "Categoria do produto": ["product_category"],

    # Textos complementares
    "Informações Adicionais": ["extra_info"],
    "Descrição Complementar": ["extra_info"],

    # Variações (se usar grid como string/JSON)
    "Produto Variação": ["variations_grid"],
}

# Campos que devem sofrer conversão numérica
NUMERIC_FIELDS = {
    # preços/valores
    "price", "preco", "valor",
    "cost_price", "preco_custo", "custo",
    "purchase_price",

    # estoque / quantidades
    "stock_qty", "stock", "estoque", "quantity", "qtd",

    # dimensões / pesos
    "width_cm", "height_cm", "length_cm",
    "weight_net", "weight_gross",

    # fiscais / garantia
    "warranty_months_supplier",
    "icms_st_base_retencao", "icms_st_valor_retencao", "icms_proprio_substituto",
}


@dataclass
class ImportResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)
    samples: List[Dict[str, Any]] = field(default_factory=list)


def _decode_file(upload: UploadedFile) -> TextIOWrapper:
    """
    Retorna um wrapper texto com encoding tolerante.
    """
    try:
        upload.seek(0)
    except Exception:
        pass
    try:
        return TextIOWrapper(upload, encoding="utf-8-sig")
    except Exception:
        return TextIOWrapper(upload, encoding="latin-1")


def _to_number(val: str) -> Any:
    """
    Converte string em número, lidando com formato BR (1.234,56).
    """
    if val is None:
        return None
    s = str(val).strip()
    if s == "":
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s) if "." in s else int(s)
    except ValueError:
        return None


def _first_present_field(model, candidates: Iterable[str]) -> Tuple[str | None, bool]:
    for c in candidates:
        if hasattr(model, c):
            return c, True
    return None, False


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    clean = {}
    for k, v in row.items():
        kk = (k or "").strip()
        clean[kk] = v.strip() if isinstance(v, str) else v
    return clean


def import_bling_csv(upload: UploadedFile) -> ImportResult:
    """
    Importa CSV do Bling para o model catalog.Product.
    - Identifica produto por sku/codigo/code (na ordem que existir no model).
    - Cria ou atualiza produtos conforme payload.
    - Somente campos existentes no model são setados.
    """
    Product = apps.get_model("catalog", "Product")
    result = ImportResult()

    txt = _decode_file(upload)

    # Sniff de delimitador (preferindo ';')
    sample = txt.read(8192)
    txt.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
    except Exception:
        class _D:
            delimiter = ';'
        dialect = _D()

    reader = csv.DictReader(txt, dialect=dialect)
    if not reader.fieldnames:
        result.errors.append("CSV sem cabeçalho.")
        warn("csv-no-header")
        return result

    info("csv-headers", headers=reader.fieldnames)

    # Mapear colunas -> campos do Product
    field_map: Dict[str, str] = {}
    for header, targets in BLING_HEADER_MAP.items():
        if header in reader.fieldnames:
            field, ok = _first_present_field(Product, targets)
            if ok and field:
                field_map[header] = field
    dbg("field-map", field_map=field_map)

    # Descobrir campo identificador no model
    id_field = None
    if "Código" in field_map:
        id_field = field_map["Código"]
    else:
        for candidate in ("sku", "codigo", "code"):
            if hasattr(Product, candidate):
                id_field = candidate
                break
    if not id_field:
        result.errors.append("Não encontrei campo identificador no Product (esperado: sku/codigo/code).")
        warn("id-field-missing")
        return result

    # Iterar linhas
    for i, raw in enumerate(reader, start=2):  # linha 2 = primeira após o header
        if i == 2:
            dbg("first-row", sample={k: raw.get(k) for k in list(raw.keys())[:6]})

        row = _normalize_row(raw)
        payload: Dict[str, Any] = {}

        # Monta payload com conversões
        for header, model_field in field_map.items():
            val = row.get(header)
            if model_field in NUMERIC_FIELDS:
                num = _to_number(val)
                if num is not None:
                    payload[model_field] = num
            else:
                if val not in (None, ""):
                    payload[model_field] = val

        # Resolve identificador
        ident = (
            payload.get(id_field)
            or row.get("Código")
            or row.get("codigo")
            or row.get("Código do produto")
        )
        if ident in (None, ""):
            result.skipped += 1
            continue

        # defaults = payload sem o identificador
        defaults = payload.copy()
        defaults.pop(id_field, None)

        try:
            obj, created = Product.objects.get_or_create(**{id_field: ident}, defaults=defaults)
            if created:
                result.created += 1
            else:
                changed = []
                for k, v in defaults.items():
                    if hasattr(obj, k) and v not in (None, "") and getattr(obj, k) != v:
                        setattr(obj, k, v)
                        changed.append(k)
                if changed:
                    obj.save(update_fields=changed)
                    result.updated += 1
                else:
                    result.skipped += 1
        except Exception as e:
            result.errors.append(f"Linha {i}: {e}")
            warn("row-fail", line=i, error=str(e))
            continue

        if len(result.samples) < 3:
            sample_view = {k: payload.get(v) for k, v in field_map.items()}
            result.samples.append(sample_view)

    info("csv-result", created=result.created, updated=result.updated, skipped=result.skipped, errors=len(result.errors))
    return result
