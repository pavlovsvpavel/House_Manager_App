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

resource "aws_iam_policy" "access_policy" {
  name        = "MyS3AccessPolicy"
  description = "Policy to allow access to the .env.aws file in S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "s3:GetObject"
        Resource = "arn:aws:s3:::storage-for-env-files/.env.aws"
      }
    ]
  })
}

resource "aws_iam_role" "access_role" {
  name = "my_s3_access_role" # Replace with your desired role name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_policy" {
  policy_arn = aws_iam_policy.access_policy.arn
  role       = aws_iam_role.access_role.name
}

resource "tls_private_key" "tlspk" {
  algorithm = "RSA"
  rsa_bits  = 2048 # Specify the number of bits for the RSA key
}

resource "aws_key_pair" "akp" {
  count      = var.key_pair_exists ? 0 : 1 # Create if it doesn't exist
  key_name   = var.aws_key_pair
  public_key = tls_private_key.tlspk.public_key_openssh
}


resource "local_file" "private_key" {
  filename = "${path.module}/house-manager-terraform-key.pem" # Specify the path and filename to save the private key
  content  = tls_private_key.tlspk.private_key_pem            # Use the private key content from the TLS resource

  # Set permissions if desired
  file_permission = "0400" # Set the file to read-only for the owner
}

output "private_key" {
  value     = tls_private_key.tlspk.private_key_pem
  sensitive = true # Mark the output as sensitive to avoid displaying it in the console
}

resource "aws_security_group" "asg" {
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

resource "aws_instance" "awsi" {
  ami                    = var.instance_image_id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.asg.id]
  key_name               = aws_key_pair.akp[0].key_name

  root_block_device {
    volume_size = var.ebs_volume_size
    volume_type = var.ebs_volume_type
  }

  tags = {
    Name = var.instance_name
  }

  connection {
    type        = "ssh"
    host        = aws_instance.awsi.public_ip
    user        = var.connection_user
    private_key = local_file.private_key.content # Path to your SSH private key
  }

  provisioner "remote-exec" {
    inline = [
      "aws s3 cp s3://storage-for-env-files/.env.aws /home/ubuntu/app/envs/.env.aws"
    ]
  }

  # provisioner "remote-exec" {
  #   inline = [
  #     "mkdir -p /home/ubuntu/app/envs"
  #   ]
  # }
  #
  # provisioner "file" {
  #   source      = "${path.module}/.env.aws"        # Path to your local .env file
  #   destination = "/home/ubuntu/app/envs/.env.aws" # Destination path on the EC2 instance
  # }

  provisioner "file" {
    source      = "${path.module}/setup.sh"
    destination = "/home/ubuntu/setup.sh"
  }

  provisioner "file" {
    source      = "${path.module}/setup-web-container.sh"
    destination = "/home/ubuntu/setup-web-container.sh"
  }

  provisioner "file" {
    source      = "${path.module}/createsuperuser.sh"
    destination = "/home/ubuntu/createsuperuser.sh"
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /home/ubuntu/setup.sh",
      "sleep 5",
      "sudo /home/ubuntu/setup.sh"
    ]
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /home/ubuntu/setup-web-container.sh",
      "sleep 10",
      "sudo /home/ubuntu/setup-web-container.sh"
    ]
  }
}

resource "aws_eip_association" "aeipa" {
  depends_on    = [aws_instance.awsi]
  instance_id   = aws_instance.awsi.id
  allocation_id = var.existing_eip_allocation_id
}

resource "null_resource" "run_setup_script" {
  # Add a trigger to force rerun when needed
  triggers = {
    always_run = timestamp()
  }

  connection {
    type        = "ssh"
    host        = aws_instance.awsi.public_ip
    user        = var.connection_user
    private_key = local_file.private_key.content
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /home/ubuntu/setup.sh",
      "/home/ubuntu/setup.sh"
    ]
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /home/ubuntu/setup-web-container.sh",
      "sleep 10",
      "sudo /home/ubuntu/setup-web-container.sh"
    ]
  }
}

# Use this resourse, if you don't have elastic IP
# resource "aws_eip" "aeip" {
#   allocation_id = var.existing_eip_allocation_id
# }

