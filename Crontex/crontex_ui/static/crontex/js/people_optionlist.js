(function(){
  "use strict";

  // ======= Helpers =======
  function $(sel, root){ return (root||document).querySelector(sel); }
  function $all(sel, root){ return Array.prototype.slice.call((root||document).querySelectorAll(sel)); }

  // Monta painel do dropdown (busca + lista)
  function buildPanel(root){
    const panel = document.createElement("div");
    panel.className = "combo-panel";
    panel.hidden = true;

    const q = document.createElement("input");
    q.type = "text";
    q.className = "input combo-search";
    q.placeholder = "Pesquisar...";

    const list = document.createElement("ul");
    list.className = "combo-list";
    list.setAttribute("role", "listbox");
    list.tabIndex = -1;

    panel.appendChild(q);
    panel.appendChild(list);
    root.appendChild(panel);
    return { panel, q, list };
  }

  function renderItems(listEl, items){
    listEl.innerHTML = "";
    if (!items.length){
      const li = document.createElement("div");
      li.className = "combo-empty";
      li.textContent = "Nenhum resultado.";
      listEl.appendChild(li);
      return;
    }
    items.forEach((it, idx) => {
      const li = document.createElement("li");
      li.className = "combo-option";
      li.setAttribute("role", "option");
      li.setAttribute("data-id", String(it.id));
      li.setAttribute("data-name", it.name);
      li.setAttribute("aria-selected", idx===0 ? "true" : "false");
      // Mantém o visual existente: "Nome — <rótulo>"
      li.textContent = it.name + " — " + (it.role_label || it.role_key || "");
      listEl.appendChild(li);
    });
  }

  function getActiveOption(listEl){
    return listEl.querySelector('.combo-option[aria-selected="true"]');
  }
  function setActiveOption(listEl, el){
    $all('.combo-option[aria-selected="true"]', listEl).forEach(n=>n.setAttribute('aria-selected','false'));
    if (el) el.setAttribute('aria-selected','true');
    if (el && el.scrollIntoView) el.scrollIntoView({block:'nearest'});
  }
  function moveActive(listEl, dir){
    const opts = $all('.combo-option', listEl);
    if (!opts.length) return;
    let idx = opts.findIndex(n => n.getAttribute('aria-selected') === 'true');
    idx = (idx < 0) ? 0 : idx + dir;
    if (idx < 0) idx = 0;
    if (idx >= opts.length) idx = opts.length - 1;
    setActiveOption(listEl, opts[idx]);
  }

  // ======= Data Source (INTEGRADO com /people/api) =======
  // Substitui o antigo /people/collaborators/search pelo novo contrato:
  //   GET /people/api/search/?q=<termo>&page=1[&type=<roleKey>]
  //   -> { results: [{id, text, subtitle}], pagination: {more: bool} }
  // Mapeamos para o shape esperado por renderItems(): {id, name, role_label|role_key}
  function fetchPeople(q, roleKey, signal){
    const u = new URL("/people/api/search/", window.location.origin);
    if (q) u.searchParams.set("q", q);
    // Nosso backend espera "type" (não "role"); mantemos compat no JS:
    if (roleKey) u.searchParams.set("type", roleKey);
    u.searchParams.set("page", "1");

    return fetch(u.toString(), { credentials:"same-origin", signal, headers: {"X-Requested-With":"XMLHttpRequest"} })
      .then(r => r.ok ? r.json() : {results:[]})
      .then(d => {
        const arr = Array.isArray(d.results) ? d.results : [];
        // map -> shape antigo
        const mapped = arr.map(it => ({
          id: it.id,
          name: it.text || "",                 // texto principal vira "name"
          role_label: it.subtitle || "",       // opcional (mostra do lado)
          role_key: roleKey || ""              // mantemos também, se quiser estilizar
        }));
        // ordena por nome (mesmo comportamento anterior)
        mapped.sort((a,b) => String(a.name||"").localeCompare(String(b.name||""), "pt-BR"));
        return mapped;
      })
      .catch(() => []);
  }

  // Hidratação: quando há ID no hidden, busca o nome em:
  //   GET /people/api/get/?id=<pk> -> {id, text, subtitle}
  function fetchPersonById(id, signal){
    if (!id) return Promise.resolve(null);
    const u = new URL("/people/api/get/", window.location.origin);
    u.searchParams.set("id", String(id));
    return fetch(u.toString(), { credentials:"same-origin", signal, headers: {"X-Requested-With":"XMLHttpRequest"} })
      .then(r => r.ok ? r.json() : null)
      .catch(() => null);
  }

  // ======= Componente Combobox =======
  function attachCombo(wrapper){
    // Caso 1 (ideal): HTML já está assim:
    // <div class="combo" data-combo data-role="...">
    //   <input type="hidden" id="..._id" name="..._id">
    //   <input type="text"   id="..."    name="..."    class="input">
    //   <button type="button" class="combo-toggle"></button>
    // </div>
    //
    // Caso 2 (compat): wrapper vazio com data-txt/data-hid:
    // <div data-combo data-txt="#id_campo" data-hid="#id_campo_id" data-role="..."></div>

    const roleKey = wrapper.getAttribute("data-role") || null;

    // Tenta achar input/hidden dentro do wrapper
    let txt = wrapper.querySelector("input.input");
    let hid = wrapper.querySelector('input[type="hidden"]');
    let toggle = wrapper.querySelector(".combo-toggle");

    // Compat: se o wrapper vier vazio, puxa via seletor data-*
    if (!txt) {
      const txtSel = wrapper.getAttribute("data-txt");
      const hidSel = wrapper.getAttribute("data-hid");
      if (!(txtSel && hidSel)) return; // nada a fazer
      txt = document.querySelector(txtSel);
      hid = document.querySelector(hidSel);
      if (!(txt && hid)) return;       // seletor inválido
      txt.classList.add("input");
      // injeta estrutura visual mínima
      wrapper.classList.add("combo");
      wrapper.appendChild(hid);
      wrapper.appendChild(txt);
    }

    // Garante botão seta
    if (!toggle) {
      toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "combo-toggle";
      toggle.setAttribute("aria-haspopup", "listbox");
      toggle.setAttribute("aria-expanded", "false");
      wrapper.appendChild(toggle);
    }

    const { panel, q, list } = buildPanel(wrapper);

    let abortCtrl = null;
    let debounce = null;

    function open(){
      wrapper.classList.add("open");
      panel.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
      q.focus();
      doSearch(q.value.trim());
    }
    function close(){
      wrapper.classList.remove("open");
      panel.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
    }
    function select(el){
      if (!el) return;
      const name = el.getAttribute("data-name") || "";
      const id = el.getAttribute("data-id") || "";
      txt.value = name;
      if (hid) hid.value = id;
      close();
      txt.focus();
    }

    function doSearch(text){
      if (abortCtrl) abortCtrl.abort();
      abortCtrl = new AbortController();
      fetchPeople(text, roleKey, abortCtrl.signal).then(items=>{
        renderItems(list, items);
      });
    }

    // Eventos
    toggle.addEventListener("click", function(){
      if (panel.hidden) open(); else close();
    });

    // Ao digitar manualmente, limpamos o ID (evita mismatch nome↔ID)
    txt.addEventListener("input", function(){ if (hid) hid.value = ""; });

    // Hidrata nome no input quando já houver ID (edição)
    if (hid && hid.value && !txt.value){
      const ctrl = new AbortController();
      fetchPersonById(hid.value, ctrl.signal).then(data => {
        if (data && data.text) {
          txt.value = data.text;
        }
      });
    }

    q.addEventListener("input", function(){
      const text = (this.value||"").trim();
      clearTimeout(debounce);
      debounce = setTimeout(()=> doSearch(text), 150);
    });

    list.addEventListener("click", function(e){
      const li = e.target.closest(".combo-option");
      if (li) select(li);
    });

    wrapper.addEventListener("keydown", function(e){
      if (panel.hidden) return;
      if (e.key === "ArrowDown"){ e.preventDefault(); moveActive(list, +1); }
      else if (e.key === "ArrowUp"){ e.preventDefault(); moveActive(list, -1); }
      else if (e.key === "Enter"){ e.preventDefault(); select(getActiveOption(list)); }
      else if (e.key === "Escape"){ e.preventDefault(); close(); }
    });

    document.addEventListener("click", function(e){
      if (!wrapper.contains(e.target)) close();
    });
  }

  // ======= Boot =======
  document.addEventListener("DOMContentLoaded", function(){
    // Atacha em todos os wrappers: .combo[data-combo] ou [data-combo][data-txt][data-hid]
    $all('.combo[data-combo], [data-combo][data-txt][data-hid]').forEach(attachCombo);
  });
})();
