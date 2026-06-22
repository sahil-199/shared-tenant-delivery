FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

COPY . .

RUN chmod +x start.sh

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=config.settings.production

CMD ["./start.sh"]
