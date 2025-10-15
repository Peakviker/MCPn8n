# n8n MCP Server

Этот репозиторий содержит реализацию сервера **Model Context Protocol (MCP)** на базе FastAPI, который позволяет инструментам ChatGPT управлять рабочими процессами n8n через официальный REST API.

## Возможности

- SSE-интерфейс `/mcp/request` для взаимодействия в формате MCP.
- Поддерживаемые методы:
  - `list_workflows` — `GET /rest/workflows`
  - `create_workflow` — `POST /rest/workflows`
  - `update_workflow` — `PATCH /rest/workflows/{id}`
  - `delete_workflow` — `DELETE /rest/workflows/{id}`
  - `run_workflow` — `POST /rest/workflows/run`
  - `get_execution_status` — `GET /rest/executions/{id}`
- Асинхронный HTTP-клиент `httpx.AsyncClient` с поддержкой API-ключей n8n.
- Pydantic-схемы для строгой валидации MCP-запросов и ответов.
- Логирование входящих запросов и обращений к n8n.

## Требования

- Python 3.10 или новее.
- Запущенный экземпляр n8n с доступом по HTTP и включённым REST API.
- API-токен n8n с правами на чтение и изменение workflow.

## Установка и запуск

1. Клонируйте репозиторий и перейдите в директорию проекта:

   ```bash
   git clone https://github.com/Peakviker/MCPn8n.git
   cd MCPn8n
   ```

2. Создайте виртуальное окружение и установите зависимости:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install fastapi uvicorn[standard] sse-starlette httpx python-dotenv
   ```

3. Скопируйте пример конфигурации и задайте переменные окружения:

   ```bash
   cp .env.example .env
   # отредактируйте значения по необходимости
   ```

   Доступные параметры:

   | Переменная          | Описание                                     | Значение по умолчанию |
   | ------------------- | -------------------------------------------- | --------------------- |
   | `N8N_URL`           | Базовый URL REST API n8n                     | `http://localhost:5678/api/v1/` |
   | `N8N_API_KEY`       | API-токен n8n                                | пусто (анонимный доступ) |
   | `N8N_TIMEOUT`       | Таймаут HTTP-запросов в секундах             | `30.0` |

4. Запустите сервер MCP:

   ```bash
   uvicorn mcp_server:app --reload --port 8080
   ```

5. Проверьте, что сервер отвечает:

   ```bash
   curl http://localhost:8080/healthz
   curl http://localhost:8080/mcp/discover
   ```

## Использование MCP-инструментов

`POST /mcp/request` принимает JSON вида:

```json
{
  "id": "<уникальный идентификатор запроса>",
  "method": "list_workflows",
  "params": { "limit": 20 }
}
```

Ответ поступает по SSE в виде событий `result` или `error`. Поле `result` содержит MCP-структуру `json_schema` с данными, полученными от n8n.

### Пример запуска workflow

```bash
curl -N \
  -H "Content-Type: application/json" \
  -X POST http://localhost:8080/mcp/request \
  -d '{
    "id": "demo-run",
    "method": "run_workflow",
    "params": {
      "workflow_id": "123",
      "payload": {
        "runData": {
          "HTTP Trigger": [[ { "json": { "foo": "bar" } } ]]
        },
        "startNodes": ["HTTP Trigger"],
        "destinationNode": "Respond to Webhook"
      }
    }
  }'
```

Чтобы отслеживать выполнение, используйте метод `get_execution_status` с идентификатором, возвращённым n8n при запуске.

## Разработка

- Все основные настройки находятся в `mcp_server.py`.
- При добавлении новых методов обновляйте словарь `METHOD_PARAM_MODELS` и класс клиента `N8nClient`.
- Логирование настроено на уровень `INFO`. При необходимости измените уровень, передав значение через `logging.basicConfig`.

## Лицензия

Добавьте файл LICENSE при необходимости.
