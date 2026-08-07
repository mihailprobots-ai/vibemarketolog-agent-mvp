const form = document.querySelector("#analyzeForm");
const result = document.querySelector("#result");
const emptyState = document.querySelector("#emptyState");
const statusEl = document.querySelector("#status");
const fillDemo = document.querySelector("#fillDemo");

const demoPayload = {
  business_name: "Стоматология в Москве",
  industry: "Стоматология / медицинские услуги",
  product: "Имплантация зубов под ключ: консультация хирурга, 3D-диагностика, установка импланта, временная коронка, рассрочка и гарантия.",
  audience: "Мужчины и женщины 35-65 лет, которые потеряли один или несколько зубов, боятся боли, не понимают итоговую цену и сравнивают клиники по доверию.",
  location: "Москва и ближайшее Подмосковье",
  budget: "150 000 ₽ в месяц",
  goal: "получить лиды",
};

fillDemo.addEventListener("click", () => {
  for (const [key, value] of Object.entries(demoPayload)) {
    const field = form.elements[key];
    if (field) field.value = value;
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(form).entries());

  statusEl.textContent = "Запрос к агенту...";
  result.classList.add("hidden");
  emptyState.classList.remove("hidden");

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || data.error || "API request failed");
    }

    renderResult(data);
    statusEl.textContent = `Готово · cost ${data.vibe_meta?.cost ?? "n/a"} ₽`;
  } catch (error) {
    result.classList.remove("hidden");
    emptyState.classList.add("hidden");
    result.innerHTML = `<div class="error"><b>Ошибка запроса</b><p>${escapeHtml(error.message)}</p></div>`;
    statusEl.textContent = "Ошибка";
  }
});

function renderResult(data) {
  emptyState.classList.add("hidden");
  result.classList.remove("hidden");
  result.innerHTML = `
    <article class="result-card wide">
      <p class="kicker">Анализ бизнеса</p>
      <p>${escapeHtml(data.business_analysis)}</p>
      ${renderMeta(data)}
    </article>
    ${renderList("Целевая аудитория", data.target_audience)}
    ${renderList("Рекламные гипотезы", data.marketing_hypotheses)}
    ${renderList("Офферы", data.offer_variants)}
    ${renderList("Идеи креативов", data.creative_ideas)}
    ${renderList("Следующие действия", data.recommended_actions)}
  `;
}

function renderList(title, items = []) {
  return `
    <article class="result-card">
      <p class="kicker">${escapeHtml(title)}</p>
      <ul>${items.map((item) => `<li>${escapeHtml(String(item))}</li>`).join("")}</ul>
    </article>
  `;
}

function renderMeta(data) {
  if (!data.vibe_meta) return "";
  const meta = data.vibe_meta;
  return `
    <div class="meta">
      <span>generation_id: ${escapeHtml(meta.generation_id ?? "n/a")}</span>
      <span>model: ${escapeHtml(meta.model ?? "n/a")}</span>
      <span>balance: ${escapeHtml(meta.balance_after ?? "n/a")}</span>
    </div>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
