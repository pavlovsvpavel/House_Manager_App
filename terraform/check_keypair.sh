#!/bin/bash

# Define the key pair name
KEY_NAME="house-manager-terraform-key"

# Check if the key pair already exists in AWS
aws ec2 describe-key-pairs --key-names "$KEY_NAME" >/dev/null 2>&1

# Import the key pair into Terraform if it exists
if [ $? -eq 0 ]; then
  echo "Key pair '$KEY_NAME' already exists. Importing into Terraform..."
  terraform import aws_key_pair.akp "$KEY_NAME"
else
  echo "Key pair '$KEY_NAME' does not exist. Terraform will create it."
fi
