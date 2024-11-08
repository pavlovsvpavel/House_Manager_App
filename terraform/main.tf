terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.73"
    }

    tls = {
      source  = "hashicorp/tls"
      version = "4.0.6"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

## Creation of new key pair for local deploy
resource "tls_private_key" "app_private_key_creation" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "aws_key_pair" "app_key_pair" {
  key_name   = var.aws_new_key_pair
  public_key = tls_private_key.app_private_key_creation.public_key_openssh
}

resource "local_file" "private_key_path" {
  filename = var.private_key_path
  content  = tls_private_key.app_private_key_creation.private_key_pem

  file_permission = "0400"
}

resource "aws_security_group" "app_security_group" {
  name_prefix = var.aws_security_group
  description = "Allow SSH and HTTP/HTTPS"

  # Allow SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Egress (allow all outgoing traffic)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "app_instance_creation" {
  ami                    = var.instance_image_id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.app_security_group.id]
  key_name               = aws_key_pair.app_key_pair.key_name

  root_block_device {
    volume_size = var.ebs_volume_size
    volume_type = var.ebs_volume_type
  }

  tags = {
    Name = var.instance_name
  }

  connection {
    type        = "ssh"
    host        = aws_instance.app_instance_creation.public_ip
    user        = var.connection_user
    private_key = local_file.private_key_path.content
  }

  provisioner "remote-exec" {
    inline = [
      "mkdir -p /home/ubuntu/app/envs",
      "mkdir -p /home/ubuntu/app/scripts",
    ]
  }

  provisioner "file" {
    source      = "../envs/.env.cloud"
    destination = "/home/ubuntu/app/envs/.env.cloud"
  }

  provisioner "file" {
    source      = "${path.module}/scripts/setup.sh"
    destination = "/home/ubuntu/app/scripts/setup.sh"
  }

  provisioner "file" {
    source      = "${path.module}/scripts/setup-web-container.sh"
    destination = "/home/ubuntu/app/scripts/setup-web-container.sh"
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /home/ubuntu/app/scripts/setup.sh",
      "sleep 5",
      "sudo /home/ubuntu/app/scripts/setup.sh",
      "chmod +x /home/ubuntu/app/scripts/setup-web-container.sh",
      "sleep 5",
      "sudo /home/ubuntu/app/scripts/setup-web-container.sh"
    ]
  }
}

## Use this resource, if you don't have elastic IP
resource "aws_eip" "elastic_ip_creation" {
  instance = aws_instance.app_instance_creation.id
  domain   = "vpc"
}

## Use this resource, if you already have elastic IP
# resource "aws_eip_association" "existing_ip_association" {
#   instance_id   = aws_instance.app_instance_creation.id
#   allocation_id = var.existing_eip_allocation_id
# }

output "private_ip" {
  value = aws_instance.app_instance_creation.private_ip
}

output "instance_id" {
  value = aws_instance.app_instance_creation.id
}

output "elastic_ip" {
  value = aws_eip.elastic_ip_creation.public_ip
}
