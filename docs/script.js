(function () {
  var root = document.documentElement;
  var buttons = document.querySelectorAll('.mk-theme-btn');
  var headerToggle = document.getElementById('themeToggle');

  function apply(theme) {
    if (theme === 'light') {
      root.setAttribute('data-theme', 'light');
      root.style.backgroundColor = 'var(--m-bg, #F2F3F1)';
    } else {
      root.setAttribute('data-theme', 'dark');
      root.style.backgroundColor = 'var(--m-bg, #161718)';
    }
    buttons.forEach(function (b) {
      b.setAttribute('aria-checked', b.getAttribute('data-theme-set') === theme ? 'true' : 'false');
    });
    if (headerToggle) {
      headerToggle.innerHTML = theme === 'light'
        ? '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"></path></svg>'
        : '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"></path></svg>';
    }
  }

  var saved = null;
  try { saved = localStorage.getItem('m-theme'); } catch (e) {}
  if (!saved || saved !== 'light') saved = 'dark';
  apply(saved);

  function setTheme(theme) {
    apply(theme);
    try { localStorage.setItem('m-theme', theme); } catch (e) {}
  }

  buttons.forEach(function (b) {
    b.addEventListener('click', function () { setTheme(b.getAttribute('data-theme-set')); });
  });
  if (headerToggle) {
    headerToggle.addEventListener('click', function () {
      setTheme(root.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
    });
  }

  // Cost calculator
  var calcBase = document.querySelectorAll('[data-calc-base]');
  var calcAdds = document.querySelectorAll('[data-calc-add]');
  var calcTotal = document.getElementById('calcTotal');
  var calcOrder = document.getElementById('calcOrder');

  function calcLoad() {
    try {
      var s = JSON.parse(localStorage.getItem('glam-calc'));
      if (s && s.base) {
        calcBase.forEach(function (b) {
          var on = b.getAttribute('data-id') === s.base;
          b.classList.toggle('is-active', on);
          b.setAttribute('aria-checked', on ? 'true' : 'false');
        });
      }
      if (s && s.adds) {
        calcAdds.forEach(function (b) {
          var on = s.adds.indexOf(b.getAttribute('data-id')) !== -1;
          b.setAttribute('aria-pressed', on ? 'true' : 'false');
          b.classList.toggle('is-active', on);
        });
      }
    } catch (e) {}
  }

  function calcSave() {
    var base = null, adds = [];
    calcBase.forEach(function (b) { if (b.classList.contains('is-active')) base = b.getAttribute('data-id'); });
    calcAdds.forEach(function (b) { if (b.getAttribute('aria-pressed') === 'true') adds.push(b.getAttribute('data-id')); });
    try { localStorage.setItem('glam-calc', JSON.stringify({ base: base, adds: adds })); } catch (e) {}
  }

  function calcUpdate() {
    var total = 0, base = null, adds = [];
    calcBase.forEach(function (b) {
      if (b.classList.contains('is-active')) { total += parseInt(b.getAttribute('data-price'), 10); base = b.getAttribute('data-id'); }
    });
    calcAdds.forEach(function (b) {
      if (b.getAttribute('aria-pressed') === 'true') { total += parseInt(b.getAttribute('data-price'), 10); adds.push(b.getAttribute('data-id')); }
    });
    if (calcTotal) calcTotal.textContent = total + ' ₽';
    if (calcOrder) calcOrder.href = 'https://t.me/GLAAAM_BOT?start=calc_' + (base || 'premium') + (adds.length ? '_' + adds.join('_') : '');
    calcSave();
  }

  calcBase.forEach(function (b) {
    b.addEventListener('click', function () {
      calcBase.forEach(function (x) { x.classList.remove('is-active'); x.setAttribute('aria-checked', 'false'); });
      b.classList.add('is-active'); b.setAttribute('aria-checked', 'true');
      calcUpdate();
    });
  });
  calcAdds.forEach(function (b) {
    b.addEventListener('click', function () {
      var on = b.getAttribute('aria-pressed') === 'true';
      b.setAttribute('aria-pressed', on ? 'false' : 'true');
      b.classList.toggle('is-active', !on);
      calcUpdate();
    });
  });
  calcLoad();
  calcUpdate();

  // Distance-based card hover: card near cursor comes forward, far recedes
  function bindGridDistance(grid) {
    var cards = grid.querySelectorAll('.product-card');
    if (!cards.length) return;
    function onMove(e) {
      var rect = grid.getBoundingClientRect();
      var gx = e.clientX - rect.left, gy = e.clientY - rect.top;
      cards.forEach(function (c) {
        var cr = c.getBoundingClientRect();
        var cx = cr.left - rect.left + cr.width / 2;
        var cy = cr.top - rect.top + cr.height / 2;
        var d = Math.hypot(gx - cx, gy - cy);
        var f = Math.max(0, 1 - d / (rect.width * 0.85 + rect.height * 0.45));
        var scale = 0.9 + 0.16 * f;
        c.style.transform = 'translateY(' + (-10 * f).toFixed(1) + 'px) scale(' + scale.toFixed(3) + ')';
        c.style.opacity = (0.45 + 0.55 * f).toFixed(3);
        c.style.filter = 'brightness(' + (0.6 + 0.4 * f).toFixed(3) + ')';
        c.style.zIndex = f > 0.6 ? 3 : '';
      });
    }
    function reset() {
      cards.forEach(function (c) { c.style.transform = ''; c.style.opacity = ''; c.style.filter = ''; c.style.zIndex = ''; });
    }
    grid.addEventListener('mousemove', onMove);
    grid.addEventListener('mouseleave', reset);
  }
  document.querySelectorAll('.team').forEach(bindGridDistance);
})();
