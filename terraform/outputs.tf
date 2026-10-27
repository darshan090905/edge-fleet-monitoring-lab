output "ec2_public_ip" {
  description = "Public IP address of the deployed EC2 Operations Server"
  value       = aws_instance.ops_server.public_ip
}

output "ssh_login_command" {
  description = "Command to connect via SSH"
  value       = "ssh -i <your-private-key> ec2-user@${aws_instance.ops_server.public_ip}"
}

output "grafana_url" {
  description = "Public URL for Grafana Dashboard"
  value       = "http://${aws_instance.ops_server.public_ip}:3000"
}

output "prometheus_url" {
  description = "Public URL for Prometheus Console"
  value       = "http://${aws_instance.ops_server.public_ip}:9090"
}

output "sns_topic_arn" {
  description = "ARN of the SNS alert topic"
  value       = aws_sns_topic.ops_alerts.arn
}
