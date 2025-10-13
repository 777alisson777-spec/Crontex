/* =============================================================================
 * CRONTEX – Dicionários de Grade (Cores + Tamanhos) v2.0
 * Base de cores sincronizada com a sua planilha (00–99).
 * - code = "00".."99"
 * - family = família da tabela (qdo existir)
 * - cmyk = [C,M,Y,K] em percentuais (qdo existir)
 * - rgb/hex são derivados on-the-fly de CMYK; quando CMYK ausente, ficam null.
 * - Helpers para gerar mapas "Nome=NN" (Bling), normalizar e buscar códigos.
 * =============================================================================
 * Uso rápido:
 *   CrontexDictionaries.presetMapColors()            -> texto p/ textarea
 *   CrontexDictionaries.presetMapLetterSizes()
 *   CrontexDictionaries.presetMapNumberSizes()
 *   CrontexDictionaries.getColorCode("PRETO")        -> "02"
 *   CrontexDictionaries.getLetterSizeCode("G2")      -> "07"
 *   CrontexDictionaries.getNumberSizeCode(42)        -> "42"
 * ============================================================================= */

(function (root, factory) {
  const lib = factory();
  // Browser global
  root.CrontexDictionaries = lib;
  // CommonJS
  if (typeof module !== "undefined" && module.exports) module.exports = lib;
})(typeof self !== "undefined" ? self : this, function () {
  // ---------- utils ----------
  const slug = (s) =>
    String(s || "")
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .toLowerCase().replace(/\s+/g, " ").trim();

  const cmykToRgb = (c, m, y, k) => {
    // c,m,y,k em 0..100 -> rgb 0..255
    const C = (c || 0) / 100, M = (m || 0) / 100, Y = (y || 0) / 100, K = (k || 0) / 100;
    const r = Math.round(255 * (1 - C) * (1 - K));
    const g = Math.round(255 * (1 - M) * (1 - K));
    const b = Math.round(255 * (1 - Y) * (1 - K));
    return [r, g, b];
  };

  const rgbToHex = ([r, g, b]) =>
    "#" + [r, g, b].map(v => v.toString(16).padStart(2, "0")).join("").toUpperCase();

  // ---------- tabela de cores (copiada da sua planilha) ----------
  // name, code, family, cmyk: [C,M,Y,K] (percentuais) ou null quando "-".
  const COLOR_SPEC = [
    { name: "TRANSPARENTE", code: "00", family: "BÁSICAS", cmyk: [0,0,0,0] },
    { name: "BRANCO",       code: "01", family: "BÁSICAS", cmyk: [0,0,0,0] },
    { name: "PRETO",        code: "02", family: "BÁSICAS", cmyk: [0,0,0,100] },
    { name: "TURQUESA",     code: "03", family: "BÁSICAS", cmyk: [100,0,0,0] },
    { name: "PINK",         code: "04", family: "BÁSICAS", cmyk: [0,100,0,0] },
    { name: "AMARELO",      code: "05", family: "BÁSICAS", cmyk: [0,0,100,0] },
    { name: "RED",          code: "06", family: "BÁSICAS", cmyk: null },
    { name: "GREEN",        code: "07", family: "BÁSICAS", cmyk: null },
    { name: "BLUE",         code: "08", family: "BÁSICAS", cmyk: null },

    { name: "AMARELO CLARO", code: "09", family: "AMARELO", cmyk: [0,0,16,0] },
    { name: "MOSTARDA",      code: "10", family: "AMARELO", cmyk: [0,20,100,0] },

    { name: "CRU",           code: "11", family: "CAQUI",   cmyk: [0,0,5,5] },
    { name: "AREIA",         code: "12", family: "CAQUI",   cmyk: [5,5,16,7] },
    { name: "CAQUI CLARO",   code: "13", family: "CAQUI",   cmyk: [16,15,37,11] },
    { name: "CAQUI ESCURO",  code: "14", family: "MARROM",  cmyk: [28,31,44,0] },
    { name: "MARROM",        code: "15", family: "MARROM",  cmyk: [50,90,90,50] },

    { name: "VERDE CLARO",   code: "16", family: "VERDE",   cmyk: [16,0,16,0] },
    { name: "BANDEIRA",      code: "17", family: "VERDE",   cmyk: [100,0,100,0] },
    { name: "VERDE PISCINA", code: "18", family: "VERDE",   cmyk: [79,7,37,0] },
    { name: "MILITAR",       code: "19", family: "VERDE",   cmyk: [98,42,92,50] },
    { name: "MUSGO",         code: "20", family: "VERDE",   cmyk: [65,40,86,26] },
    { name: "OLIVA",         code: "21", family: "VERDE",   cmyk: [56,41,52,11] },

    { name: "AZUL CLARO",    code: "22", family: "AZUL",    cmyk: [16,0,0,0] },
    { name: "AZUL JEANS",    code: "23", family: "AZUL",    cmyk: [73,40,16,0] },
    { name: "ROYAL",         code: "24", family: "AZUL",    cmyk: [95,75,0,0] },
    { name: "MARINHO",       code: "25", family: "AZUL",    cmyk: [100,78,37,30] },
    { name: "MARINHO CLARO", code: "26", family: "AZUL",    cmyk: [40,40,0,60] },

    { name: "LILAS BEBE",    code: "27", family: "LILAS",   cmyk: [16,16,0,0] },
    { name: "LILAS",         code: "28", family: "LILAS",   cmyk: [26,26,0,15] },
    { name: "ROXO",          code: "29", family: "LILAS",   cmyk: [89,89,0,0] },
    { name: "UVA",           code: "30", family: "LILAS",   cmyk: [68,68,0,35] },

    { name: "ROSA CLARO",    code: "31", family: "ROSA",    cmyk: [0,10,0,0] },
    { name: "ROSADO",        code: "32", family: "ROSA",    cmyk: [0,26,0,15] },
    { name: "MARSALA",       code: "33", family: "ROSA",    cmyk: [0,100,0,50] },

    { name: "VERMELHO",      code: "34", family: "VERMELHO", cmyk: [0,100,100,0] },
    { name: "VINHO",         code: "35", family: "VERMELHO", cmyk: [0,100,100,40] },
    { name: "BORDO",         code: "36", family: "VERMELHO", cmyk: [30,100,100,42] },
    { name: "SALMAO",        code: "37", family: "LARANJA",  cmyk: [0,10,20,0] },
    { name: "LARANJA",       code: "38", family: "LARANJA",  cmyk: [0,50,100,0] },

    { name: "GELO",          code: "39", family: "CINZAS",  cmyk: [0,0,0,10] },
    { name: "CINZA",         code: "40", family: "CINZAS",  cmyk: [0,0,0,50] },
    { name: "CHUMBO",        code: "41", family: "CINZAS",  cmyk: [0,0,0,80] },

    { name: "AMARELO FLUOR", code: "42", family: "FLÚOR",   cmyk: null },
    { name: "LARANJA FLUOR", code: "43", family: "FLÚOR",   cmyk: null },
    { name: "ROSA FLUOR",    code: "44", family: "FLÚOR",   cmyk: null },
    { name: "VERDE FLUOR",   code: "45", family: "FLÚOR",   cmyk: null },

    { name: "VERMELHO MESCLA", code: "46", family: "MESCLA", cmyk: null },
    { name: "MARINHO MESCLA",  code: "47", family: "MESCLA", cmyk: null },
    { name: "VERDE MESCLA",    code: "48", family: "MESCLA", cmyk: null },
    { name: "GELO MESCLA",     code: "49", family: "MESCLA", cmyk: null },
    { name: "CINZA MESCLA",    code: "50", family: "MESCLA", cmyk: null },
    { name: "CHUMBO MESCLA",   code: "51", family: "MESCLA", cmyk: null },
    { name: "AREIA MESCLA",    code: "52", family: "MESCLA", cmyk: null },
    { name: "PRETO MESCLA",    code: "53", family: "MESCLA", cmyk: null },
    { name: "OLIVA MESCLA",    code: "54", family: "MESCLA", cmyk: null },
    { name: "JEANS MESCLA",    code: "55", family: "MESCLA", cmyk: null },

    { name: "FERRUGEM",      code: "56", family: "LARANJA", cmyk: null },
    { name: "PETROLEO",      code: "57", family: null,      cmyk: null },
    { name: "GOIABA",        code: "58", family: null,      cmyk: null },
    { name: "ANIS",          code: "59", family: null,      cmyk: null },
    { name: "TIFFANY",       code: "60", family: null,      cmyk: null },

    // 61..69 vazios na planilha original -> ignorados

    { name: "INDIGO DELAVE", code: "70", family: "JEANS",  cmyk: null },
    { name: "INDIGO MEDIO",  code: "71", family: "JEANS",  cmyk: null },
    { name: "INDIGO ESCURO", code: "72", family: "JEANS",  cmyk: null },
    { name: "INDIGO BLACK",  code: "73", family: "JEANS",  cmyk: null },

    // 74 vazio

    { name: "PRATA",         code: "75", family: "METAIS",     cmyk: null },
    { name: "OURO",          code: "76", family: "METAIS",     cmyk: null },
    { name: "BRONZE",        code: "77", family: "METAIS",     cmyk: null },

    { name: "STONE",         code: "78", family: "TINGIMENTO", cmyk: null },
    { name: "TIE DIE",       code: "79", family: "TINGIMENTO", cmyk: null },
    { name: "MANCHADO",      code: "80", family: "TINGIMENTO", cmyk: null },
    { name: "DEGRADE",       code: "81", family: "TINGIMENTO", cmyk: null },

    { name: "GEOMETRICO",    code: "82", family: "ESTAMPAS", cmyk: null },
    { name: "RESPINGO",      code: "83", family: "ESTAMPAS", cmyk: null },
    { name: "TEXTURA",       code: "84", family: "ESTAMPAS", cmyk: null },
    { name: "XADREZ",        code: "85", family: "ESTAMPAS", cmyk: null },
    { name: "LISTRADO",      code: "86", family: "ESTAMPAS", cmyk: null },
    { name: "CAVEIRA",       code: "87", family: "ESTAMPAS", cmyk: null },
    { name: "REGGAE",        code: "88", family: "ESTAMPAS", cmyk: null },
    { name: "LOGOS STUN",    code: "89", family: "ESTAMPAS", cmyk: null },
    { name: "ESCRITO STUN",  code: "90", family: "ESTAMPAS", cmyk: null },
    { name: "MUSICA",        code: "91", family: "ESTAMPAS", cmyk: null },
    { name: "SKATE",         code: "92", family: "ESTAMPAS", cmyk: null },
    { name: "SURF",          code: "93", family: "ESTAMPAS", cmyk: null },
    { name: "FLORAL CLARO",  code: "94", family: "ESTAMPAS", cmyk: null },
    { name: "FLORAL ESCURO", code: "95", family: "ESTAMPAS", cmyk: null },
    { name: "CAMUFLADO",     code: "96", family: "ESTAMPAS", cmyk: null },
    { name: "CAMU CINZA",    code: "97", family: "ESTAMPAS", cmyk: null },
    { name: "CAMU VERDE",    code: "98", family: "ESTAMPAS", cmyk: null },
    { name: "VARIAS",        code: "99", family: "ESTAMPAS", cmyk: null },
  ];

  // ---------- build maps ----------
  const COLOR_MAP = {};
  const COLOR_BY_CODE = {};

  COLOR_SPEC.forEach(row => {
    let rgb = null, hex = null;
    if (row.cmyk && row.cmyk.length === 4) {
      rgb = cmykToRgb(row.cmyk[0], row.cmyk[1], row.cmyk[2], row.cmyk[3]);
      hex = rgbToHex(rgb);
    }
    const payload = {
      code: row.code,
      family: row.family || null,
      cmyk: row.cmyk || null,
      rgb,
      hex,
    };
    COLOR_MAP[row.name] = payload;
    COLOR_BY_CODE[row.code] = { name: row.name, ...payload };
  });

  // ---------- tamanhos ----------
  const SIZE_LETTERS_ORDERED = ["PP","P","M","G","GG","G1","G2","G3"];
  const SIZE_LETTERS_MAP = SIZE_LETTERS_ORDERED
    .reduce((acc, name, i) => { acc[name] = { code: String(i+1).padStart(2,"0") }; return acc; }, {});

  // 16,18,20...34,36,38...58
  const SIZE_NUMBERS_ORDERED = [16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58];
  const SIZE_NUMBERS_MAP = SIZE_NUMBERS_ORDERED
    .reduce((acc, n) => { acc[String(n)] = { code: String(n).padStart(2,"0") }; return acc; }, {});

  // ---------- helpers ----------
  const resolveColorName = (nameOrCode) => {
    const s = String(nameOrCode || "");
    // se veio código "NN"
    if (/^\d{2}$/.test(s)) {
      return COLOR_BY_CODE[s]?.name || null;
    }
    // nome
    const target = slug(s);
    for (const n of Object.keys(COLOR_MAP)) {
      if (slug(n) === target) return n;
    }
    return null;
  };

  const getColorCode = (nameOrCode) => {
    // aceita já o código
    const s = String(nameOrCode || "");
    if (/^\d{2}$/.test(s)) return s;
    const n = resolveColorName(s);
    return n ? COLOR_MAP[n].code : null;
  };

  const toTextareaMap = (dict, keys) => {
    const list = Array.isArray(keys) && keys.length ? keys : Object.keys(dict);
    return list.map(k => `${k}=${dict[k].code}`).join("\n");
  };

  const presetMapColors = () => {
    // mantém a ordem do COLOR_SPEC
    return COLOR_SPEC.map(r => `${r.name}=${r.code}`).join("\n");
  };
  const presetMapLetterSizes = () => toTextareaMap(SIZE_LETTERS_MAP, SIZE_LETTERS_ORDERED);
  const presetMapNumberSizes = () => toTextareaMap(
    SIZE_NUMBERS_MAP, SIZE_NUMBERS_ORDERED.map(String)
  );

  const getLetterSizeCode = (name) => SIZE_LETTERS_MAP[String(name || "").toUpperCase()]?.code || null;
  const getNumberSizeCode = (value) => SIZE_NUMBERS_MAP[String(value)]?.code || null;

  // ---------- export ----------
  return {
    // cores
    COLOR_MAP,           // por nome
    COLOR_BY_CODE,       // por código
    COLOR_SPEC,          // array original
    // tamanhos
    SIZE_LETTERS_MAP,
    SIZE_LETTERS_ORDERED,
    SIZE_NUMBERS_MAP,
    SIZE_NUMBERS_ORDERED,
    // helpers
    resolveColorName,
    getColorCode,
    getLetterSizeCode,
    getNumberSizeCode,
    toTextareaMap,
    presetMapColors,
    presetMapLetterSizes,
    presetMapNumberSizes,
  };
});
