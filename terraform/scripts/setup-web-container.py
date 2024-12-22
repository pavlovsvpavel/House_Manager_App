#!/usr/bin/env python3
import subprocess
import os
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

# Navigate to the application directory
app_path = "/home/ubuntu/app/House_Manager_App"
if not os.path.isdir(app_path):
    print(f"Directory {app_path} does not exist.")
    sys.exit(1)

os.chdir(app_path)

# Run Django management commands inside the web container
docker_compose_file = "docker-compose.dev.yml"
docker_project_name = "development"
management_commands = [
    "python manage.py migrate",
    "python manage.py collectstatic --noinput",
    "python manage.py makemessages -l bg",
    "python manage.py compilemessages",
]

for command in management_commands:
    full_command = f"docker-compose -f {docker_compose_file} -p {docker_project_name} exec -T web {command}"
    run_command(full_command, sudo=True)

# Restart all containers
run_command("docker restart $(docker ps -q)", sudo=True)

# Restart the instance
run_command("reboot", sudo=True)
