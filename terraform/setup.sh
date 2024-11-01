#!/bin/bash

# Update and upgrade the system
sudo apt update -y
sudo apt upgrade -y

# Install Docker using snap
sudo apt install -y docker.io
sudo apt install -y docker-compose 

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
  git clone https://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@github.com/pavlovsvpavel/House_Manager_App.git
  cd House_Manager_App
fi

# Move the env file to repository root folder
if [ -f "/home/ubuntu/app/envs/.env.aws" ]; then
    mv /home/ubuntu/app/envs/.env.aws .
else
    echo "No .env.aws file found."
fi

# Build images and run containers
sudo docker-compose -f docker-compose.aws.yml up -d --build

EOF