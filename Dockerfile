FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 DJANGO_SETTINGS_MODULE=core.settings
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN DJANGO_ENV=local DJANGO_SECRET_KEY=build-only-value DJANGO_ALLOWED_HOSTS=localhost DB_NAME=build DB_USER=build DB_PASSWORD=build DB_HOST=localhost python manage.py collectstatic --noinput
RUN useradd --system --create-home virms && chown -R virms:virms /app
USER virms
EXPOSE 8000
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
