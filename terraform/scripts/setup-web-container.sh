#!/bin/bash

cd /home/ubuntu/app/House_Manager_App

# Run Django management commands inside the web container
sudo docker-compose -f docker-compose.cloud.yml exec -T web python manage.py migrate
sudo docker-compose -f docker-compose.cloud.yml exec -T web python manage.py collectstatic --noinput
sudo docker-compose -f docker-compose.cloud.yml exec -T web python manage.py makemessages -l bg
sudo docker-compose -f docker-compose.cloud.yml exec -T web python manage.py compilemessages

# Restart all containers
sudo docker restart $(docker ps -q)

# Restart instance
sudo reboot

