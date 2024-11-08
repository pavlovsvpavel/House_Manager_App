variable "aws_region" {
  type        = string
  description = "AWS region"
}

variable "aws_new_key_pair" {
  type        = string
  description = "The name of the key pair"
}

variable "aws_security_group" {
  type        = string
  description = "The name of the security group"
}

variable "instance_name" {
  type        = string
  description = "The name of the instance"
}

variable "instance_image_id" {
  type        = string
  description = "Instance image OS/AMI ID for your region"
}

variable "instance_type" {
  type        = string
  description = "Instance type"
}

variable "ebs_volume_size" {
  type        = number
  description = "The size of the EBS volume in GB"
}

variable "ebs_volume_type" {
  type        = string
  description = "The type of the EBS volume"
}

variable "existing_eip_allocation_id" {
  description = "The allocation ID of the existing Elastic IP."
  type        = string
}

variable "connection_user" {
  description = "The user for ssh connection"
  type        = string
}

variable "private_key_path" {
  description = "The private key path"
  type        = string
}
