FROM python:3.12-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gettext \
        redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Install Python deps
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

# Copy project code
COPY . .

# Create dirs that may be needed at runtime
RUN mkdir -p /app/logs /app/staticfiles && \
    chown -R appuser:appgroup /app

# Entrypoint
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER appuser

ENTRYPOINT ["/entrypoint.sh"]
