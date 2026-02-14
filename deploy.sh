#!/bin/bash
set -e

# WarriorFit API - Docker Deploy Script
# Usage: ./deploy.sh

APP_NAME="api-warriorfit-app"
IMAGE_NAME="api-warriorfit-app"
PORT="8555"
CONFIG_DIR="/home/benoit/PycharmProjects/CrossClientAPIWarriorFit/src/config"

echo "=========================================="
echo "  WarriorFit API - Deploy"
echo "=========================================="

# 1. Sync repository from GitHub
echo ""
echo "[1/4] Syncing repository from GitHub..."
gh repo sync
git pull
echo "Repository synced."

# 2. Stop running container
echo ""
echo "[2/4] Stopping container '${APP_NAME}'..."
if sudo docker ps -q -f name="${APP_NAME}" | grep -q .; then
    sudo docker stop "${APP_NAME}"
    echo "Container stopped."
else
    echo "Container not running, skipping stop."
fi

# 3. Remove container
echo ""
echo "[3/4] Removing container '${APP_NAME}'..."
if sudo docker ps -aq -f name="${APP_NAME}" | grep -q .; then
    sudo docker rm "${APP_NAME}"
    echo "Container removed."
else
    echo "Container does not exist, skipping remove."
fi

# 4. Build and deploy
echo ""
echo "[4/4] Building and deploying..."
sudo docker build -t "${IMAGE_NAME}" .

sudo docker run -d \
    --name "${APP_NAME}" \
    -p "${PORT}:${PORT}" \
    --restart unless-stopped \
    -e APP_ENV=docker \
    -v /home/benoit/path/to/config.yml:/etc/CrossClientAPI \
    "${IMAGE_NAME}"

echo ""
echo "=========================================="
echo "  Deploy complete!"
echo "  API running on https://localhost:${PORT}"
echo "=========================================="

# Show container status
sudo docker ps -f name="${APP_NAME}"