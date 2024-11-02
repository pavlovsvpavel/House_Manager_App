aws_region                 = "eu-central-1"
aws_key_pair               = "house-manager-terraform-key"
aws_security_group         = "house-manager-sg"
instance_image_id          = "ami-0084a47cc718c111a"
instance_type              = "t2.micro"
ebs_volume_size            = 10
ebs_volume_type            = "gp2"
instance_name              = "HouseManagerInstance"
existing_eip_allocation_id = "eipalloc-0e0c01eed51156701"
connection_user            = "ubuntu"
s3_bucket_name             = "storage-for-env-files"

