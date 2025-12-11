# Detection Engine Deployment Guide

This document provides comprehensive deployment instructions for the Detection Engine microservice in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **CPU**: 2+ cores recommended
- **Memory**: 512MB minimum, 2GB+ recommended
- **Disk**: 100MB+ for application and rules
- **Network**: Connectivity to Kafka brokers (if used)

### Software Requirements

- Go 1.21+ (for local builds)
- Docker (for containerized deployment)
- Kubernetes 1.20+ (for K8s deployment)
- Kafka 2.8+ (optional, for alert publishing)

## Local Development

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd detection-engine
```

2. Download dependencies:
```bash
go mod download
go mod tidy
```

3. Build the application:
```bash
go build -o detection-engine ./cmd/detection-engine
```

### Running Locally

Basic run with in-memory alert publisher:

```bash
./detection-engine \
  --rules-dir ./rules \
  --http :8080
```

With debug output:

```bash
./detection-engine \
  --rules-dir ./rules \
  --http :8080 \
  2>&1 | tee detection.log
```

### Testing

Run all tests:
```bash
go test ./...
```

Run tests with coverage:
```bash
go test -cover ./...
```

Run specific test:
```bash
go test -v ./internal/engine -run TestDetectorDetectSimpleMatch
```

## Docker Deployment

### Building the Docker Image

Create a `Dockerfile` in the project root:

```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o detection-engine ./cmd/detection-engine

# Runtime stage
FROM alpine:3.18

RUN apk --no-cache add ca-certificates

WORKDIR /app

COPY --from=builder /app/detection-engine /app/detection-engine
COPY --from=builder /app/rules /app/rules

RUN chmod +x /app/detection-engine

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

ENTRYPOINT ["/app/detection-engine"]
CMD ["--rules-dir", "/app/rules", "--http", ":8080"]
```

### Building the Image

```bash
docker build -t detection-engine:latest .
docker tag detection-engine:latest detection-engine:$(git rev-parse --short HEAD)
```

### Running the Container

Basic run:
```bash
docker run -p 8080:8080 detection-engine:latest
```

With rules volume:
```bash
docker run \
  -p 8080:8080 \
  -v $(pwd)/rules:/app/rules:ro \
  detection-engine:latest
```

With Kafka:
```bash
docker run \
  -p 8080:8080 \
  -e KAFKA_BROKERS=kafka:9092 \
  -e KAFKA_TOPIC=detection-alerts \
  -v $(pwd)/rules:/app/rules:ro \
  --network=detection-network \
  detection-engine:latest
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  detection-engine:
    build: .
    ports:
      - "8080:8080"
    depends_on:
      - kafka
    environment:
      DETECTION_HTTP_ADDR: ":8080"
      DETECTION_KAFKA_BROKERS: "kafka:9092"
      DETECTION_KAFKA_TOPIC: "detection-alerts"
    volumes:
      - ./rules:/app/rules:ro
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

Start services:
```bash
docker-compose up -d
```

Verify:
```bash
docker-compose logs -f detection-engine
curl http://localhost:8080/health
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Container registry access

### Creating Kubernetes Manifests

Create `k8s/namespace.yaml`:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: detection
```

Create `k8s/configmap.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: detection-rules
  namespace: detection
data:
  suspicious_login.yaml: |
    id: rule_001
    name: Suspicious Login Detection
    severity: high
    source: authentication
    enabled: true
    definition:
      event_types:
        - authentication_failure
      conditions:
        - field: payload.failure_count
          operator: greater_than
          value: 3
      actions:
        - type: alert
          indicators:
            - suspicious_authentication
```

Create `k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: detection-engine
  namespace: detection
  labels:
    app: detection-engine
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: detection-engine
  template:
    metadata:
      labels:
        app: detection-engine
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: detection-engine
      containers:
      - name: detection-engine
        image: detection-engine:latest
        imagePullPolicy: Always
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        env:
        - name: DETECTION_HTTP_ADDR
          value: ":8080"
        - name: DETECTION_KAFKA_BROKERS
          value: "kafka:9092"
        - name: DETECTION_KAFKA_TOPIC
          value: "detection-alerts"
        - name: DETECTION_RULES_DIR
          value: "/etc/detection/rules"
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 2
        volumeMounts:
        - name: rules
          mountPath: /etc/detection/rules
          readOnly: true
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1000
          capabilities:
            drop:
              - ALL
      volumes:
      - name: rules
        configMap:
          name: detection-rules
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - detection-engine
              topologyKey: kubernetes.io/hostname
```

Create `k8s/service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: detection-engine
  namespace: detection
  labels:
    app: detection-engine
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 8080
    targetPort: http
    protocol: TCP
  selector:
    app: detection-engine
```

Create `k8s/serviceaccount.yaml`:
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: detection-engine
  namespace: detection
