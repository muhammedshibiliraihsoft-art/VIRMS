FROM python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 DJANGO_SETTINGS_MODULE=core.settings
WORKDIR /app
COPY requirements.txt requirements-production-linux.lock ./
RUN pip install --no-cache-dir -r requirements.txt -c requirements-production-linux.lock
COPY . .
RUN DJANGO_ENV=local DJANGO_STATIC_MANIFEST=True DJANGO_SECRET_KEY=build-only-value DJANGO_ALLOWED_HOSTS=localhost DB_NAME=build DB_USER=build DB_PASSWORD=build DB_HOST=localhost python manage.py collectstatic --noinput
RUN useradd --system --create-home virms && chown -R virms:virms /app
USER virms
EXPOSE 8000
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
