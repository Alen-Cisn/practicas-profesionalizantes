#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=practicas-e2e:latest

echo "Building Docker image $IMAGE_NAME..."
docker build -f docker/e2e.Dockerfile -t $IMAGE_NAME .

echo "Running E2E tests in container (this will start Streamlit inside the container)..."
docker run --rm -it $IMAGE_NAME
