variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "operator_ip" {
  description = "Your personal public IP address with CIDR suffix (e.g. 203.0.113.45/32)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "alert_email" {
  description = "Email address to receive CloudWatch critical notifications via SNS"
  type        = string
  default     = "darshan@example.com"
}

variable "public_key" {
  description = "SSH Public Key content (from ~/.ssh/id_rsa.pub or ssh-keygen)"
  type        = string
  default     = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGeneratedOpsKeyForBrivoPortfolioLab user@laptop"
}
