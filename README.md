# Detection Engine Microservice

A threat detection microservice responsible for ingesting normalized telemetry, running signature/rule-based detections, and emitting alerts.

## Features

- **HTTP and gRPC Endpoints**: Flexible ingestion interfaces for telemetry events
- **Pluggable Rules Engine**: YAML/JSON rule format with extensible matching operators
- **Alert Publishing**: Kafka-based publisher with in-memory fallback for testing
- **Rule Validation**: Strict validation of rule structure and severity levels
- **Comprehensive Matchers**: Built-in operators including equals, contains, regex, and numeric comparisons
- **Alert Enrichment**: Supports indicators and enrichment stubs for downstream logging/monitoring
- **Thread-Safe**: Concurrent-safe rule management and detection

## Architecture

### Components

1. **Detection Engine** (`internal/engine`)
   - Core detection logic
   - Rule evaluation against telemetry events
   - Alert generation
   - Pluggable matcher system

2. **Rule Management** (`internal/rules`)
   - YAML/JSON rule loading
   - Rule validation
   - Rule lifecycle management

3. **Alert Publishing** (`internal/alert`)
   - Kafka-based alert publisher
   - In-memory publisher for testing
   - Publisher interface for custom implementations

4. **HTTP Server** (`internal/server`)
   - Telemetry ingestion endpoint
   - Rule management endpoints
   - Health checks

## Getting Started

### Prerequisites

- Go 1.21 or later
- Kafka broker (optional, for Kafka-based alert publishing)

### Installation

```bash
cd /home/engine/project
go mod download
go mod tidy
```

### Building

```bash
go build -o detection-engine ./cmd/detection-engine
```

### Running

Basic usage (with in-memory alert publisher):

```bash
./detection-engine --rules-dir ./rules
```

With Kafka publisher:

```bash
./detection-engine \
  --rules-dir ./rules \
  --kafka-brokers localhost:9092 \
  --kafka-topic detection-alerts \
  --http :8080
```

## API Endpoints

### Health Check

```bash
curl http://localhost:8080/health
```

### Ingest Telemetry Event

```bash
curl -X POST http://localhost:8080/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "auth_server",
    "event_type": "authentication_failure",
    "payload": {
      "username": "user123",
      "failure_count": 5,
      "timestamp": 1634567890
    },
    "tags": {
      "environment": "production",
      "region": "us-east-1"
    }
  }'
```

### List Rules

```bash
curl http://localhost:8080/rules
```

### Get Specific Rule

```bash
curl http://localhost:8080/rules/{rule_id}
```

## Authoring Detection Rules

### Rule Format

Detection rules are defined in YAML or JSON format with the following structure:

```yaml
id: rule_001
name: Rule Display Name
description: Detailed description of the rule
severity: high  # critical, high, medium, low, info
source: source_system
enabled: true
definition:
  event_types:
    - authentication_failure
    - login_attempt
  conditions:
    - field: payload.failure_count
      operator: greater_than
      value: 3
    - field: tags.environment
      operator: equals
      value: production
  actions:
    - type: alert
      indicators:
        - suspicious_authentication
        - brute_force_attempt
      enrichment:
        recommendation: Block user after 5 failed attempts
        action: Quarantine account
```

### Field References

Rules can reference different parts of telemetry events:

- **Simple fields**: `source`, `event_type`, `id`
- **Tags**: `tags.key_name`
- **Payload fields**: `payload.field_name`
- **Nested payload**: Use dot notation (e.g., `payload.nested.field`)

### Operators

#### String Operators

- `equals`: Exact string match
- `not_equals`: String does not match
- `contains`: String contains substring
- `not_contains`: String does not contain substring
- `starts_with`: String starts with prefix
- `ends_with`: String ends with suffix
- `in`: Value is in list
- `not_in`: Value is not in list

#### Numeric Operators

- `greater_than`: Value > threshold
- `less_than`: Value < threshold

