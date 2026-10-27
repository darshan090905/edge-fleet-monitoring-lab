terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# 1. SSH Key Pair for Secure Access
resource "aws_key_pair" "ops_key" {
  key_name   = "brivo-ops-key"
  public_key = var.public_key
}

# 2. Security Group with Least Privilege Access (Restricted to Operator IP)
resource "aws_security_group" "brivo_ops_sg" {
  name        = "brivo-edge-monitoring-sg"
  description = "Security group for Brivo Edge Operations Fleet Control Center"

  # SSH Access ONLY from Operator's specific IP
  ingress {
    description = "SSH administration access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.operator_ip]
  }

  # Grafana Dashboard Access ONLY from Operator IP
  ingress {
    description = "Grafana dashboard"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = [var.operator_ip]
  }

  # Prometheus Access ONLY from Operator IP
  ingress {
    description = "Prometheus web console"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = [var.operator_ip]
  }

  # Alertmanager Access ONLY from Operator IP
  ingress {
    description = "Alertmanager console"
    from_port   = 9093
    to_port     = 9093
    protocol    = "tcp"
    cidr_blocks = [var.operator_ip]
  }

  # Outbound Internet Access for Docker pulls and package updates
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "brivo-edge-monitoring-sg"
    Environment = "Portfolio-Lab"
  }
}

# 3. Least-Privilege IAM Role & Instance Profile for EC2
resource "aws_iam_role" "ec2_ops_role" {
  name = "brivo-ec2-ops-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# CloudWatch Agent permissions for telemetry
resource "aws_iam_role_policy_attachment" "cloudwatch_policy" {
  role       = aws_iam_role.ec2_ops_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "brivo-ec2-ops-profile"
  role = aws_iam_role.ec2_ops_role.name
}

# 4. Amazon Linux 2023 AMI Lookup
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

# 5. EC2 Instance (t3.micro - Free Tier Eligible)
resource "aws_instance" "ops_server" {
  ami                  = data.aws_ami.amazon_linux_2023.id
  instance_type        = "t3.micro"
  key_name             = aws_key_pair.ops_key.key_name
  vpc_security_group_ids = [aws_security_group.brivo_ops_sg.id]
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }

  # User Data: Installs Docker, Compose, and creates 2GB swap space to ensure smooth execution on t3.micro
  user_data = <<-EOF
              #!/bin/bash
              set -ex

              # 1. Create 2GB Swap file for smooth container compilation
              dd if=/dev/zero of=/swapfile bs=128M count=16
              chmod 600 /swapfile
              mkswap /swapfile
              swapon /swapfile
              echo "/swapfile swap swap defaults 0 0" >> /etc/fstab

              # 2. Install Docker and Git
              dnf update -y
              dnf install -y docker git

              # 3. Enable and start Docker
              systemctl enable --now docker
              usermod -aG docker ec2-user

              # 4. Install Docker Compose plugin
              mkdir -p /usr/local/lib/docker/cli-plugins
              curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
              chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

              echo "Brivo Operations Control Center initialization complete." > /home/ec2-user/bootstrap.log
              EOF

  tags = {
    Name        = "brivo-edge-operations-center"
    Environment = "Portfolio-Lab"
  }
}

# 6. SNS Topic for Operations Critical Alerts
resource "aws_sns_topic" "ops_alerts" {
  name = "brivo-operations-alerts-topic"
}

resource "aws_sns_topic_subscription" "email_sub" {
  topic_arn = aws_sns_topic.ops_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# 7. CloudWatch Alarms: EC2 Status Check Failed & High CPU (>80%)
resource "aws_cloudwatch_metric_alarm" "instance_status_check" {
  alarm_name          = "brivo-ec2-status-check-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Maximum"
  threshold           = 0
  alarm_description   = "Triggered when EC2 hardware or system status checks fail"
  alarm_actions       = [aws_sns_topic.ops_alerts.arn]

  dimensions = {
    InstanceId = aws_instance.ops_server.id
  }
}

resource "aws_cloudwatch_metric_alarm" "high_cpu_alarm" {
  alarm_name          = "brivo-ec2-high-cpu-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Triggers when EC2 server CPU exceeds 80% for 10 minutes"
  alarm_actions       = [aws_sns_topic.ops_alerts.arn]

  dimensions = {
    InstanceId = aws_instance.ops_server.id
  }
}
