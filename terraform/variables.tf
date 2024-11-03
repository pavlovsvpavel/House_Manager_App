variable "aws_region" {
  type        = string
  description = "AWS region"
}

variable "aws_key_pair" {
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

variable "key_pair_exists" {
  description = "Indicates whether the EC2 key pair already exists."
  type        = bool
  default     = false # Default to false if you want to assume it doesn't exist unless stated otherwise
}

variable "policy_exists" {
  type        = bool
  description = "Indicates if the IAM policy exists"
  default     = false
}

variable "role_exists" {
  type        = bool
  description = "Indicates if the IAM role exists"
  default     = false
}

variable "s3_bucket_name" {
  type        = string
  description = "The name of the S3 bucket."
}

variable "s3_env_file_key" {
  description = "The key for the .env file in S3"
  type        = string
  default     = ".env.aws"
}

variable "private_key_path" {
  description = "The private key path"
  type        = string
}
