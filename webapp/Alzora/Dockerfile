# Dockerfile (use this)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
WORKDIR /app

ENV PATH="/home/myuser/.local/bin:$PATH"

# Install OS packages required to build mysqlclient + a few helpful tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    python3-dev \
    gcc \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (optional but recommended)
RUN adduser --disabled-password --gecos "" myuser && mkdir /home/myuser/.cache
RUN chown -R myuser:myuser /app /home/myuser
USER myuser

# Copy dependencies first (leveraging docker cache)
COPY --chown=myuser:myuser requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the code
COPY --chown=myuser:myuser . /app

# Collect static files into STATIC_ROOT (make sure collectstatic does NOT require DB at import)
# If collectstatic triggers DB access in settings, you may run this step in CI instead.
RUN python manage.py collectstatic --noinput || true

# Expose port and run gunicorn using $PORT provided by Cloud Run
CMD exec gunicorn Alzora.wsgi:application --bind :$PORT --workers 2 --threads 4 --timeout 120
