(function () {
  // Cores alinhadas ao logo:
  // Navy #0B3A6E (fundo suave 12.5%), Laranja #F59E0B (fill)
  var form = document.querySelector('form'); // o form do produto
  if (!form) return;

  var barWrap = document.getElementById('ai-progress');
  var barFill = document.getElementById('ai-progress-fill');
  if (!barWrap || !barFill) return;

  // Evita múltiplos submits
  var isSubmitting = false;

  // Animação indeterminada simples + lock do submit padrão
  form.addEventListener('submit', function (ev) {
    if (isSubmitting) return; // deixa passar o segundo (redirect)
    isSubmitting = true;

    // mostra barra
    barWrap.style.display = 'flex';

    // animação: vai 0→85% em loop leve até o servidor responder
    var pct = 0;
    var timer = setInterval(function () {
      // acelera no começo, desacelera perto de 85
      pct += Math.max(0.5, (85 - pct) * 0.07);
      if (pct > 85) pct = 85;
      barFill.style.width = pct.toFixed(1) + '%';
    }, 120);

    // não cancela o submit; apenas deixa visual rodando
    // o servidor só responde quando IA + fallback concluírem
    // quando a página carregar a resposta, esse JS sai de cena
    // (novo documento). Em SPA não precisaríamos disso.

    // segurança: depois de 2.5s, adiciona pequena oscilação
    setTimeout(function () {
      var dir = 1;
      var wobble = setInterval(function () {
        if (!isSubmitting) return clearInterval(wobble);
        var now = parseFloat(barFill.style.width) || pct;
        var delta = dir * 0.6;
        var next = Math.max(60, Math.min(88, now + delta));
        if (next >= 88 || next <= 60) dir = -dir;
        barFill.style.width = next.toFixed(1) + '%';
      }, 300);
    }, 2500);

    // Quando a resposta voltar (nova página), os timers morrem naturalmente.
  });

  // Caso queira também mostrar em Update (edição) sem recarregar, poderíamos escutar fetch/XHR,
  // mas aqui o fluxo é full-page, então mantemos simples e robusto.
})();
