# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from typing import Tuple

from openai import OpenAI
from django.conf import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM = (
    "Você é redator técnico da marca Compton. Escreva em PT-BR, tom urbano e direto, "
    "sem enrolação. Sem promessas vazias. Sem superlativos óbvios."
)

def gerar_descricoes_curta_media(sku: str, nome: str, notas: str = "") -> Tuple[str, str]:
    """
    Retorna (desc_curta <= 140c, desc_media ~ 300-600c).
    Usa modelo econômico.
    """
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": (
            "Gere duas descrições em JSON com chaves 'curta' e 'media'. "
            "curta: até 140 caracteres, headline impactante. "
            "media: 300-600 caracteres, técnica porém acessível, linguagem urbana. "
            f"SKU: {sku}\nNome: {nome}\nNotas: {notas}"
        )},
    ]
    rsp = client.chat.completions.create(
        model="gpt-4o-mini",  # econômico
        messages=msgs,
        temperature=0.4,
        response_format={"type": "json_object"},
    )
    raw = rsp.choices[0].message.content
    data = json.loads(raw)
    return data.get("curta", ""), data.get("media", "")