#### Existence Operators

- `exists`: Field exists
- `not_exists`: Field does not exist
- `regex`: Regex pattern match (simple substring matching in current implementation)

### Severity Levels

- **critical**: Immediate action required, severe security impact
- **high**: Significant security concern, quick investigation needed
- **medium**: Notable security event, should be investigated
- **low**: Minor security event, monitor for patterns
- **info**: Informational, no immediate action required

## Sample Rules

### Suspicious Login Detection

Detects multiple failed authentication attempts within a time window:

```yaml
id: rule_001
name: Suspicious Login Detection
description: Detects login attempts with high failure count
severity: high
source: authentication
enabled: true
definition:
  event_types:
    - authentication_failure
  conditions:
    - field: event_type
      operator: equals
      value: authentication_failure
    - field: payload.failure_count
      operator: greater_than
      value: 3
  actions:
    - type: alert
      indicators:
        - suspicious_authentication
        - failed_login_attempts
      enrichment:
        recommendation: Investigate user account for compromised credentials
        action: Block user after 5 failed attempts
```

### Malware Detection

Detects execution of files with known malware hashes:

```yaml
id: rule_002
name: Known Malware Hash Detection
description: Detects files matching known malware signatures
severity: critical
source: endpoint_protection
enabled: true
definition:
  event_types:
    - file_execution
    - process_created
  conditions:
    - field: payload.file_hash
      operator: in
      value:
        - "d41d8cd98f00b204e9800998ecf8427e"
        - "c4ca4238a0b923820dcc509a6f75849b"
  actions:
    - type: alert
      indicators:
        - known_malware
        - file_hash_match
      enrichment:
        action: Quarantine file immediately
```

### Data Exfiltration Detection

Detects large data transfers to external networks:

```yaml
id: rule_003
name: Potential Data Exfiltration
description: Detects large data transfers to external networks
severity: high
source: network_monitoring
enabled: true
definition:
  event_types:
    - network_traffic
  conditions:
    - field: payload.data_bytes
      operator: greater_than
      value: 1073741824  # 1 GB
    - field: payload.destination
      operator: starts_with
      value: "external:"
  actions:
    - type: alert
      indicators:
        - data_exfiltration
      enrichment:
        action: Review and potentially block connection
```

## Alert Structure

When a rule matches, an alert is generated with the following structure:

```json
{
  "id": "alert_uuid",
  "rule_id": "rule_001",
  "rule_name": "Suspicious Login Detection",
  "severity": "high",
  "timestamp": 1634567890000,
  "event_id": "event_uuid",
  "indicators": [
    "suspicious_authentication",
    "failed_login_attempts"
  ],
  "enrichment": {
    "recommendation": "Investigate user account",
    "action": "Block user after 5 failed attempts"
  },
  "description": "Detects login attempts with high failure count",
  "metadata": {
    "rule_source": "authentication",
    "event_source": "auth_server"
  }
}
```

## Testing

Run all tests:

```bash
go test ./...
```

Run tests with coverage:

```bash
go test -cover ./...
```

Run specific test file:

```bash
go test -v ./internal/engine -run TestDetectorDetectSimpleMatch
```

### Test Coverage

The project includes comprehensive unit tests covering:

- **Detector Tests** (`internal/engine/detector_test.go`)
  - Rule addition and retrieval
  - Event matching with various conditions
  - Multiple condition evaluation
  - Tag-based filtering
  - Disabled rule handling
  - Alert generation

- **Matcher Tests** (`internal/engine/matchers_test.go`)
  - All operator types (equals, contains, regex, etc.)
  - Numeric comparisons
  - String operations
  - Payload extraction
  - Nested field access

- **Rule Loader Tests** (`internal/rules/loader_test.go`)
  - YAML/JSON parsing
  - Rule validation
  - Severity validation
  - Batch rule loading
  - File format handling

