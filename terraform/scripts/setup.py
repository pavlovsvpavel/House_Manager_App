#!/usr/bin/env python3
import os
import subprocess
import sys

def run_command(command, sudo=False):
    """Run a shell command."""
    try:
        if sudo:
            command = f"sudo {command}"
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error while executing '{command}': {e.stderr.decode('utf-8').strip()}")
        sys.exit(1)

# Update and upgrade the system
run_command("rm -rf /var/lib/dpkg/lock-frontend", sudo=True)
run_command("rm -rf /var/cache/apt/archives/lock", sudo=True)
run_command("apt-get update -y && apt-get upgrade -y", sudo=True)

# Install Docker/Docker Compose
run_command("snap install docker", sudo=True)

# Add the docker group and user to the docker group
run_command("groupadd docker || true", sudo=True)  # Skip if the group already exists
run_command("usermod -aG docker ubuntu", sudo=True)

# Switch to the ubuntu user for the remaining commands
try:
    # Navigate to the app directory
    app_path = "/home/ubuntu/app"
    os.makedirs(app_path, exist_ok=True)
    os.chdir(app_path)

    # Clone or pull the repository
    repo_path = os.path.join(app_path, "House_Manager_App")
    if os.path.isdir(os.path.join(repo_path, ".git")):
        os.chdir(repo_path)
        run_command("git pull origin development", sudo=True)
    else:
        run_command("git clone https://$GH_PAT@github.com/pavlovsvpavel/House_Manager_App.git")
        os.chdir(repo_path)
        run_command("git checkout development", sudo=True)

    # Move the env file to repository envs folder
    env_file = "/home/ubuntu/app/envs/.env.dev"
    env_dest_dir = "./envs"
    if os.path.isfile(env_file):
        os.makedirs(env_dest_dir, exist_ok=True)
        run_command(f"cp {env_file} {env_dest_dir}")
    else:
        print("No .env.dev file found.")

    # Build images and run containers
    run_command("docker-compose -f docker-compose.dev.yml -p development up -d --build", sudo=True)

except Exception as e:
    print(f"An error occurred: {str(e)}")
    sys.exit(1)
