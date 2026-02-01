# WarriorFit API

A **FastAPI** backend application for managing running events and tracking runner performance.

## Overview

This project provides a secure RESTful API to interact with the WarriorFit database. WarriorFit is a running event management system that allows you to register participants, track finish times, and manage cross recordings during running events.

## Features

- **Runner Registration**: Register participants for running events
- **Time Tracking**: Record and manage finish times for runners
- **Cross Management**: Track and manage cross recordings for events
- **Event Management**: Access and manage running event data
- **API Key Security**: Secure endpoints with API key authentication
- **SSL/HTTPS Support**: Encrypted communication with SSL certificates
- **Database Integration**: Async PostgreSQL connection with SQLAlchemy
- **CORS Support**: Cross-origin resource sharing enabled

## Tech Stack

- **Backend**: FastAPI (Python 3.13+)
- **Database**: PostgreSQL with asyncpg
- **ORM**: SQLAlchemy (async)
- **Package Manager**: uv
- **Containerization**: Docker

## Prerequisites

- Docker and Docker Compose
- Git
- API key configured in `src/config/config.yml`
- SSL certificates (for HTTPS deployment)

## Installation & Deployment

### Using Docker (Recommended)

```bash
# Generate SSL certificates (if not already present)
mkdir -p src/certs
openssl req -x509 -newkey rsa:4096 \
  -keyout src/certs/key.pem \
  -out src/certs/cert.pem \
  -days 365 \
  -nodes \
  -subj "/CN=0.0.0.0" \
  -addext "subjectAltName=DNS:localhost,IP:0.0.0.0,IP:127.0.0.1,IP:YOUR_SERVER_IP"

# Sync repository
gh repo sync

# Stop and remove existing container
sudo docker stop api-warriorfit-app
sudo docker rm api-warriorfit-app

# Build Docker image
sudo docker build -t api-warriorfit-app .

# Run container with HTTPS
sudo docker run -d --restart unless-stopped --name api-warriorfit-app -p 8555:8555 api-warriorfit-app
```

### Local Development

```bash
# Generate SSL certificates (if not already present)
mkdir -p src/certs
openssl req -x509 -newkey rsa:4096 \
  -keyout src/certs/key.pem \
  -out src/certs/cert.pem \
  -days 365 \
  -nodes \
  -subj "/CN=0.0.0.0" \
  -addext "subjectAltName=DNS:localhost,IP:0.0.0.0,IP:127.0.0.1"

# Install dependencies
uv sync

# Run the application with HTTPS
uv run uvicorn src.main:app --host 0.0.0.0 --port 8555 --ssl-keyfile=./src/certs/key.pem --ssl-certfile=./src/certs/cert.pem

# Or run directly via Python
python src/main.py
```

## Configuration

The application uses a YAML configuration file located at `src/config/config.yml`. Ensure you configure:

- Database connection settings
- API secret key for authentication
- Environment-specific settings (test/production)

## API Documentation

Once the server is running, access the interactive API documentation at:
- **Swagger UI**: `https://localhost:8555/docs`
- **ReDoc**: `https://localhost:8555/redoc`

Note: If using self-signed certificates, your browser will show a security warning. You can proceed by accepting the certificate.

## Authentication

All API endpoints are protected with API key authentication. Include the API key in your requests:

```bash
# With SSL certificate verification
curl -H "X-API-Key: your-api-key-here" --cacert src/certs/cert.pem https://localhost:8555/api/endpoint

# Without SSL verification (not recommended for production)
curl -k -H "X-API-Key: your-api-key-here" https://localhost:8555/api/endpoint
```

### Client Configuration

Clients need the server's certificate file (`cert.pem`) to verify SSL connections:

**Python example:**
```python
import requests

response = requests.post(
    "https://YOUR_SERVER_IP:8555/crosses/38",
    json=data,
    headers={"X-API-Key": "your-api-key"},
    verify="./src/certs/cert.pem"  # Path to server's cert.pem
)
```

## Project Structure

```
CrossClientAPIWarriorFit/
├── src/
│   ├── main.py              # FastAPI application entry point
│   ├── certs/               # SSL certificates (key.pem, cert.pem)
│   ├── config/              # Configuration files
│   ├── core/                # Core utilities (config reader, etc.)
│   ├── model/               # Database models and schemas
│   ├── repo/                # Repository layer for database operations
│   └── data/                # Data-related utilities
├── Dockerfile               # Container configuration with SSL support
├── pyproject.toml          # Python project dependencies
├── uv.lock                 # Locked dependency versions
└── README.md               # This file
```

## License

Copyright (c) 2025 Goethals Benoit

This source code is provided for viewing purposes only.

You may NOT:
- Use this code in any project
- Copy, modify, or distribute this code
- Use this code for commercial or non-commercial purposes

All rights reserved.
