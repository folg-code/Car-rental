FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .

RUN pip install uv

RUN uv pip install --system \
    "django>=5.2" \
    "psycopg[binary]" \
    "django-environ"

COPY . .

CMD ["sh", "-c", "python backend/manage.py migrate && python backend/manage.py runserver 0.0.0.0:8000"]