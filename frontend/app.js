const form = document.querySelector("#analyzeForm");
const result = document.querySelector("#result");
const statusEl = document.querySelector("#status");
const emptyState = document.querySelector("#emptyState");
const fillDemo = document.querySelector("#fillDemo");

const demo = {
  business_name: "Стоматология в Москве",
  industry: "Стоматология / медицинские услуги",
  product:
    "Имплантация зубов под ключ: консультация хирурга, 3D-диагностика, установка импланта, временная коронка, рассрочка и гарантия.",
  audience:
    "Мужчины и женщины 35-65 лет, которые потеряли один или несколько зубов, боятся боли, не понимают итоговую цену и сравнивают клиники по доверию.",
  location: "Москва и ближайшее Подмосковье",
  budget: "150 000 ₽ в месяц",
  goal: "получить лиды",
};

fillDemo.addEventListener("click", () => {
  Object.entries(demo).forEach(([key, value]) => {
    const field = form.elements[key];
    if (field) field.value = value;
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(form).entries());

  setLoading(true);
  try {
    const response = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "API request failed");
    }

    renderResult(data);
    statusEl.textContent = `Готово · cost ${data.vibe_meta?.cost ?? "n/a"} ₽`;
  } catch (error) {
    result.classList.remove("hidden");
    emptyState.classList.add("hidden");
    result.innerHTML = `<div class="error"><b>Ошибка запроса</b><p>${escapeHtml(error.message)}</p></div>`;
    statusEl.textContent = "Ошибка";
  } finally {
    setLoading(false);
  }
});

function setLoading(isLoading) {
  form.querySelector(".primary").disabled = isLoading;
  statusEl.textContent = isLoading ? "Агент анализирует..." : statusEl.textContent;
}

function renderResult(data) {
  emptyState.classList.add("hidden");
  result.classList.remove("hidden");
  result.innerHTML = `
    ${section("Анализ бизнеса", data.business_analysis)}
    ${section("Целевая аудитория", data.target_audience)}
    ${section("Маркетинговые гипотезы", data.marketing_hypotheses)}
    ${section("Варианты офферов", data.offer_variants)}
    ${section("Идеи креативов", data.creative_ideas)}
    ${section("Рекомендованные действия", data.recommended_actions)}
    <details class="meta">
      <summary>Технические данные Vibe API</summary>
      <pre>${escapeHtml(JSON.stringify({ estimate: data.estimate, vibe_meta: data.vibe_meta }, null, 2))}</pre>
    </details>
  `;
}

function section(title, content) {
  if (Array.isArray(content)) {
    return `
      <article class="result-card">
        <h3>${title}</h3>
        <ul>${content.map((item) => `<li>${formatItem(item)}</li>`).join("")}</ul>
      </article>
    `;
  }

  return `
    <article class="result-card">
      <h3>${title}</h3>
      <p>${escapeHtml(content || "Нет данных")}</p>
    </article>
  `;
}

function formatItem(item) {
  if (typeof item === "string") return escapeHtml(item);
  return `<pre>${escapeHtml(JSON.stringify(item, null, 2))}</pre>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
