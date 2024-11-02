#!/bin/bash

cd /home/ubuntu/app/House_Manager_App

sudo docker-compose -f docker-compose.aws.yml exec web python manage.py createsuperuser
