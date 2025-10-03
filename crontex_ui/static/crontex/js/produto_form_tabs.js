/* Tabs tipo navegador + altura estável + add dinâmico + UID auto */
(function () {
  function uuidv4() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
      (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
  }

  function normalizePanelsHeight(container, panels) {
    let maxH = 0;
    panels.forEach(p => {
      const prev = p.style.display;
      if (p.hidden) { p.style.display = "block"; }
      maxH = Math.max(maxH, p.scrollHeight);
      p.style.display = prev;
    });
    container.style.minHeight = maxH + "px";
  }

  document.addEventListener("DOMContentLoaded", function () {
    // UID auto
    const uidInput = document.querySelector('input[name="form_uid"]');
    if (uidInput && !uidInput.value) uidInput.value = uuidv4();

    // Tabs
    const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
    const panels = Array.from(document.querySelectorAll('[role="tabpanel"]'));
    const panelsWrap = document.getElementById("produto-tab-panels");
    if (!tabs.length || !panels.length || !panelsWrap) return;

    function activate(name) {
      tabs.forEach(t => {
        const isActive = t.dataset.tab === name;
        t.classList.toggle("is-active", isActive);
        t.setAttribute("aria-selected", isActive ? "true" : "false");
        t.setAttribute("tabindex", isActive ? "0" : "-1");
      });
      panels.forEach(p => {
        const isActive = p.dataset.tab === name;
        p.classList.toggle("is-active", isActive);
        p.hidden = !isActive;
      });
      normalizePanelsHeight(panelsWrap, panels);
    }

    const initial = (tabs.find(t => t.classList.contains("is-active")) || tabs[0]).dataset.tab;
    activate(initial);

    tabs.forEach(t => t.addEventListener("click", () => activate(t.dataset.tab)));
    tabs.forEach(t => t.addEventListener("keydown", e => {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      e.preventDefault();
      const idx = tabs.indexOf(t);
      const next = e.key === "ArrowRight" ? (idx + 1) % tabs.length : (idx - 1 + tabs.length) % tabs.length;
      tabs[next].focus();
      activate(tabs[next].dataset.tab);
    }));
    window.addEventListener("resize", () => normalizePanelsHeight(panelsWrap, panels));

    // Add dinâmico
    function wireDynamicAdd(scope) {
      scope.querySelectorAll("[data-add]").forEach(btn => {
        btn.addEventListener("click", () => {
          const target = scope.querySelector(btn.dataset.add);
          const tpl = scope.querySelector(btn.dataset.template);
          if (!target || !tpl) return;
          const clone = tpl.content.cloneNode(true);
          const idx = target.querySelectorAll("[data-row]").length + 1;
          clone.querySelectorAll("[name]").forEach(inp => {
            const base = inp.getAttribute("name");
            inp.setAttribute("name", base.replace("__idx__", String(idx)));
            inp.classList.add("input");
          });
          target.appendChild(clone);
          normalizePanelsHeight(panelsWrap, panels);
        });
      });
    }

    panels.forEach(p => wireDynamicAdd(p));
  });
})();
