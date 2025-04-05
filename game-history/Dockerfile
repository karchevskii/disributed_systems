FROM python:3.12.2-slim

WORKDIR /src/

# Install dependencies
COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./alembic.ini /src/alembic.ini
COPY ./app /src/app

# start the app
ENTRYPOINT ["gunicorn", "app.main:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--log-level", "INFO", "--access-logfile", "-", "--error-logfile", "-"]