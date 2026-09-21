FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc libmagic1 libpango-1.0-0 libpangocairo-1.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt
COPY . .
RUN mkdir -p logs staticfiles && chmod +x docker-entrypoint.sh
ENTRYPOINT ["./docker-entrypoint.sh"]
