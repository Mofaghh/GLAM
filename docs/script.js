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
    if (headerToggle) headerToggle.textContent = theme === 'light' ? '☀️' : '🌙';
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
})();
