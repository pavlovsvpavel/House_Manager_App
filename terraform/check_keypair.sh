#!/bin/bash

# Output current operation
echo "Checking if the key pair exists..."

# Attempt to get the key pair details
KEY_PAIR_NAME="house-manager-terraform-key"
KEY_PAIR_INFO=$(aws ec2 describe-key-pairs --key-names "$KEY_PAIR_NAME" 2>&1)

if echo "$KEY_PAIR_INFO" | grep -q "not found"; then
    echo "Key pair '$KEY_PAIR_NAME' does not exist. Creating a new one..."
    # Your command to create the key pair here, if necessary
    # e.g., aws ec2 create-key-pair --key-name "$KEY_PAIR_NAME" ...
    echo "exists=false" >> $GITHUB_ENV  # Key pair does not exist
else
    echo "Key pair '$KEY_PAIR_NAME' already exists. Importing into Terraform..."
    echo "exists=true" >> $GITHUB_ENV  # Key pair exists
fi

# Exit with status code 0 for success
exit 0

