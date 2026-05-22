FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .

RUN pip install uv

COPY . .

RUN uv pip install --system .

CMD ["sh", "-c", "python backend/manage.py migrate && python backend/manage.py runserver 0.0.0.0:8000"]