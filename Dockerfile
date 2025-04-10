FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir "uv>=0.1.0"
RUN uv pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Set environment variables with defaults
ENV NOTION_TOKEN=""
ENV NOTION_CONFIG=""
ENV SENTRY_NOTION_INTEGRATION_CLIENT_SECRET=""
ENV CACHE_TIMEOUT="21600"
ENV REDIS_HOST="redis"
ENV REDIS_PORT="6379"

EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
