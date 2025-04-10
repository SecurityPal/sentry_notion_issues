FROM python:3.11-slim

WORKDIR /app

# Copy source code first
COPY . .

# Install dependencies using uv
RUN pip install --no-cache-dir "uv>=0.1.0" && \
    uv pip install --system --no-cache-dir -e .

# Set environment variables with defaults
ENV NOTION_TOKEN=""
ENV NOTION_CONFIG=""
ENV SENTRY_NOTION_INTEGRATION_CLIENT_SECRET=""
ENV CACHE_TIMEOUT="21600"
ENV REDIS_HOST="redis"
ENV REDIS_PORT="6379"

EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
