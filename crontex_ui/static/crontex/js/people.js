// crontex_ui/static/crontex/js/people.js
(function () {
  const onlyDigits = (s) => (s || "").replace(/\D+/g, "");
  const isCep = (v) => /^\d{5}-?\d{3}$/.test(v);

  const applyPhoneMask = (input) => {
    let d = onlyDigits(input.value);
    const hasDDI = input.value.trim().startsWith("+");
    if (hasDDI) { input.value = "+" + d; return; }
    if (d.length <= 10) {
      input.value = d.replace(/^(\d{2})(\d)/, "($1) $2").replace(/(\d{4})(\d{1,4})$/, "$1-$2");
    } else {
      input.value = d.replace(/^(\d{2})(\d)/, "($1) $2").replace(/(\d{5})(\d{1,4})$/, "$1-$2");
    }
  };
  const applyCepMask = (input) => {
    let d = onlyDigits(input.value).slice(0, 8);
    input.value = d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  };
  async function fetchViaCEP(cep) {
    const clean = onlyDigits(cep);
    if (clean.length !== 8) return null;
    try {
      const r = await fetch(`https://viacep.com.br/ws/${clean}/json/`);
      if (!r.ok) return null;
      const j = await r.json();
      if (j.erro) return null;
      return { cep: j.cep||"", street: j.logradouro||"", district: j.bairro||"", city: j.localidade||"", uf: j.uf||"" };
    } catch { return null; }
  }

  const form = document.querySelector('form[method="post"]');
  if (!form) return;

  const prefix = "addr";
  const formsDiv = document.getElementById("addr-forms");
  const addBtn = document.getElementById("addr-add");
  const totalForms = document.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`);

  if (addBtn && formsDiv && totalForms) {
    addBtn.addEventListener("click", function () {
      const idx = parseInt(totalForms.value, 10);
      const block = document.createElement("div");
      block.className = "card subtle addr-item";
      block.dataset.index = String(idx);
      block.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-6 gap-2">
          <div class="form-field md:col-span-2"><label>Rótulo</label><input type="text" name="${prefix}-${idx}-label" class="input"></div>
          <div class="form-field"><label>CEP</label><input type="text" name="${prefix}-${idx}-cep" class="input" placeholder="00000-000"></div>
          <div class="form-field md:col-span-3"><label>Logradouro</label><input type="text" name="${prefix}-${idx}-street" class="input"></div>
          <div class="form-field"><label>Número</label><input type="text" name="${prefix}-${idx}-number" class="input"></div>
          <div class="form-field md:col-span-2"><label>Complemento</label><input type="text" name="${prefix}-${idx}-complement" class="input"></div>
          <div class="form-field"><label>Bairro</label><input type="text" name="${prefix}-${idx}-district" class="input"></div>
          <div class="form-field"><label>Cidade</label><input type="text" name="${prefix}-${idx}-city" class="input"></div>
          <div class="form-field"><label>UF</label><input type="text" name="${prefix}-${idx}-uf" class="input" maxlength="2"></div>
          <div class="form-field"><label>País</label><input type="text" name="${prefix}-${idx}-country" class="input" value="Brasil"></div>
        </div>`.trim();
      formsDiv.appendChild(block);
      totalForms.value = String(idx + 1);
    });
  }

  form.addEventListener("input", (ev) => {
    const el = ev.target;
    if (!(el instanceof HTMLInputElement)) return;
    if (el.name === "phone" || el.name === "phone_alt") applyPhoneMask(el);
    if (/-cep$/.test(el.name)) applyCepMask(el);
    if (/-uf$/.test(el.name)) el.value = el.value.toUpperCase().replace(/[^A-Z]/g, "").slice(0, 2);
  });

  form.addEventListener("blur", async (ev) => {
    const el = ev.target;
    if (!(el instanceof HTMLInputElement)) return;
    if (!/-cep$/.test(el.name)) return;

    applyCepMask(el);
    if (!isCep(el.value)) return;

    const box = el.closest(".addr-item") || el.closest(".grid, .card");
    const data = await fetchViaCEP(el.value);
    if (!data || !box) return;

    const byName = (suffix) => box.querySelector(`input[name$="${suffix}"]`);
    const street = byName("-street");
    const district = byName("-district");
    const city = byName("-city");
    const uf = byName("-uf");

    if (street && !street.value) street.value = data.street;
    if (district && !district.value) district.value = data.district;
    if (city && !city.value) city.value = data.city;
    if (uf && !uf.value) uf.value = data.uf;
  }, true);
})();
