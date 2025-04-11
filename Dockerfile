FROM python:3.11-slim

WORKDIR /app

# Install uv separately first for better caching if uv version doesn't change
RUN pip install --no-cache-dir "uv>=0.1.0"

# Copy only the dependency definition file first
COPY pyproject.toml ./

# Now copy the rest of the application code
COPY . .

# Install dependencies using uv based on pyproject.toml
# The editable install (-e .) requires the src directory to be present
RUN uv pip install --system --no-cache-dir -e .

# Set environment variables with defaults
ENV CACHE_TIMEOUT="21600"
ENV REDIS_HOST="redis"
ENV REDIS_PORT="6379"

EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
