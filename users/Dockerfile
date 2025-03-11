FROM python:3.12.2-slim

WORKDIR /src/

# Install dependencies
COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./alembic.ini /src/alembic.ini
COPY ./prestart.sh /src/prestart.sh
COPY ./app /src/app

# Set execute permissions for the prestart script
RUN chmod +x ./prestart.sh

# CMD to run the application
CMD ["./prestart.sh", "gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--log-level", "INFO", "--access-logfile", "-", "--error-logfile", "-"]