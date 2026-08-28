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
})();
