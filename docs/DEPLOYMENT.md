# Deployment Guide

This guide covers deploying the Threat Intelligence Monitoring & Reputation Service across different environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Compose](#docker-compose)
3. [Kubernetes](#kubernetes)
4. [AWS ECS with Terraform](#aws-ecs-with-terraform)
5. [Configuration](#configuration)
6. [Health Checks](#health-checks)
7. [Monitoring Setup](#monitoring-setup)

## Local Development

### Prerequisites

- Python 3.9 or higher
- pip
- Redis (optional, but recommended)

### Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd threat-intelligence-monitoring
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

4. **Start Redis (optional)**
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

5. **Run the application**
```bash
python main.py
```

6. **Verify deployment**
```bash
curl http://localhost:8000/health
```

7. **Access API documentation**
Open browser: http://localhost:8000/docs

## Docker Compose

### Quick Start

```bash
cd infrastructure
docker-compose up -d
```

This deploys:
- **Monitoring Service**: Port 8000
- **Redis**: Port 6379
- **Prometheus**: Port 9090
- **Grafana**: Port 3000
- **AlertManager**: Port 9093

### Access Services

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- AlertManager: http://localhost:9093

### View Logs

```bash
docker-compose logs -f monitoring-service
```

### Stop Services

```bash
docker-compose down
```

### Rebuild and Restart

```bash
docker-compose up -d --build
```

## Kubernetes

### Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured
- Docker registry access

### Build and Push Image

```bash
# Build image
docker build -f infrastructure/Dockerfile -t your-registry/threat-monitoring:1.0.0 .

# Push to registry
docker push your-registry/threat-monitoring:1.0.0
```

### Update Deployment Configuration

Edit `infrastructure/kubernetes-deployment.yaml`:

```yaml
containers:
  - name: monitoring-service
    image: your-registry/threat-monitoring:1.0.0  # Update this
```

### Deploy to Kubernetes

```bash
# Create namespace and deploy
kubectl apply -f infrastructure/kubernetes-deployment.yaml

# Check deployment status
kubectl get pods -n threat-monitoring
kubectl get services -n threat-monitoring

# View logs
kubectl logs -f -n threat-monitoring deployment/monitoring-service

# Get service URL
kubectl get ingress -n threat-monitoring
```

### Configure Secrets

Before deploying, update secrets:

```bash
kubectl create secret generic monitoring-secrets \
  --from-literal=SMTP_HOST=smtp.gmail.com \
  --from-literal=SMTP_PORT=587 \
  --from-literal=SMTP_USERNAME=your-email@gmail.com \
  --from-literal=SMTP_PASSWORD=your-password \
  -n threat-monitoring
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment monitoring-service --replicas=5 -n threat-monitoring

# View HPA status
kubectl get hpa -n threat-monitoring
```

### Health Checks

```bash
# Check pod health
kubectl describe pod <pod-name> -n threat-monitoring

# Test health endpoint
kubectl port-forward -n threat-monitoring svc/monitoring-service 8000:8000
curl http://localhost:8000/health
```

## AWS ECS with Terraform

### Prerequisites

- AWS CLI configured
- Terraform installed (v1.0+)
- ECR repository created
- S3 bucket for Terraform state (recommended)

### Steps

1. **Build and push Docker image to ECR**

```bash
# Authenticate with ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -f infrastructure/Dockerfile -t threat-monitoring .
docker tag threat-monitoring:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/threat-monitoring:latest

# Push
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/threat-monitoring:latest
```

2. **Configure Terraform variables**

Create `infrastructure/terraform/terraform.tfvars`:

```hcl
aws_region         = "us-east-1"
environment        = "production"
ecr_repository_url = "<account-id>.dkr.ecr.us-east-1.amazonaws.com/threat-monitoring"
image_tag          = "latest"

# Resource sizing
task_cpu           = "1024"
task_memory        = "2048"
desired_count      = 3
min_capacity       = 2
max_capacity       = 10

# Network configuration
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

# Redis configuration
redis_node_type    = "cache.t3.medium"
```

3. **Initialize Terraform**

```bash
cd infrastructure/terraform
terraform init
```

4. **Plan deployment**

```bash
terraform plan -var-file=terraform.tfvars
```

5. **Apply deployment**

```bash
terraform apply -var-file=terraform.tfvars
```

6. **Get outputs**

```bash
terraform output alb_dns_name
terraform output redis_endpoint
terraform output ecs_cluster_name
```

7. **Access the service**

```bash
ALB_DNS=$(terraform output -raw alb_dns_name)
curl http://$ALB_DNS/health
```

### Update Deployment

```bash
# Build new image
docker build -f infrastructure/Dockerfile -t threat-monitoring .
docker tag threat-monitoring:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/threat-monitoring:v1.1.0
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/threat-monitoring:v1.1.0

# Update Terraform variable
# Edit terraform.tfvars: image_tag = "v1.1.0"

# Apply changes
terraform apply -var-file=terraform.tfvars
```

### Destroy Infrastructure

```bash
terraform destroy -var-file=terraform.tfvars
```

## Configuration

### Environment Variables

#### Required

```bash
# Redis (optional but recommended)
REDIS_URL=redis://localhost:6379
REDIS_TTL_SECONDS=3600

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

#### Optional

```bash
# Alert Configuration
ALERT_THRESHOLD=10
BURST_THRESHOLD=100
BURST_WINDOW_SECONDS=60

# Notification (for production)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@example.com
SMTP_PASSWORD=your-password
NOTIFICATION_FROM=alerts@example.com
NOTIFICATION_TO=security@example.com

# Webhook
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
WEBHOOK_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

### Configuration Files

#### Docker Compose

Edit `infrastructure/docker-compose.yml` to modify environment variables:

```yaml
environment:
  - REDIS_URL=redis://redis:6379
  - ALERT_THRESHOLD=10
  # Add more variables
```

#### Kubernetes

Update ConfigMap in `infrastructure/kubernetes-deployment.yaml`:

```yaml
data:
  REDIS_URL: "redis://redis-service:6379"
  ALERT_THRESHOLD: "10"
```

#### Terraform

Update variables in `infrastructure/terraform/variables.tf` or `terraform.tfvars`.

## Health Checks

### Endpoints

**Liveness Probe**
```bash
curl http://localhost:8000/health
```

Returns:
```json
{"status": "healthy"}
```

**Readiness Probe**
```bash
curl http://localhost:8000/api/v1/monitoring/health
```

Returns:
```json
{
  "status": "healthy",
  "components": {
    "streaming_processor": {"status": "healthy"},
    "notification_manager": {"status": "healthy"}
  },
  "uptime_seconds": 86400.5
}
```

### Kubernetes Health Checks

Health checks are configured in the Kubernetes deployment:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /api/v1/monitoring/health
    port: 8000
  initialDelaySeconds: 20
  periodSeconds: 5
```

## Monitoring Setup

### Prometheus Configuration

Prometheus is configured to scrape metrics from the monitoring service:

```yaml
scrape_configs:
  - job_name: 'threat-monitoring'
    static_configs:
      - targets: ['monitoring-service:8000']
    metrics_path: '/api/v1/monitoring/metrics'
    scrape_interval: 15s
```

### Grafana Setup

1. **Access Grafana**
   - URL: http://localhost:3000 (Docker Compose)
   - Default credentials: admin/admin

2. **Add Prometheus Data Source**
   - Already configured via provisioning
   - URL: http://prometheus:9090

3. **Import Dashboard**
   - Create new dashboard
   - Add panels for key metrics

4. **Key Metrics to Monitor**
   - Event processing rate: `rate(detection_events_total[5m])`
   - Active alerts: `sum(active_alerts) by (severity)`
   - Notification success rate: `sum(rate(notifications_sent_total{success="true"}[5m])) / sum(rate(notifications_sent_total[5m]))`
   - Cache hit rate: `sum(rate(reputation_lookups_total{cached="true"}[5m])) / sum(rate(reputation_lookups_total[5m]))`

### AlertManager Configuration

Configure alerts in `infrastructure/alertmanager.yml`:

```yaml
receivers:
  - name: 'critical-alerts'
    email_configs:
      - to: 'security-critical@example.com'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
```

## Production Best Practices

### Security

1. **TLS/SSL**: Enable HTTPS for all endpoints
2. **Authentication**: Implement API authentication (API keys, OAuth)
3. **Secrets Management**: Use AWS Secrets Manager, HashiCorp Vault, or Kubernetes Secrets
4. **Network Security**: Configure security groups and network policies

### Performance

1. **Caching**: Enable Redis caching for reputation lookups
2. **Horizontal Scaling**: Configure auto-scaling based on load
3. **Resource Limits**: Set appropriate CPU and memory limits
4. **Connection Pooling**: Configure Redis connection pooling

### Reliability

1. **High Availability**: Deploy across multiple availability zones
2. **Health Checks**: Configure proper liveness and readiness probes
3. **Monitoring**: Set up comprehensive monitoring and alerting
4. **Backup**: Regular backups of Redis data (if persistence is needed)

### Observability

1. **Logging**: Centralized logging (ELK, CloudWatch, etc.)
2. **Metrics**: Prometheus + Grafana for metrics
3. **Tracing**: Distributed tracing (Jaeger, Zipkin)
4. **Alerting**: AlertManager for critical alerts

## Troubleshooting

### Service Not Starting

```bash
# Check logs
docker-compose logs monitoring-service
kubectl logs -f deployment/monitoring-service -n threat-monitoring

# Common issues:
# - Redis connection failed: Check REDIS_URL
# - Port already in use: Change API_PORT
# - Import errors: Reinstall dependencies
```

### High Memory Usage

```bash
# Reduce cache TTL
REDIS_TTL_SECONDS=1800

# Limit event history
# (Modify processor.py maxlen parameter)

# Scale horizontally instead of vertically
```

### Slow Response Times

```bash
# Enable caching
REDIS_URL=redis://localhost:6379

# Increase resources
# Kubernetes: Update resource requests/limits
# ECS: Increase task_cpu and task_memory

# Check external API rate limits
```

### Failed Notifications

```bash
# Check SMTP configuration
# Verify webhook URLs
# Review notification logs
# Test connectivity

# Test email notification
curl -X POST http://localhost:8000/api/v1/monitoring/events \
  -H "Content-Type: application/json" \
  -d '{"event_id":"test", "severity":"critical", ...}'
```

## Rollback

### Kubernetes

```bash
# View rollout history
kubectl rollout history deployment/monitoring-service -n threat-monitoring

# Rollback to previous version
kubectl rollout undo deployment/monitoring-service -n threat-monitoring

# Rollback to specific revision
kubectl rollout undo deployment/monitoring-service --to-revision=2 -n threat-monitoring
```

### ECS with Terraform

```bash
# Revert to previous image tag
# Edit terraform.tfvars: image_tag = "previous-version"

terraform apply -var-file=terraform.tfvars
```

## Support

For deployment issues:
- Check logs and health endpoints
- Review configuration
- Consult documentation
- Open an issue on GitHub
