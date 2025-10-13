// ============================================================
// CRONTEX - FORM DE PRODUTO (tabs + grade dinâmica + skus EAN-13)
// Mantém padrão: <script src="{% static 'crontex/js/produto_form_full.js' %}"></script>
// ============================================================

(function () {
  const log = (...a) => console.log(...a);
  const warn = (...a) => console.warn(...a);

  document.addEventListener("DOMContentLoaded", () => {
    log("🔥 DOM pronto — produto_form_full.js");

    // ---------- Tabs ----------
    const tabs = document.querySelectorAll(".tab[role='tab']");
    const panels = document.querySelectorAll(".tab-panel");
    const form = document.getElementById("produto-form");

    // util: marca/limpa required de inputs em um painel
    const setPanelRequired = (panelEl, enable) => {
      if (!panelEl) return;
      const fields = panelEl.querySelectorAll("input, select, textarea");
      fields.forEach((f) => {
        if (f.dataset.required === "1") {
          if (enable) f.setAttribute("required", "required");
          else f.removeAttribute("required");
        }
      });
    };

    // registra quais eram required originalmente
    const bootstrapRequiredFlags = () => {
      document
        .querySelectorAll(".tab-panel input[required], .tab-panel select[required], .tab-panel textarea[required]")
        .forEach((el) => (el.dataset.required = "1"));
      // só mantém required no painel ativo
      panels.forEach((p) => {
        const isActive = p.classList.contains("is-active") && !p.hidden;
        setPanelRequired(p, isActive);
      });
    };

    const activateTab = (tab) => {
      tabs.forEach((t) => {
        t.classList.remove("is-active");
        t.setAttribute("aria-selected", "false");
      });
      panels.forEach((p) => {
        setPanelRequired(p, false); // limpamos antes de esconder
        p.classList.remove("is-active");
        p.hidden = true;
      });

      tab.classList.add("is-active");
      tab.setAttribute("aria-selected", "true");
      const target = tab.dataset.tab;
      const panel = document.querySelector(`.tab-panel[data-tab='${target}']`);
      if (panel) {
        panel.classList.add("is-active");
        panel.hidden = false;
        setPanelRequired(panel, true);
      }
    };

    // acha tab por data-tab
    const getTabButton = (name) => document.querySelector(`.tab[role='tab'][data-tab='${name}']`);

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        activateTab(tab);
        if (tab.dataset.tab === "grade") {
          renderVariations();
          renderTable();
        }
      });
    });

    bootstrapRequiredFlags();
    log("✅ Abas inicializadas");

    // Se o servidor retornou erros (sentinela no template), abre a aba "bling"
    const hasServerErrors = document.getElementById("form-has-errors");
    if (hasServerErrors) {
      const blingTab = getTabButton("bling") || tabs[0];
      activateTab(blingTab);

      // marca como erro os required vazios da aba ativa
      const activePanel = document.querySelector(".tab-panel.is-active");
      if (activePanel) {
        const reqs = activePanel.querySelectorAll("[data-required='1']");
        reqs.forEach((el) => {
          if (
            (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.tagName === "SELECT") &&
            !String(el.value || "").trim()
          ) {
            el.classList.add("error");
          }
        });
        // foco no primeiro erro
        const firstErr = activePanel.querySelector(".input.error");
        if (firstErr) firstErr.focus({ preventScroll: false });
      }
    }

    // ---------- GRADE DINÂMICA ----------
    const payloadInput = document.getElementById("id_grade_payload");
    const addParamBtn = document.getElementById("btn-add-param");
    const listWrapper = document.getElementById("variations-wrapper");
    const preview = document.getElementById("grade-preview");
    const skuField = document.getElementById("id_sku"); // SKU pai (ref+base)
    const blingExtraField = document.getElementById("id_bling_extra"); // textarea JSON (oculta)

    if (!(payloadInput && addParamBtn && listWrapper && preview)) {
      warn("ℹ️ Página sem grade editável. Encerrando módulos de grade.");
      return;
    }
    log("✅ DOM da grade pronto.");

    let variations = []; // [{chave:'tam', valores:['P','M',...]}, ...]

    // utils
    const cartesian = (arr) =>
      arr.reduce((a, b) => a.flatMap((d) => b.map((e) => [d, e].flat())), [[]]);

    const twoDigit = (n) => String(n).padStart(2, "0");

    // EAN-13
    const ean13CheckDigit = (num12) => {
      let s = 0;
      for (let i = 0; i < 12; i++) {
        const d = num12.charCodeAt(i) - 48;
        s += d * (i % 2 ? 3 : 1);
      }
      const dv = (10 - (s % 10)) % 10;
      return String(dv);
    };

    const deriveRefBase = () => {
      const sku = (skuField && skuField.value) ? skuField.value.trim() : "";
      const refRaw = (sku.slice(0, 4) || "0000").padEnd(4, "0").slice(0, 4);
      const baseRaw = (sku.slice(-4) || "0000").padStart(4, "0").slice(-4);
      const onlyDigits = (s) => s.replace(/\D/g, "0");
      const ref = onlyDigits(refRaw);
      const base = onlyDigits(baseRaw);
      return { ref: ref.length === 4 ? ref : "0000", base: base.length === 4 ? base : "0000" };
    };

    const buildCombosAndSkus = () => {
      const params = variations
        .map((p) => ({
          chave: (p.chave || "").trim(),
          valores: (p.valores || []).map((v) => String(v).trim()).filter(Boolean),
        }))
        .filter((p) => p.chave);

      if (params.length === 0) return { rows: [], meta: {} };

      const p1 = params[0];
      const p2 = params[1] || { chave: "", valores: [] };

      const map1 = p1.valores.length ? Object.fromEntries(p1.valores.map((v, i) => [v, twoDigit(i + 1)])) : { "—": "00" };
      const map2 = p2.valores.length ? Object.fromEntries(p2.valores.map((v, i) => [v, twoDigit(i + 1)])) : { "—": "00" };

      const { ref, base } = deriveRefBase();

      const axes = params.map((p) => (p.valores.length ? p.valores : ["—"]));
      const combos = cartesian(axes);

      const rows = combos.map((vals) => {
        const combo = Object.fromEntries(vals.map((v, i) => [params[i].chave, vals[i]]));
        const v1 = combo[p1.chave] ?? "—";
        const v2 = p2.chave ? combo[p2.chave] ?? "—" : "—";
        const c1 = map1[v1] || "00";
        const c2 = map2[v2] || "00";
        const base12 = `${ref}${base}${c1}${c2}`;
        const dv = ean13CheckDigit(base12);
        const ean13 = `${base12}${dv}`;
        return { combo, sku: ean13 };
      });

      const meta = {
        ref,
        base,
        param_tamanho: p1.chave,
        param_cor: p2.chave || "",
        warn: params.length > 2 ? "Mais de 2 parâmetros; somente os 2 primeiros entram no EAN-13." : undefined,
      };

      return { rows, meta };
    };

    const updateBlingExtraGradeSkus = () => {
      if (!blingExtraField) return;
      let obj;
      try {
        obj = JSON.parse(blingExtraField.value || "{}");
      } catch {
        obj = {};
      }
      obj = obj && typeof obj === "object" ? obj : {};

      // grade (payload)
      let gradePayload = {};
      try {
        gradePayload = JSON.parse(payloadInput.value || "{}");
      } catch {
        gradePayload = {};
      }
      obj.grade = gradePayload;

      // skus calculados
      const { rows, meta } = buildCombosAndSkus();
      obj.grade_skus = rows;
      obj.grade_skus_meta = meta;

      blingExtraField.value = JSON.stringify(obj);
    };

    const updatePayload = () => {
      const payload = { parametros: variations };
      payloadInput.value = JSON.stringify(payload);
      updateBlingExtraGradeSkus();
      log("🧠 Payload:", payloadInput.value);
      renderTable();
    };

    const makeChip = (val, idx, vi) => {
      const chip = document.createElement("span");
      chip.className = "token-chip";
      chip.textContent = val;
      const close = document.createElement("button");
      close.className = "token-close";
      close.type = "button";
      close.textContent = "×";
      close.onclick = () => {
        variations[idx].valores.splice(vi, 1);
        updatePayload();
        renderVariations();
      };
      chip.appendChild(close);
      return chip;
    };

    const renderVariations = () => {
      listWrapper.innerHTML = "";
      variations.forEach((v, idx) => {
        const row = document.createElement("div");
        row.className = "variation-row flex items-center gap-2 mb-2";

        const key = document.createElement("input");
        key.className = "input small w-1/4";
        key.placeholder = "Parâmetro (ex: tam, cor)";
        key.value = v.chave || "";
        key.addEventListener("input", (e) => {
          const val = (e.target.value || "").trim();
          variations[idx].chave = val;
          updatePayload();
        });

        const box = document.createElement("div");
        box.className = "token-input flex-1";
        const chipList = document.createElement("div");
        chipList.className = "token-list";
        (v.valores || []).forEach((val, vi) => chipList.appendChild(makeChip(val, idx, vi)));

        const editor = document.createElement("input");
        editor.className = "token-editor";
        editor.placeholder = "Valores (TAB, ENTER ou ,)";
        editor.addEventListener("keydown", (e) => {
          if (e.key === "Tab" || e.key === "," || e.key === "Enter") {
            e.preventDefault();
            const val = (editor.value || "").trim();
            if (val && !(v.valores || []).includes(val)) {
              v.valores.push(val);
              editor.value = "";
              updatePayload();
              renderVariations();
            }
          }
        });

        box.appendChild(chipList);
        box.appendChild(editor);

        const del = document.createElement("button");
        del.className = "btn small danger";
        del.type = "button";
        del.textContent = "–";
        del.onclick = () => {
          variations.splice(idx, 1);
          updatePayload();
          renderVariations();
        };

        row.appendChild(key);
        row.appendChild(box);
        row.appendChild(del);
        listWrapper.appendChild(row);
      });
      log("🎨 renderVariations() OK —", variations);
    };

    const renderTable = () => {
      preview.innerHTML = "";

      if (!variations.length) {
        preview.innerHTML = `<div class="alert info">Nenhum parâmetro adicionado.</div>`;
        return;
      }

      const headers = variations.map((v) => (v.chave || "—").toUpperCase());
      const { rows } = buildCombosAndSkus();

      const table = document.createElement("table");
      table.className = "table";
      const thead = document.createElement("thead");
      const trh = document.createElement("tr");
      headers.forEach((h) => {
        const th = document.createElement("th");
        th.textContent = h;
        trh.appendChild(th);
      });
      const thSku = document.createElement("th");
      thSku.textContent = "SKUs (EAN-13)";
      trh.appendChild(thSku);
      thead.appendChild(trh);
      table.appendChild(thead);

      const tbody = document.createElement("tbody");
      if (!rows.length) {
        const tr = document.createElement("tr");
        const td = document.createElement("td");
        td.colSpan = headers.length + 1;
        td.className = "muted";
        td.textContent = "Adicione valores para gerar a grade.";
        tr.appendChild(td);
        tbody.appendChild(tr);
      } else {
        rows.forEach(({ combo, sku }) => {
          const tr = document.createElement("tr");
          variations.forEach((p) => {
            const td = document.createElement("td");
            td.textContent = combo[p.chave] ?? "—";
            tr.appendChild(td);
          });
          const tdSku = document.createElement("td");
          tdSku.textContent = sku;
          tr.appendChild(tdSku);
          tbody.appendChild(tr);
        });
      }

      table.appendChild(tbody);
      preview.appendChild(table);
      log("📊 renderTable() OK —", rows.length, "linhas");
    };

    // botão add parâmetro
    if (addParamBtn) {
      addParamBtn.addEventListener("click", () => {
        variations.push({ chave: "", valores: [] });
        updatePayload();
        renderVariations();
        log("➕ Parâmetro adicionado");
      });
    }

    // carregar dados prévios (edição)
    try {
      const initial = JSON.parse(payloadInput.value || "{}");
      if (initial && Array.isArray(initial.parametros)) {
        variations = initial.parametros.map((p) => ({
          chave: p.chave || "",
          valores: Array.isArray(p.valores) ? p.valores : [],
        }));
      }
    } catch {
      variations = [];
    }

    // boot render
    renderVariations();
    updatePayload();

    // re-calcula preview se SKU pai mudar (ref/base)
    if (skuField) {
      skuField.addEventListener("input", () => updatePayload());
    }

    log("✅ Inicialização completa — FORM");
  });
})();
