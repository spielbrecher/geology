FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# код проекта
COPY . .

# каталоги данных (поверх монтируются тома)
RUN mkdir -p /app/data /app/output /app/patterns

EXPOSE 8000 8501