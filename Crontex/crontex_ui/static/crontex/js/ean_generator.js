/* ============================================================================
 * CRONTEX — Geração de EAN-13 por variação  (padrão: [ref][base][tam][cor][dig])
 * Integra com:
 *   - #ean-ref (4 dígitos)
 *   - #ean-base (4 dígitos)
 *   - #map-size (textarea "Nome=NN" por linha)  [opcional; usa dicionário se vazio]
 *   - #map-color (textarea "Nome=NN" por linha) [opcional; usa dicionário se vazio]
 *   - #btn-generate-ean (botão)
 *   - #ean-preview (div de saída)
 *   - #id_grade_payload (hidden JSON { parametros: [{chave, valores}] })
 *
 * Regras:
 *   - tamanho e cor são mapeados para 2 dígitos cada.
 *   - checksum EAN-13 conforme especificação (peso 3 nas posições pares).
 *   - não altera server; apenas pré-visualiza a tabela com SKUs e EANs.
 * ============================================================================ */

(function () {
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  const elRef   = () => $("#ean-ref");
  const elBase  = () => $("#ean-base");
  const elMSize = () => $("#map-size");
  const elMColor= () => $("#map-color");
  const elBtn   = () => $("#btn-generate-ean");
  const elOut   = () => $("#ean-preview");
  const elGrade = () => $("#id_grade_payload"); // hidden com JSON da grade

  const dict = window.CrontexDictionaries || null;

  // ---- helpers --------------------------------------------------------------

  function sanitize4(str) {
    const s = String(str || "").replace(/\D+/g, "").slice(0, 4);
    return s.padEnd(4, "0");
  }

  function sanitize2(str) {
    const s = String(str || "").replace(/\D+/g, "").slice(0, 2);
    return s.padEnd(2, "0");
  }

  function computeEan13Checksum(first12) {
    // first12 = string com 12 dígitos
    const nums = first12.split("").map((c) => parseInt(c, 10));
    let sum = 0;
    // posições: 1..12 (da esquerda); pares têm peso 3
    for (let i = 0; i < 12; i++) {
      const pos = i + 1;
      sum += nums[i] * (pos % 2 === 0 ? 3 : 1);
    }
    const mod = sum % 10;
    const check = mod === 0 ? 0 : 10 - mod;
    return String(check);
  }

  function parseMapTextarea(textarea) {
    // Formato: "Nome=NN" por linha; ignora vazias
    const map = {};
    String((textarea && textarea.value) || "")
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter(Boolean)
      .forEach((line) => {
        const [k, v] = line.split("=").map((s) => (s || "").trim());
        if (k && v && /^\d{2}$/.test(v)) map[k.toLowerCase()] = v;
      });
    return map;
  }

  function buildSizeMapFallback() {
    if (!dict) return {};
    const m = {};
    // letras
    (dict.SIZE_LETTERS_ORDERED || []).forEach((name) => {
      const code = dict.SIZE_LETTERS_MAP?.[name]?.code;
      if (code) m[name.toLowerCase()] = code;
    });
    // numéricos
    (dict.SIZE_NUMBERS_ORDERED || []).forEach((n) => {
      const code = dict.SIZE_NUMBERS_MAP?.[String(n)]?.code;
      if (code) m[String(n).toLowerCase()] = code;
    });
    return m;
  }

  function buildColorMapFallback() {
    if (!dict) return {};
    const m = {};
    (dict.COLOR_SPEC || []).forEach((r) => {
      m[r.name.toLowerCase()] = r.code; // "PRETO" => "02"
    });
    return m;
  }

  function getGradeParams() {
    // Lê o hidden #id_grade_payload -> { parametros: [{chave, valores}] }
    try {
      const raw = elGrade() ? elGrade().value : "";
      if (!raw) return [];
      const obj = JSON.parse(raw);
      const list = obj?.parametros || [];
      return Array.isArray(list) ? list : [];
    } catch {
      return [];
    }
  }

  function cartesian(arr) {
    return arr.reduce(
      (a, b) => a.flatMap((d) => b.map((e) => [d, e].flat())),
      [[]]
    );
  }

  // Tenta identificar no array de parâmetros quem é tamanho e quem é cor
  function identifySizeAndColor(params) {
    // Estratégia: procura chaves que "parecem" tamanho/cor
    // — se não achar pelo nome, decide pela interseção com dicionários.
    const out = { size: null, color: null };

    // 1) por nome da chave
    const byName = (k) => (k || "").toLowerCase().replace(/\s+/g, "");
    params.forEach((p) => {
      const key = byName(p.chave);
      if (!out.size && /(tam|tamanho|size|numero|número)/.test(key)) out.size = p;
      if (!out.color && /(cor|color)/.test(key)) out.color = p;
    });
    if (out.size && out.color) return out;

    // 2) por interseção com dicionários (fallback)
    const sizeMap = { ...buildSizeMapFallback(), ...parseMapTextarea(elMSize()) };
    const colorMap = { ...buildColorMapFallback(), ...parseMapTextarea(elMColor()) };

    params.forEach((p) => {
      const values = (p.valores || []).map((v) => String(v).toLowerCase());
      const hitSize = values.some((v) => sizeMap[v]);
      const hitColor = values.some((v) => colorMap[v]);
      if (!out.size && hitSize) out.size = p;
      if (!out.color && hitColor) out.color = p;
    });

    return out;
  }

  function resolveSizeCode(nameRaw) {
    const name = String(nameRaw || "").toLowerCase().trim();
    const fromTxt = parseMapTextarea(elMSize());
    if (fromTxt[name]) return sanitize2(fromTxt[name]);

    // fallback dicionário
    if (dict) {
      const codeL = dict.SIZE_LETTERS_MAP?.[name.toUpperCase()]?.code || null;
      if (codeL) return sanitize2(codeL);
      const codeN = dict.SIZE_NUMBERS_MAP?.[String(name)]?.code || null;
      if (codeN) return sanitize2(codeN);
    }
    return "00";
  }

  function resolveColorCode(nameRaw) {
    const name = String(nameRaw || "").toLowerCase().trim();
    const fromTxt = parseMapTextarea(elMColor());
    if (fromTxt[name]) return sanitize2(fromTxt[name]);

    // fallback dicionário
    if (dict) {
      // aceita nome exato
      const code = dict.getColorCode ? dict.getColorCode(nameRaw) : null;
      if (code) return sanitize2(code);
      // tentativa cega por nome lower
      const m = buildColorMapFallback();
      if (m[name]) return sanitize2(m[name]);
    }
    return "00";
  }

  function buildCombosForSizeColor(params) {
    const { size, color } = identifySizeAndColor(params);
    const valsSize = size?.valores || [];
    const valsColor = color?.valores || [];

    // se faltar um dos dois, ainda geramos com "00" no que faltar
    const listSize  = valsSize.length  ? valsSize  : ["—"];
    const listColor = valsColor.length ? valsColor : ["—"];

    // mantém outras chaves para exibir contexto na tabela
    const others = params.filter((p) => p !== size && p !== color);

    // produto cartesiano tam x cor, com payload de contexto
    const combos = [];
    listSize.forEach((s) => {
      listColor.forEach((c) => {
        combos.push({
          size: s,
          color: c,
          ctx: others.map((o) => ({ key: o.chave, value: (o.valores || [])[0] || "" })),
        });
      });
    });
    return combos;
  }

  function renderTable(rows) {
    const out = elOut();
    if (!out) return;
    out.innerHTML = "";

    if (!rows.length) {
      out.innerHTML = `<div class="alert info">Sem combinações para gerar EAN.</div>`;
      return;
    }

    const table = document.createElement("table");
    table.className = "table";

    const thead = document.createElement("thead");
    const trh = document.createElement("tr");
    ["Tamanho", "Cor", "SKU (12)", "EAN-13"].forEach((h) => {
      const th = document.createElement("th");
      th.textContent = h;
      trh.appendChild(th);
    });
    thead.appendChild(trh);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    rows.forEach((r) => {
      const tr = document.createElement("tr");
      const tdSize = document.createElement("td");
      const tdColor = document.createElement("td");
      const tdSku = document.createElement("td");
      const tdEan = document.createElement("td");

      tdSize.textContent = r.size;
      tdColor.textContent = r.color;
      tdSku.textContent = r.sku12;
      tdEan.textContent = r.ean13;

      tr.appendChild(tdSize);
      tr.appendChild(tdColor);
      tr.appendChild(tdSku);
      tr.appendChild(tdEan);
      tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    out.appendChild(table);
  }

  // ---- main ---------------------------------------------------------------

  function generate() {
    const out = elOut();
    if (!out) return;

    const ref4  = sanitize4(elRef()?.value || "");
    const base4 = sanitize4(elBase()?.value || "");

    if (!/^\d{4}$/.test(ref4) || !/^\d{4}$/.test(base4)) {
      out.innerHTML = `<div class="alert error">Preencha REF (4 dígitos) e BASE (4 dígitos).</div>`;
      return;
    }

    const params = getGradeParams(); // [{chave, valores}]
    if (!params.length) {
      out.innerHTML = `<div class="alert info">Defina ao menos um parâmetro com valores na aba <b>Grade</b>.</div>`;
      return;
    }

    const combos = buildCombosForSizeColor(params);
    if (!combos.length) {
      out.innerHTML = `<div class="alert info">Sem combinações de tamanho/cor para processar.</div>`;
      return;
    }

    const rows = combos.map((c) => {
      const tam2 = sanitize2(resolveSizeCode(c.size));
      const cor2 = sanitize2(resolveColorCode(c.color));
      const sku12 = `${ref4}${base4}${tam2}${cor2}`;
      const dig = computeEan13Checksum(sku12);
      const ean13 = `${sku12}${dig}`;
      return { size: c.size, color: c.color, sku12, ean13 };
    });

    renderTable(rows);
  }

  function wire() {
    const btn = elBtn();
    if (!btn) return;
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      generate();
    });
  }

  // boot
  document.addEventListener("DOMContentLoaded", () => {
    // safety logs mínimos (sem poluir)
    if (!window.CrontexDictionaries) {
      // Pode operar apenas com mapas do textarea, mas avisa:
      console.warn("[Crontex] Dicionário de cores/tamanhos não encontrado. Usando apenas mapas manuais (textareas).");
    }
    wire();
  });
})();
