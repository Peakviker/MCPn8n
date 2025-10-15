# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY mcp_server.py .
COPY .env.example .

# Открываем порт 8080
EXPOSE 8080

# Команда запуска приложения
CMD ["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8080"]
