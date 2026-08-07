# AI Marketing Analyst Agent

MVP-сервис для демонстрации интеграции с VibeMarketolog Agent API.

Пользователь вводит данные о бизнесе и маркетинговой задаче. Backend собирает качественный prompt, делает бесплатную оценку стоимости через `/generate/estimate`, отправляет запрос в VibeMarketolog Agent API через `/generate`, получает структурированный JSON и показывает результат в web-интерфейсе.

## Зачем нужен агент

Такой агент помогает быстро получить первую маркетинговую стратегию для малого и среднего бизнеса:

- анализ бизнеса и продукта;
- сегменты целевой аудитории;
- рекламные гипотезы;
- варианты офферов;
- идеи рекламных креативов;
- план следующих действий.

## Архитектура

```text
Frontend form
    ↓ POST /analyze
FastAPI backend
    ↓ build prompt
VibeMarketolog Agent API /generate/estimate
    ↓ free preflight
VibeMarketolog Agent API /generate
    ↓ text model result
Structured JSON response
    ↓
Frontend result cards
```

## Структура проекта

```text
/
├── backend/
│   ├── main.py
│   ├── vibe_client.py
│   ├── prompts.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── n8n/
│   └── vibemarketolog_marketing_analyst_workflow.json
├── .env.example
└── README.md
```

## Как запустить

1. Создать виртуальное окружение:

```bash
python -m venv .venv
```

2. Активировать окружение:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

3. Установить зависимости:

```bash
pip install -r backend/requirements.txt
```

4. Создать `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

5. Вставить API-ключ:

```env
SPA_ACCESS_TOKEN=your_spa_access_token_here
```

6. Запустить сервер:

```bash
uvicorn backend.main:app --reload
```

7. Открыть:

```text
http://127.0.0.1:8000
```

## Пример запроса

```json
{
  "business_name": "Стоматология в Москве",
  "industry": "Стоматология / медицинские услуги",
  "product": "Имплантация зубов под ключ: консультация хирурга, 3D-диагностика, установка импланта, временная коронка, рассрочка и гарантия.",
  "audience": "Мужчины и женщины 35-65 лет, которые потеряли один или несколько зубов, боятся боли, не понимают итоговую цену и сравнивают клиники по доверию.",
  "location": "Москва и ближайшее Подмосковье",
  "budget": "150 000 ₽ в месяц",
  "goal": "получить лиды"
}
```

## Live verification

To prove that the MVP made real calls to VibeMarketolog Agent API, use:

```bash
python backend/run_live_demo.py --repeat 2
```

The script performs:

```text
/generate/estimate -> /generate -> save result artifact
```

After launch, `results/` contains:

- `live_run_*.json` with request, estimate, generation metadata and structured result;
- `LIVE_RUNS.md` with generation IDs, model, cost and balance_after.

Current saved live runs are available in [esults/LIVE_RUNS.md](results/LIVE_RUNS.md).

Secrets are not stored in the repository.

## n8n workflow

В папке `n8n/` лежит отдельный workflow для импорта в n8n.

Логика:

```text
Webhook
  → Code: Build Vibe Request
  → HTTP: Vibe Estimate Cost
  → HTTP: Vibe Generate Analysis
  → Code: Parse Vibe JSON Result
  → Respond to Webhook
```

В HTTP-ноды нужно вставить API-ключ VibeMarketolog:

```text
Authorization: Bearer PASTE_VIBE_API_KEY_HERE
```

## Что показывает MVP

- работа с внешним Agent API;
- prompt engineering под бизнес-задачу;
- preflight-оценка стоимости до платного вызова;
- обработка ошибок API;
- структурированный JSON-ответ;
- простой frontend для демонстрации результата;
- n8n workflow как no-code/automation вариант той же логики.