- **Publisher Tests** (`internal/alert/publisher_test.go`)
  - In-memory alert publishing
  - Multiple alert handling
  - Publisher isolation

## Deployment

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o detection-engine ./cmd/detection-engine

FROM alpine:latest
COPY --from=builder /app/detection-engine /app/detection-engine
COPY --from=builder /app/rules /app/rules
EXPOSE 8080
CMD ["/app/detection-engine", "--rules-dir", "/app/rules"]
```

Build and run:

```bash
docker build -t detection-engine:latest .
docker run -p 8080:8080 detection-engine:latest
```

### Kubernetes Deployment

Example Kubernetes manifests:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: detection-engine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: detection-engine
  template:
    metadata:
      labels:
        app: detection-engine
    spec:
      containers:
      - name: detection-engine
        image: detection-engine:latest
        ports:
        - containerPort: 8080
        env:
        - name: KAFKA_BROKERS
          value: "kafka:9092"
        - name: KAFKA_TOPIC
          value: "detection-alerts"
        volumeMounts:
        - name: rules
          mountPath: /app/rules
      volumes:
      - name: rules
        configMap:
          name: detection-rules
---
apiVersion: v1
kind: Service
metadata:
  name: detection-engine
spec:
  selector:
    app: detection-engine
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
  type: LoadBalancer
```

## Rule Lifecycle

### Rule Loading

1. Rules are loaded from the specified directory on startup
2. Rules are validated for structure and required fields
3. Rules are registered with the detector engine
4. Invalid rules are logged and skipped

### Rule Execution

1. Incoming telemetry event is received via HTTP/gRPC
2. Event is validated for required fields
3. All enabled rules are evaluated against the event
4. For each matching rule, an alert is generated
5. Alerts are published to the configured publisher

### Rule Update

To update rules:

1. Modify rule files in the rules directory
2. Restart the detection engine service
3. New rules will be loaded on startup

## Configuration

### Environment Variables

- `DETECTION_HTTP_ADDR`: HTTP server address (default: `:8080`)
- `DETECTION_RULES_DIR`: Path to rules directory (default: `./rules`)
- `DETECTION_KAFKA_BROKERS`: Kafka brokers (optional)
- `DETECTION_KAFKA_TOPIC`: Kafka topic for alerts (default: `detection-alerts`)

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

## Extending the Engine

### Custom Matchers

Implement the `Matcher` interface to create custom matching logic:

```go
type CustomMatcher struct{}

func (cm *CustomMatcher) Match(event *TelemetryEvent, condition Condition) bool {
    // Custom matching logic
    return true
}

// Register the matcher
detector.RegisterMatcher("custom", &CustomMatcher{})
```

### Custom Publishers

Implement the `Publisher` interface for custom alert destinations:

```go
type CustomPublisher struct{}

func (cp *CustomPublisher) Publish(ctx context.Context, alert *Alert) error {
    // Custom publishing logic
    return nil
}

func (cp *CustomPublisher) Close() error {
    return nil
}
```

## Performance Considerations

- **Concurrent Detection**: Multiple events can be processed concurrently
- **Rule Optimization**: Order conditions from most restrictive to least restrictive
- **Payload Parsing**: Large JSON payloads are parsed on-demand
- **Alert Batching**: Consider batching alerts before publishing to Kafka

## Troubleshooting

### No alerts generated

1. Check rule is enabled: `enabled: true`
2. Verify event_type matches rule condition
3. Check all conditions are satisfied
4. Enable debug logging for detailed matching information

### Rules not loading

1. Verify rules directory path is correct
2. Check rule files are valid YAML/JSON
3. Check rule validation requirements (name, severity, event_types, conditions)
4. Check file permissions

### Alert publishing failures

1. Verify Kafka broker connectivity
2. Check Kafka topic exists
3. Verify network configuration

## License

This project is provided as-is for security operations.

## Support

For issues and questions, please refer to the project documentation or contact the security team.
