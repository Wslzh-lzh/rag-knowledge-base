FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

COPY pyproject.toml /app/backend/pyproject.toml
RUN pip install --upgrade pip && pip install .

COPY app /app/backend/app
COPY alembic /app/backend/alembic
COPY alembic.ini /app/backend/alembic.ini
COPY entrypoint.sh /app/backend/entrypoint.sh

RUN chmod +x /app/backend/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/backend/entrypoint.sh"]
