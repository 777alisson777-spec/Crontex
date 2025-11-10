# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
from pathlib import Path
from typing import Dict, Any
import requests

from openai import OpenAI
from django.conf import settings


def _get_openai() -> OpenAI:
    """
    Cria o cliente só quando for usar (evita acessar settings durante import).
    """
    key = getattr(settings, "OPENAI_API_KEY", None)
    if not key:
        raise RuntimeError("OPENAI_API_KEY ausente em settings/.env")
    return OpenAI(api_key=key)


def _prompt_compton(ft_dict: Dict[str, Any], brand_notes: str) -> str:
    return f"""
Gere um mockup fotográfico realista de peça Compton, guiado pelo desenho técnico.
Diretrizes:
- Fidelidade às linhas, recortes e proporções do desenho técnico.
- Estilo urbano, atitude confiante, diversidade; linguagem visual streetwear premium.
- Iluminação de estúdio suave; fundo cinza escuro, sem reflexo.
- Evidencie caimento, costuras e textura do tecido.
- Sem logos de terceiros. Sem texto na imagem.
Notas: {brand_notes}
Ficha técnica resumida: {ft_dict}
""".strip()


def _write_b64_or_url(data_obj: Any, out_path: Path) -> Path:
    """
    Salva a imagem vinda da API (b64_json ou url).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    b64 = getattr(data_obj, "b64_json", None)
    if b64:
        out_path.write_bytes(base64.b64decode(b64))
        return out_path

    url = getattr(data_obj, "url", None)
    if url:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        return out_path

    raise ValueError("Images API: sem b64_json e sem url.")


def gerar_mockup_texto(saida_png: str, ft_dict: dict, brand_notes: str = "") -> Path:
    client = _get_openai()
    prompt = _prompt_compton(ft_dict, brand_notes)
    resp = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1536",
        n=1,
        # ❌ response_format não é suportado aqui
        # response_format="b64_json",
    )
    return _write_b64_or_url(resp.data[0], Path(saida_png))


def editar_com_base_no_desenho(path_desenho: str, saida_png: str, ft_dict: dict, brand_notes: str = "") -> Path:
    """
    Edição com base no desenho técnico (image edit).
    """
    client = _get_openai()
    prompt = _prompt_compton(ft_dict, brand_notes)
    with open(path_desenho, "rb") as img:
        resp = client.images.edit(
            model="gpt-image-1",
            image=img,
            prompt=prompt,
            size="1024x1536",
            n=1,
        )
    data = resp.data[0]
    return _write_b64_or_url(data, Path(saida_png))


def gerar_mockup_de_desenho(path_desenho: str, saida_png: str, ft_dict: dict, brand_notes: str = "") -> Path:
    """
    Alias: usa a edição baseada no desenho técnico por padrão.
    """
    return editar_com_base_no_desenho(path_desenho, saida_png, ft_dict, brand_notes)
