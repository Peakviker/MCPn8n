# MCPn8n

MCPn8n — шаблонный репозиторий для интеграций и автоматизаций на базе n8n. Этот README создаёт основу с инструкциями по установке, запуску, разработке и вкладу. Заполните разделы проектной информацией и настройками по мере необходимости.

## Описание

MCPn8n предназначен для быстрой настройки рабочих процессов (workflows) и кастомных узлов (nodes) для n8n. Репозиторий содержит примеры, конфигурации и инструкции по локальной разработке.

> Важно: отредактируйте этот файл, чтобы добавить конкретную информацию о функциональности вашего проекта.

## Возможности

- Шаблоны workflow для типичных задач
- Инструкции по развёртыванию и локальной разработке
- Подготовка к публикации кастомных нод n8n (примерная структура)

## Требования

- Node.js >= 18 (для работы с workflow-проектами n8n)
- npm или yarn
- Python >= 3.10 для MCP-сервера
- Docker (опционально, для запуска n8n в контейнере)

## Установка

1. Клонируйте репозиторий:

   git clone https://github.com/Peakviker/MCPn8n.git
   cd MCPn8n

2. Установите зависимости Node.js (если используются workflow- или node-пакеты):

   npm install
   # или
   yarn install

3. Настройте Python-окружение и установите зависимости MCP-сервера:

   python -m venv .venv
   source .venv/bin/activate
   pip install fastapi uvicorn[standard] sse-starlette httpx python-dotenv

4. Скопируйте и отредактируйте пример файла конфигурации:

   cp .env.example .env
   # переменные уже содержат доступы для демо-сервера n8n

## Запуск локально

- Если проект содержит серверную часть или скрипты для n8n, используйте:

  npm run start
  # или
  yarn start

- Для запуска n8n через Docker:

  docker run -it --rm \
    -p 5678:5678 \
    -v ~/.n8n:/home/node/.n8n \
    n8nio/n8n

- Для запуска MCP FastAPI-сервера, проксирующего запросы к n8n:

  export N8N_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDcwNjBkNi1kMTkxLTQ3NTEtODdjOC05YzA0MmZhNmM2NTQiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYwNTUzOTQwLCJleHAiOjE3NjMwNjc2MDB9.tbOVXX0M_Y0t2cv-dbLQhdZoPLmB6TwOS4SenrJvyJM"
  # при необходимости скорректируйте базовый URL
  export N8N_URL="https://2n8ntimeweb.webtm.ru"
  uvicorn mcp_server:app --reload --port 8080

  Приложение автоматически читает переменные окружения из `.env`, поэтому можно вместо экспорта использовать файл, созданный из
  `.env.example`.

  Сервер предоставляет эндпоинты `/mcp/discover`, `/mcp/request` (SSE) и `/healthz`. При обработке MCP-команд он обращается к REST API n8n с помощью `httpx.AsyncClient`, логирует запросы/ответы и транслирует ответы в JSON Schema-формате, совместимом с MCP.

## Структура репозитория (пример)

- /workflows — примеры workflow для n8n
- /nodes — кастомные ноды (если применимо)
- /scripts — вспомогательные скрипты для разработки

Отредактируйте в соответствии с реальной структурой проекта.

## Разработка

1. Создайте ветку для фичи или исправления:

   git checkout -b feature/имя-фичи

2. Вносите изменения, коммитьте и пушьте:

   git add .
   git commit -m "Описание изменений"
   git push origin feature/имя-фичи

3. Откройте pull request и опишите изменения.

## Тестирование

Добавьте инструкции по запуску тестов, если они есть:

   npm test
   # или
   yarn test

## Лицензия

Укажите лицензию проекта (например, MIT). Если лицензия ещё не выбрана, добавьте файл LICENSE в корень репозитория.

## Контакты

Если у вас есть вопросы или предложения — откройте issue в репозитории или свяжитесь с автором: @Peakviker
