# -*- coding: utf-8 -*-
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Tuple

from django.conf import settings
from django.db import transaction

from catalog.models import Product  # type: ignore
# services que você já tem:
from ai.services_imagem import gerar_mockup_de_desenho, editar_com_base_no_desenho
from openai import OpenAI
from django.conf import settings

# util: pega/gera um Variant para o Product
def _get_or_create_variant_for(product: Product):
    # tenta acessos comuns: product.variants, product.productvariant_set
    qs = None
    if hasattr(product, "variants"):
        qs = getattr(product, "variants")
    elif hasattr(product, "productvariant_set"):
        qs = getattr(product, "productvariant_set")
    if qs is None:
        raise RuntimeError("Não encontrei relação de variantes no Product.")

    obj, _ = qs.get_or_create(defaults={})
    return obj  # deve ter campos: desc_short, desc_medium, image_real_url

def _ensure_media_dir(sub: str) -> Path:
    root = Path(getattr(settings, "MEDIA_ROOT", "media"))
    path = root / sub
    path.mkdir(parents=True, exist_ok=True)
    return path

def _cheap_descs_for(product: Product) -> Tuple[str, str]:
    """
    Gera descrições curtas/baratas. Se falhar, retorna placeholders.
    """
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        return ("", "")

    client = OpenAI(api_key=api_key)
    nome = getattr(product, "name", "") or getattr(product, "sku", f"prod-{product.pk}")
    brand = getattr(product, "brand", "") or "Compton"
    sku = getattr(product, "sku", f"prod-{product.pk}")
    price = str(getattr(product, "price", "") or "")

    prompt = (
        "Escreva 2 textos em PT-BR, tom urbano descolado, concisos:\n"
        f"- Contexto: marca {brand}, SKU {sku}, nome '{nome}', preço {price}.\n"
        "- Saída JSON: {\"short\": \"até 120 chars\", \"medium\": \"até 300 chars\"}."
    )

    try:
        rsp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = rsp.choices[0].message.content or ""
        # tenta achar um JSON simples na resposta; fallback tosco
        import json, re
        m = re.search(r"\{.*\}", content, re.S)
        if not m:
            return ("", "")
        data = json.loads(m.group(0))
        return (str(data.get("short", "") or ""), str(data.get("medium", "") or ""))
    except Exception:
        return ("", "")

@transaction.atomic
def run_ai_for_product(product: Product, desenho_file=None, artes_file=None) -> None:
    """
    - Salva mockup realista em MEDIA_ROOT/products/<sku>_realista.jpg
    - Atualiza ProductVariant.desc_short / desc_medium / image_real_url
    - Se não houver API key ou falhar, não quebra o fluxo.
    """
    # garante SKU e paths
    sku = getattr(product, "sku", None) or f"prod-{product.pk}"
    out_dir = _ensure_media_dir("products")
    out_path = out_dir / f"{sku}_realista.jpg"

    # arquivos temporários (se enviados)
    tmp_dir = _ensure_media_dir("_tmp_ai")
    tmp_desenho = None
    if desenho_file:
        tmp_desenho = tmp_dir / f"desenho_{product.pk}"
        with open(tmp_desenho, "wb") as f:
            for chunk in desenho_file.chunks():
                f.write(chunk)

    # imagem: tenta gerar (usa generate; se falhar, tenta edit)
    try:
        ft_dict = {
            "sku": sku,
            "nome": getattr(product, "name", ""),
        }
        if tmp_desenho:
            # tenta edit com base na imagem
            try:
                editar_com_base_no_desenho(str(tmp_desenho), str(out_path), ft_dict, brand_notes="Compton.")
            except Exception:
                gerar_mockup_de_desenho(str(tmp_desenho), str(out_path), ft_dict, brand_notes="Compton.")
        else:
            gerar_mockup_de_desenho("", str(out_path), ft_dict, brand_notes="Compton.")
    except Exception:
        # ignora erro de imagem
        pass

    # descrições baratas
    short, medium = _cheap_descs_for(product)

    # persiste no Variant
    variant = _get_or_create_variant_for(product)
    changed = False

    if short:
        setattr(variant, "desc_short", short)
        changed = True
    if medium:
        setattr(variant, "desc_medium", medium)
        changed = True

    # se a imagem foi criada, guarde a URL relativa para servir via MEDIA_URL
    if out_path.exists():
        rel = os.path.relpath(out_path, start=getattr(settings, "MEDIA_ROOT", "media"))
        # muitos projetos usam ImageField/FileField; se for CharField, guardamos string mesmo
        setattr(variant, "image_real_url", f"{getattr(settings, 'MEDIA_URL', '/media/')}{rel}".replace("\\", "/"))
        changed = True

    if changed:
        variant.save()

def ensure_variant_image_or_fallback(product: Product) -> None:
    """
    Garante que a primeira variante tenha image_real_url.
    Se a IA não gerou nada, aplica placeholder do projeto.
    """
    variant = _get_or_create_variant_for(product)
    url = getattr(variant, "image_real_url", "") or ""
    if not url.strip():
        placeholder = getattr(settings, "PLACEHOLDER_IMAGE_URL", "/static/crontex/img/placeholder.png")
        setattr(variant, "image_real_url", placeholder)
        variant.save(update_fields=["image_real_url"])
