const toggle = document.getElementById("themeToggle");
const root = document.documentElement;

function sync() {
  const isLight = root.getAttribute("data-theme") === "light";
  toggle.textContent = isLight ? "☀️" : "🌙";
}

const saved = localStorage.getItem("glam-theme");
if (saved) root.setAttribute("data-theme", saved);
sync();

toggle.addEventListener("click", () => {
  const next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
  root.setAttribute("data-theme", next);
  localStorage.setItem("glam-theme", next);
  sync();
});
