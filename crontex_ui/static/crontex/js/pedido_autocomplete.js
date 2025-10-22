(function(){
  function setupAuto(txtId, hidId, datalistId, roleKeyOrNull){
    var $txt = document.getElementById(txtId);
    var $hid = document.getElementById(hidId);
    var $dl  = document.getElementById(datalistId);
    if (!$txt || !$hid || !$dl) return;

    // liga o datalist no input já renderizado
    $txt.setAttribute('list', datalistId);
    $txt.setAttribute('autocomplete', 'off');

    var last = "";
    $txt.addEventListener('input', function(){
      var q = ($txt.value || '').trim();
      $hid.value = "";            // texto mudou → zera ID
      if (q.length < 2 || q === last) return;
      last = q;

      var base = "/people/collaborators/search/";
      var qs = "q=" + encodeURIComponent(q);
      if (roleKeyOrNull) qs += "&role=" + encodeURIComponent(roleKeyOrNull);

      fetch(base + "?" + qs, {credentials: 'same-origin'})
        .then(function(resp){ if (!resp.ok) return null; return resp.json(); })
        .then(function(data){
          if (!data) return;
          $dl.innerHTML = "";
          (data.items || []).forEach(function(item){
            var opt = document.createElement('option');
            opt.value = item.name;
            opt.setAttribute('data-id', item.id);
            $dl.appendChild(opt);
          });
        })
        .catch(function(){ /* segue como texto livre */ });
    });

    $txt.addEventListener('change', function(){
      var opts = Array.prototype.slice.call(($dl.options || []), 0);
      var found = opts.find(function(o){ return o.value === $txt.value; });
      $hid.value = found ? (found.getAttribute('data-id') || "") : "";
    });
  }

  // Hooks da aba PEDIDO
  setupAuto('id_pedido_requisitante', 'id_pedido_requisitante_id', 'dl_requisitante', null);
  setupAuto('id_pedido_cliente',      'id_pedido_cliente_id',      'dl_cliente',      null);
})();
