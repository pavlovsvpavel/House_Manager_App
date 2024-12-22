#!/bin/bash

# Stop the script if any command fails
set -e

# Update and upgrade the system
echo "Updating and upgrading the system..."
if ! sudo apt-get update -y; then
    echo "Error: Failed to update the package list."
    exit 1
fi

if ! sudo apt-get upgrade -y; then
    echo "Error: Failed to upgrade the system packages."
    exit 1
fi

# Install Docker/Docker Compose
echo "Installing Docker via Snap..."
if ! sudo snap install docker; then
    echo "Error: Failed to install Docker."
    exit 1
fi

# Add the docker group and user to the docker group
echo "Adding the docker group and user to the docker group..."
if ! sudo groupadd docker || true; then
    echo "Error: Failed to add the docker group."
    exit 1
fi

if ! sudo usermod -aG docker ubuntu; then
    echo "Error: Failed to add the user 'ubuntu' to the docker group."
    exit 1
fi

# Switch to the ubuntu user for the remaining commands
echo "Switching to the ubuntu user for further commands..."
sudo -u ubuntu -i <<'EOF'

# Ensure the new group membership takes effect
echo "Ensuring the new group membership takes effect..."
newgrp docker <<'GRP'

# Create app directory
echo "Creating the app directory..."
if ! mkdir -p /home/ubuntu/app; then
    echo "Error: Failed to create the app directory."
    exit 1
fi

# Navigate to the app directory
echo "Navigating to the app directory..."
cd /home/ubuntu/app || exit

# Clone the repository
echo "Cloning the repository..."
if ! git clone https://$GH_PAT@github.com/pavlovsvpavel/House_Manager_App.git; then
    echo "Error: Failed to clone the repository."
    exit 1
fi

cd House_Manager_App || exit

# Copy the env files to repository envs folder
echo "Copying .env files..."
if ! mkdir -p ./envs; then
    echo "Error: Failed to create the envs directory."
    exit 1
fi

if ! cp /home/ubuntu/app/envs/.env.dev ./envs; then
    echo "Error: Failed to copy .env.dev file."
    exit 1
fi

if ! cp /home/ubuntu/app/envs/.env.prod ./envs; then
    echo "Error: Failed to copy .env.prod file."
    exit 1
fi

# Build images and run containers
echo "Building images and running containers..."
if ! sudo docker-compose -f docker-compose.dev.yml -p development up -d --build; then
    echo "Error: Failed to build and run Docker containers."
    exit 1
fi

echo "Script completed successfully."
GRP
EOF
