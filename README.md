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

## Installation & Deployment

### Using Docker (Recommended)

```bash
# Sync repository
gh repo sync

# Stop and remove existing container
sudo docker stop api-warriorfit-app
sudo docker rm api-warriorfit-app

# Build Docker image
sudo docker build -t api-warriorfit-app .

# Run container
sudo docker run -d --restart unless-stopped --name api-warriorfit-app -p 8555:8555 api-warriorfit-app
```

### Local Development

```bash
# Install dependencies
uv sync

# Run the application
uv run uvicorn src.main:app --host 0.0.0.0 --port 8555
```

## Configuration

The application uses a YAML configuration file located at `src/config/config.yml`. Ensure you configure:

- Database connection settings
- API secret key for authentication
- Environment-specific settings (test/production)

## API Documentation

Once the server is running, access the interactive API documentation at:
- **Swagger UI**: `http://localhost:8555/docs`
- **ReDoc**: `http://localhost:8555/redoc`

## Authentication

All API endpoints are protected with API key authentication. Include the API key in your requests:

```bash
curl -H "X-API-Key: your-api-key-here" http://localhost:8555/api/endpoint
```

## Project Structure

```
CrossClientAPIWarriorFit/
├── src/
│   ├── main.py              # FastAPI application entry point
│   ├── config/              # Configuration files
│   ├── core/                # Core utilities (config reader, etc.)
│   ├── model/               # Database models
│   ├── repo/                # Repository layer for database operations
│   └── data/                # Data-related utilities
├── Dockerfile               # Container configuration
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
