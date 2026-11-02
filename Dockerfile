FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIPENV_NOSPIN=1

WORKDIR /app

COPY Pipfile Pipfile.lock ./
RUN python -m pip install --no-cache-dir pipenv \
    && pipenv install --system --deploy --ignore-pipfile

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /home/app --create-home app

COPY --chown=10001:10001 service ./service
COPY --chown=10001:10001 wsgi.py ./wsgi.py

USER 10001:10001

EXPOSE 8080

CMD ["gunicorn", "--bind=0.0.0.0:8080", "--workers=2", "--threads=4", "wsgi:app"]
