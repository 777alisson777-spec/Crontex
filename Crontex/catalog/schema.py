# -*- coding: utf-8 -*-
"""
Esquema de mapeamento da planilha Bling -> Product.
Regra:
- Headers conhecidos mapeiam 1:1 para campos do model.
- Headers desconhecidos (ex.: colunas 16–45) vão para bling_extra.
- REQUIRED_HEADERS: linha deve conter ao menos Código e Descrição.
"""

from dataclasses import dataclass
from typing import Optional, Callable

@dataclass(frozen=True)
class FieldSpec:
    excel_header: str
    model_field: str
    required: bool = False
    normalizer: Optional[Callable[[str], str]] = None

def _s(x: str) -> str:
    return (x or "").strip()

# Mapeamento explícito dos headers que conhecemos da planilha Bling
KNOWN_FIELDS: list[FieldSpec] = [
    FieldSpec("ID", "external_id"),
    FieldSpec("Código", "sku", required=True, normalizer=_s),
    FieldSpec("Descrição", "name", required=True, normalizer=_s),
    FieldSpec("Unidade", "unit"),
    FieldSpec("NCM", "ncm"),
    FieldSpec("Origem", "origin"),
    FieldSpec("Preço", "price"),
    FieldSpec("Valor IPI fixo", "ipi_fixed"),
    FieldSpec("Observações", "notes"),
    FieldSpec("Situação", "status"),
    FieldSpec("Estoque", "stock_qty"),
    FieldSpec("Preço de custo", "cost_price"),
    FieldSpec("Cód no fornecedor", "supplier_code"),
    FieldSpec("Fornecedor", "supplier_name"),
    FieldSpec("Localização", "location"),

    # Trecho intermediário 16–45 permanece em bling_extra por padrão

    FieldSpec("Link Externo", "external_link"),
    FieldSpec("Meses Garantia no Fornecedor", "warranty_months_supplier"),
    FieldSpec("Clonar dados do pai", "clone_from_parent"),
    FieldSpec("Condição do produto", "product_condition"),
    FieldSpec("Frete Grátis", "free_shipping"),
    FieldSpec("Número FCI", "fci_number"),
    FieldSpec("Vídeo", "video_url"),
    FieldSpec("Departamento", "department"),
    FieldSpec("Unidade de medida", "unit_of_measure"),
    FieldSpec("Preço de compra", "purchase_price"),
    FieldSpec("Valor base ICMS ST para retenção", "icms_st_base_retencao"),
    FieldSpec("Valor ICMS ST para retenção", "icms_st_valor_retencao"),
    FieldSpec("Valor ICMS próprio do substituto", "icms_proprio_substituto"),
    FieldSpec("Categoria do produto", "product_category"),
    FieldSpec("Informações Adicionais", "extra_info"),

    # Campos adicionais do catálogo que podem existir na sua planilha
    FieldSpec("GTIN/EAN", "gtin"),
    FieldSpec("CEST", "cest"),
    FieldSpec("Marca", "brand"),
    FieldSpec("Largura (cm)", "width_cm"),
    FieldSpec("Altura (cm)", "height_cm"),
    FieldSpec("Profundidade (cm)", "length_cm"),
    FieldSpec("Peso Líquido (kg)", "weight_net"),
    FieldSpec("Peso Bruto (kg)", "weight_gross"),
    FieldSpec("Ativo", "is_active"),
]

HEADER_TO_FIELD = {f.excel_header: f for f in KNOWN_FIELDS}
FIELD_BY_HEADER = {f.excel_header: f.model_field for f in KNOWN_FIELDS}
REQUIRED_HEADERS = {f.excel_header for f in KNOWN_FIELDS if f.required}

def is_required_present(headers: list[str]) -> bool:
    """Confere se os headers obrigatórios existem na planilha."""
    hs = set([h.strip() for h in headers])
    return REQUIRED_HEADERS.issubset(hs)

def to_model_key(header: str) -> Optional[str]:
    """Retorna o nome do campo do model para um header conhecido. Senão, None."""
    spec = HEADER_TO_FIELD.get(header)
    return spec.model_field if spec else None
