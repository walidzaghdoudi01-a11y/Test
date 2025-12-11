# Quick Start Guide

## Installation and Setup

### Build the Detection Engine

```bash
# Navigate to the project directory
cd /path/to/detection-engine

# Download dependencies
go mod download

# Build the binary
go build -o detection-engine ./cmd/detection-engine
```

### Run the Detection Engine

**Basic usage (in-memory alert storage):**

```bash
./detection-engine --rules-dir ./rules --http :8080
```

**With Kafka alert publisher:**

```bash
./detection-engine \
  --rules-dir ./rules \
  --http :8080 \
  --kafka-brokers localhost:9092 \
  --kafka-topic detection-alerts
```

## Testing the Service

### 1. Health Check

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{"status":"healthy"}
```

### 2. List Rules

```bash
curl http://localhost:8080/rules
```

### 3. Ingest a Telemetry Event

Test the suspicious login detection rule:

```bash
curl -X POST http://localhost:8080/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "auth_server",
    "event_type": "authentication_failure",
    "payload": {
      "username": "user@example.com",
      "failure_count": 5,
      "ip_address": "192.168.1.100"
    },
    "tags": {
      "environment": "production",
      "region": "us-east-1"
    }
  }'
```

Expected response (with alerts generated):
```json
{
  "event_id": "...",
  "accepted": true,
  "alerts_count": 1,
  "message": "Event processed successfully"
}
```

### 4. Test Malware Detection Rule

```bash
curl -X POST http://localhost:8080/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "endpoint_protection",
    "event_type": "file_execution",
    "payload": {
      "file_hash": "d41d8cd98f00b204e9800998ecf8427e",
      "process_name": "malware.exe",
      "path": "C:\\Windows\\System32\\malware.exe"
    },
    "tags": {
      "hostname": "workstation-01"
    }
  }'
```

This should trigger the malware detection rule (critical severity).

### 5. Test Data Exfiltration Detection

```bash
curl -X POST http://localhost:8080/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "network_monitoring",
    "event_type": "network_traffic",
    "payload": {
      "destination": "external:203.0.113.45",
      "data_bytes_transferred": 2000000000,
      "duration_seconds": 120,
      "protocol": "HTTPS"
    },
    "tags": {
      "source_ip": "10.0.0.50",
      "environment": "production"
    }
  }'
```

This should trigger the data exfiltration detection rule (high severity).

## Running Tests

Run all tests:
```bash
go test ./...
```

Run tests with verbose output:
```bash
go test -v ./...
```

Run tests with coverage:
```bash
go test -cover ./...
```

Run specific test package:
```bash
go test -v ./internal/engine
go test -v ./internal/rules
go test -v ./internal/alert
go test -v ./internal/integration
```

## Using Docker

### Build Docker Image

```bash
docker build -t detection-engine:latest .
```

### Run with Docker Compose

```bash
docker-compose up
```

This will start:
- Detection Engine (http://localhost:8080)
- Kafka (localhost:9092)
- Kafka UI (http://localhost:8081)

### Run Standalone Docker Container

```bash
docker run \
  -p 8080:8080 \
  -v $(pwd)/rules:/app/rules:ro \
  detection-engine:latest
```

## Sample Workflows

### Workflow 1: Monitor Authentication Attempts

The `suspicious_login.yaml` rule detects multiple failed authentication attempts:

1. Send an authentication failure event
2. Check the response for `alerts_count`
3. Review the alert details in the logs

### Workflow 2: Detect Known Malware

The `malware_detection.yaml` rule detects file execution with known malware hashes:

1. Maintain a list of known malware file hashes
2. Update the rule's condition `payload.file_hash` with known bad hashes
3. Send file execution events
4. Alerts are generated for matches

### Workflow 3: Detect Data Exfiltration

The `data_exfiltration.yaml` rule detects large data transfers to external networks:

1. Configure data transfer threshold (default: 1GB)
2. Configure external destination identifier (starts with "external:")
3. Monitor network events
4. Receive alerts for suspicious transfers

## Understanding Sample Rules

### Rule Structure

Each rule has:
- **id**: Unique identifier
- **name**: Human-readable name
- **description**: What the rule detects
- **severity**: critical/high/medium/low/info
- **source**: Which system the rule applies to
- **enabled**: true/false to enable/disable
- **definition**:
  - **event_types**: Types of events to match
  - **conditions**: All conditions must pass (AND logic)
  - **actions**: What to do when matched

### Condition Operators

- `equals`: Exact match
- `contains`: Substring match
- `starts_with`: Prefix match
- `greater_than`: Numeric comparison
- `in`: Value in list
- And more...

See [RULE_AUTHORING.md](docs/RULE_AUTHORING.md) for complete guide.

## Troubleshooting

### Service Won't Start

Check the logs:
```bash
./detection-engine --rules-dir ./rules 2>&1 | head -20
```

Verify rules directory exists:
```bash
ls -la ./rules
```

### No Alerts Generated

1. Check rule is enabled
2. Verify event_type matches
3. Verify all conditions match
4. Check rule list:
```bash
curl http://localhost:8080/rules | jq '.rules[] | {id, name, enabled}'
```

### Port Already in Use

Use a different port:
```bash
./detection-engine --rules-dir ./rules --http :8081
```

## Next Steps

1. **Create Custom Rules**: Read [docs/RULE_AUTHORING.md](docs/RULE_AUTHORING.md)
2. **Deploy to Production**: Read [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
3. **Integrate with Kafka**: Configure Kafka brokers and topic
4. **Set Up Monitoring**: Configure alerting to your SIEM

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./detection-engine --rules-dir ./rules` | Start service |
| `curl http://localhost:8080/health` | Health check |
| `curl http://localhost:8080/rules` | List rules |
| `curl -X POST http://localhost:8080/ingest -d '{...}'` | Send event |
| `go test ./...` | Run tests |
| `make build` | Build with Makefile |
| `docker-compose up` | Start with Docker |

For more information, see [README.md](README.md) and the [docs/](docs/) directory.