```

### Deploying to Kubernetes

1. Create namespace:
```bash
kubectl apply -f k8s/namespace.yaml
```

2. Create configuration:
```bash
kubectl apply -f k8s/configmap.yaml
```

3. Create service account:
```bash
kubectl apply -f k8s/serviceaccount.yaml
```

4. Deploy the application:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

5. Verify deployment:
```bash
kubectl get deployment -n detection
kubectl get pods -n detection
kubectl logs -n detection -l app=detection-engine
```

### Updating Rules

Update the ConfigMap:
```bash
kubectl create configmap detection-rules \
  --from-file=./rules \
  --dry-run=client -o yaml | kubectl apply -f -
```

Restart pods to load new rules:
```bash
kubectl rollout restart deployment/detection-engine -n detection
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DETECTION_HTTP_ADDR | :8080 | HTTP server listen address |
| DETECTION_RULES_DIR | ./rules | Path to rules directory |
| DETECTION_KAFKA_BROKERS | (empty) | Kafka brokers (comma-separated) |
| DETECTION_KAFKA_TOPIC | detection-alerts | Kafka topic for alerts |

### Command Line Flags

```
-http string
    HTTP server address (default ":8080")
-rules-dir string
    Directory containing detection rules (default "./rules")
-kafka-brokers string
    Comma-separated Kafka broker addresses (optional)
-kafka-topic string
    Kafka topic for alerts (default "detection-alerts")
```

## Monitoring

### Health Checks

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{"status": "healthy"}
```

### Rule Status

```bash
curl http://localhost:8080/rules
```

### Performance Metrics

Monitor these metrics:
- Requests/second to `/ingest` endpoint
- Alert generation rate
- Rule evaluation time
- Publisher latency

### Logging

Logs are sent to stdout. Redirect to file:

```bash
./detection-engine --rules-dir ./rules > detection.log 2>&1
```

Use a log aggregation tool:
- ELK Stack
- Splunk
- Datadog
- CloudWatch

### Alerts and Notifications

Publish alerts to monitoring systems:
- SIEM integration (Splunk, ELK)
- Incident management (PagerDuty)
- Chat integration (Slack, Teams)
- Custom webhooks

## Troubleshooting

### Service won't start

1. Check logs:
```bash
./detection-engine --rules-dir ./rules 2>&1
```

2. Verify rules directory exists:
```bash
ls -la ./rules
```

3. Check port is available:
```bash
netstat -tlnp | grep 8080
```

### Rules not loading

1. Verify file format (YAML/JSON):
```bash
cat rules/rule.yaml
```

2. Validate YAML syntax:
```bash
go run ./cmd/detection-engine --rules-dir ./rules
```

3. Check logs for validation errors

### No alerts generated

1. Verify rule is enabled:
```bash
curl http://localhost:8080/rules | jq '.rules[0].enabled'
```

2. Test rule with sample event:
```bash
curl -X POST http://localhost:8080/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "test",
    "event_type": "test_event",
    "payload": {}
  }'
```

3. Check rule conditions match event

### Kafka connection issues

1. Verify Kafka broker is accessible:
```bash
telnet kafka-host 9092
```

2. Check Kafka topic exists:
```bash
kafka-topics --bootstrap-server localhost:9092 --list
```

3. Create topic if needed:
```bash
kafka-topics --bootstrap-server localhost:9092 \
  --create --topic detection-alerts --partitions 1 --replication-factor 1
```

### High memory usage

1. Monitor memory:
```bash
top -p $(pgrep -f detection-engine)
```

2. Check rule complexity
3. Reduce number of concurrent events
4. Increase memory limit if appropriate

### Slow response times

1. Check rule count:
```bash
curl http://localhost:8080/rules | jq '.total'
```

2. Optimize rule conditions (order by restrictiveness)
3. Profile with pprof:
```bash
go tool pprof http://localhost:6060/debug/pprof/profile
```

## Rollback Procedure

If deployment fails:

### Docker
```bash
docker run -p 8080:8080 detection-engine:previous-tag
```

### Kubernetes
```bash
kubectl rollout undo deployment/detection-engine -n detection
```

## Security Hardening

### Production Checklist

- ✅ Use read-only filesystem
- ✅ Run as non-root user
- ✅ Enable pod security policies
- ✅ Use network policies to restrict traffic
- ✅ Enable TLS for Kafka communication
- ✅ Rotate credentials regularly
- ✅ Monitor logs for anomalies
- ✅ Keep Go version updated
- ✅ Scan images for vulnerabilities
- ✅ Use private container registry

### Network Hardening

NetworkPolicy example:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: detection-engine
  namespace: detection
spec:
  podSelector:
    matchLabels:
      app: detection-engine
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: kafka
    ports:
    - protocol: TCP
      port: 9092
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

## Performance Tuning

### Kubernetes Resource Limits

For high-traffic environments:
```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 4Gi
```

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: detection-engine
  namespace: detection
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: detection-engine
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```
