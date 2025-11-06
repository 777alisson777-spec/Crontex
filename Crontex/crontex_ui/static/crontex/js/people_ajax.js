// crontex_ui/static/crontex/js/people_ajax.js
// Autocomplete para campos de pessoa (Contact) no padrão TEXT + HIDDEN ID.
// Data-attributes no input de texto:
//   data-ac-url="/people/api/search/"
//   data-ac-get-url="/people/api/get/"
//   data-ac-target="#id_<campo>_id"
(function () {
  const DEBOUNCE_MS = 250;

  function debounce(fn, wait) {
    let t = null;
    return function (...args) {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(this, args), wait);
    };
  }

  function createDropdown(anchor) {
    const dd = document.createElement('div');
    dd.className = 'ac-dropdown';
    dd.style.position = 'absolute';
    dd.style.zIndex = 1000;
    dd.style.background = '#fff';
    dd.style.border = '1px solid #ddd';
    dd.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
    dd.style.maxHeight = '240px';
    dd.style.overflowY = 'auto';
    dd.style.borderRadius = '6px';
    document.body.appendChild(dd);
    return dd;
  }

  function positionDropdown(dd, anchor) {
    const r = anchor.getBoundingClientRect();
    dd.style.left = (window.scrollX + r.left) + 'px';
    dd.style.top  = (window.scrollY + r.bottom + 4) + 'px';
    dd.style.minWidth = r.width + 'px';
  }

  function closeDropdown(dd) {
    if (dd && dd.parentNode) dd.parentNode.removeChild(dd);
  }

  async function fetchJSON(url) {
    const resp = await fetch(url, {headers: {"X-Requested-With": "XMLHttpRequest"}});
    if (!resp.ok) return null;
    return await resp.json();
  }

  async function search(url, q, page) {
    const u = new URL(url, window.location.origin);
    if (q) u.searchParams.set('q', q);
    u.searchParams.set('page', page || 1);
    return await fetchJSON(u.toString()) || {results: [], pagination: {more: false}};
  }

  async function getById(url, id) {
    if (!id) return null;
    const u = new URL(url, window.location.origin);
    u.searchParams.set('id', id);
    return await fetchJSON(u.toString());
  }

  function renderItem(item, onSelect) {
    const el = document.createElement('div');
    el.className = 'ac-item';
    el.style.padding = '8px 10px';
    el.style.cursor = 'pointer';
    el.innerHTML = `
      <div style="font-weight:600; line-height:1.2">${item.text}</div>
      ${item.subtitle ? `<div style="font-size:12px;color:#666">${item.subtitle}</div>` : ''}
    `;
    el.addEventListener('mousedown', (ev) => {
      ev.preventDefault();
      onSelect(item);
    });
    el.addEventListener('mouseenter', () => { el.style.background = '#f7f7f7'; });
    el.addEventListener('mouseleave', () => { el.style.background = 'transparent'; });
    return el;
  }

  function attach(input) {
    const url = input.dataset.acUrl;
    const getUrl = input.dataset.acGetUrl;
    const targetSel = input.dataset.acTarget;
    const target = document.querySelector(targetSel);
    if (!url || !getUrl || !target) return;

    let dd = null;
    let currQuery = '';
    let currPage = 1;

    // Hidrata rótulo se hidden já tem ID (edição)
    if (target.value && !input.value) {
      getById(getUrl, target.value).then((data) => {
        if (data && data.text) input.value = data.text;
      });
    }

    const runSearch = debounce(async function () {
      currQuery = input.value.trim();
      currPage = 1;
      const data = await search(url, currQuery, currPage);

      if (dd) closeDropdown(dd);
      dd = createDropdown(input);
      positionDropdown(dd, input);

      (data.results || []).forEach(item => {
        dd.appendChild(renderItem(item, (sel) => {
          input.value = sel.text;
          target.value = sel.id;
          closeDropdown(dd);
        }));
      });

      if (data.pagination && data.pagination.more) {
        const more = document.createElement('div');
        more.textContent = 'Carregar mais…';
        more.style.padding = '8px 10px';
        more.style.textAlign = 'center';
        more.style.cursor = 'pointer';
        more.style.borderTop = '1px solid #eee';
        more.addEventListener('mousedown', async (ev) => {
          ev.preventDefault();
          currPage += 1;
          const nx = await search(url, currQuery, currPage);
          (nx.results || []).forEach(item => {
            dd.insertBefore(renderItem(item, (sel) => {
              input.value = sel.text;
              target.value = sel.id;
              closeDropdown(dd);
            }), more);
          });
          if (!(nx.pagination && nx.pagination.more)) {
            more.remove();
          }
        });
        dd.appendChild(more);
      }
    }, DEBOUNCE_MS);

    input.addEventListener('input', runSearch);
    input.addEventListener('focus', runSearch);
    window.addEventListener('resize', () => dd && positionDropdown(dd, input));
    window.addEventListener('scroll', () => dd && positionDropdown(dd, input));
    document.addEventListener('click', (ev) => {
      if (dd && ev.target !== input && !dd.contains(ev.target)) closeDropdown(dd);
    });
    input.addEventListener('change', () => {
      if (!input.value.trim()) target.value = '';
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.js-contact-ac').forEach(attach);
  });
})();
