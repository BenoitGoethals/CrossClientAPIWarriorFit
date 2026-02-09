FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    PYTHONPATH="/app"

# Set working directory
WORKDIR /app

# Copy dependency files first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# This creates a virtual environment in /app/.venv
RUN uv sync --frozen --no-install-project

# Add the virtual environment to the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy the rest of the application code (including certs)
COPY src ./src

# Remove config directory from container - config will be mounted from host
RUN rm -rf ./src/config

# Set APP_ENV to docker to use /etc/CrossClientAPI/config.yml
# Mount config from host: -v /path/to/config.yml:/etc/CrossClientAPI/config.yml
ENV APP_ENV=docker

# Install the project itself (if configured as a package)
RUN uv sync --frozen

EXPOSE 8555

# Run the app (FastAPI via Uvicorn with SSL)
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8555", "--ssl-keyfile", "./src/certs/key.pem", "--ssl-certfile", "./src/certs/cert.pem"]