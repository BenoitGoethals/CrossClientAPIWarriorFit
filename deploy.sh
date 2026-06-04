#!/bin/bash


set -e  # Exit on error

CONTAINER_NAME="api-warriorfit-app"
IMAGE_NAME="api-warriorfit-app"
PORT_MAPPING="8555:8555"

# Load WF_SECRET_KEY from .env if not already set in the environment
if [ -z "${WF_SECRET_KEY}" ]; then
    if [ -f ".env" ]; then
        WF_SECRET_KEY=$(grep '^WF_SECRET_KEY=' .env | cut -d '=' -f2-)
    fi
fi

if [ -z "${WF_SECRET_KEY}" ]; then
    echo "ERROR: WF_SECRET_KEY is not set and could not be loaded from .env"
    exit 1
fi

echo "=== Docker Deployment Script ==="
echo ""

# 1. List all containers
echo "Step 1: Listing all containers..."
docker ps -a
echo ""

# 2. Check if container exists and stop it
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Step 2: Container '${CONTAINER_NAME}' found. Stopping..."
    docker stop "${CONTAINER_NAME}" || true
    echo "Container stopped."
else
    echo "Step 2: Container '${CONTAINER_NAME}' not found. Skipping stop."
fi
echo ""

# 3. Remove the container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Step 3: Removing container '${CONTAINER_NAME}'..."
    sudo docker rm "${CONTAINER_NAME}"
    echo "Container removed."
else
    echo "Step 3: Container '${CONTAINER_NAME}' not found. Skipping removal."
fi
echo ""

# 4. Build the Docker image
echo "Step 4: Building Docker image '${IMAGE_NAME}'..."
sudo docker build -t "${IMAGE_NAME}" .
echo "Image built successfully."
echo ""

# 5. Run the new container
echo "Step 5: Starting new container '${CONTAINER_NAME}'..."
sudo docker run -d \
    --restart unless-stopped \
    --name "${CONTAINER_NAME}" \
    -v /home/benoit/path/to/config.yml:/etc/CrossClientAPI/config.yml \
    -e "WF_SECRET_KEY=${WF_SECRET_KEY}" \
    -p "${PORT_MAPPING}" \
    "${IMAGE_NAME}"
echo "Container started successfully."
echo ""

# 6. Show running containers
echo "=== Deployment Complete ==="
echo "Running containers:"
docker ps | grep "${CONTAINER_NAME}" || echo "Warning: Container not found in running list"
echo ""
echo "To view logs: docker logs ${CONTAINER_NAME}"
echo "To follow logs: docker logs -f ${CONTAINER_NAME}"