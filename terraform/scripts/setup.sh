#!/bin/bash

# Update and upgrade the system
sudo apt-get update -y && sudo apt-get upgrade -y

# Install Docker/Docker compose
sudo snap install docker

# Add the docker group and user to the docker group
sudo groupadd docker || true  # Skip if the group already exists
sudo usermod -aG docker ubuntu

# Switch to the ubuntu user for the remaining commands
sudo -u ubuntu -i <<'EOF'

# Create directory for the application
# mkdir -p /home/ubuntu/app

# Navigate to the app directory and either clone or pull
cd /home/ubuntu/app
if [ -d "House_Manager_App/.git" ]; then
  cd House_Manager_App
  git pull origin main  # Pulls the latest changes
else
  git clone https://$GH_PAT@github.com/pavlovsvpavel/House_Manager_App.git
  cd House_Manager_App
fi

# Move the env file to repository envs folder
if [ -f "/home/ubuntu/app/envs/.env.cloud" ]; then
    mkdir -p ./envs
    cp /home/ubuntu/app/envs/.env.cloud ./envs
else
    echo "No .env.cloud file found."
fi

# Build images and run containers
sudo docker-compose -f docker-compose.cloud.yml up -d --build

EOF