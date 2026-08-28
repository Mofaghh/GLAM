const ENDPOINT = "https://glam-0j54.onrender.com/api/order";

const form = document.getElementById("orderForm");
const status = document.getElementById("formStatus");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  status.className = "form-status";
  status.textContent = "Отправляем заявку...";

  const payload = {
    name: form.name.value.trim(),
    telegram: form.telegram.value.trim().replace(/^@/, ""),
    service: form.service.value,
    description: form.description.value.trim(),
    reference: form.reference.value.trim(),
  };

  if (!payload.name || !payload.telegram || !payload.description) {
    status.className = "form-status err";
    status.textContent = "Заполните имя, Telegram и описание.";
    return;
  }

  try {
    const res = await fetch(ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("bad status");
    status.className = "form-status ok";
    status.textContent = "Заявка отправлена! Художник свяжется с тобой в Telegram.";
    form.reset();
  } catch (err) {
    status.className = "form-status err";
    status.textContent =
      "Не удалось отправить автоматически. Напиши в бота: t.me/GLAAAM_BOT";
  }
});
