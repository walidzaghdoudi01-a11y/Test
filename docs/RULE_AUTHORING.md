# Detection Rule Authoring Guide

This guide provides detailed instructions for creating and testing detection rules for the Detection Engine microservice.

## Table of Contents

1. [Rule Structure](#rule-structure)
2. [Field References](#field-references)
3. [Operators](#operators)
4. [Best Practices](#best-practices)
5. [Testing Rules](#testing-rules)
6. [Common Patterns](#common-patterns)

## Rule Structure

Every detection rule must follow this YAML or JSON structure:

```yaml
id: unique_rule_id
name: Human Readable Rule Name
description: Detailed description of what the rule detects
severity: critical|high|medium|low|info
source: source_system_name
enabled: true|false
definition:
  event_types:
    - event_type_1
    - event_type_2
  conditions:
    - field: field_path
      operator: operator_name
      value: comparison_value
  actions:
    - type: alert
      indicators:
        - indicator_1
        - indicator_2
      enrichment:
        key1: value1
        key2: value2
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier for the rule (e.g., `rule_001`) |
| name | string | Yes | Human-readable rule name |
| description | string | Yes | Detailed description of detection logic |
| severity | string | Yes | Alert severity level (critical, high, medium, low, info) |
| source | string | Yes | Source system or domain (e.g., authentication, network) |
| enabled | boolean | No | Enable/disable rule (default: true) |
| definition.event_types | array | Yes | Event types to match (at least one required) |
| definition.conditions | array | Yes | Matching conditions (at least one required) |
| definition.actions | array | No | Actions to take when rule matches |

## Field References

Rules can reference different parts of a telemetry event using dot-notation paths:

### System Fields

```yaml
field: source              # Event source system
field: event_type          # Event type
field: id                  # Event ID
```

### Tag Fields

```yaml
field: tags.environment    # Access tag value
field: tags.region         # Nested tag access
```

### Payload Fields

```yaml
field: payload.username    # Direct field in payload
field: payload.data.count  # Nested field in payload JSON
```

## Operators

### String Operators

#### equals
Exact string match

```yaml
- field: event_type
  operator: equals
  value: authentication_failure
```

#### not_equals
String does not match

```yaml
- field: source
  operator: not_equals
  value: trusted_system
```

#### contains
String contains substring

```yaml
- field: payload.message
  operator: contains
  value: "error"
```

#### not_contains
String does not contain substring

```yaml
- field: payload.message
  operator: not_contains
  value: "success"
```

#### starts_with
String starts with prefix

```yaml
- field: payload.destination
  operator: starts_with
  value: "external:"
```

#### ends_with
String ends with suffix

```yaml
- field: payload.domain
  operator: ends_with
  value: ".malicious.com"
```

### List Operators

#### in
Value is in the provided list

```yaml
- field: payload.file_hash
  operator: in
  value:
    - "d41d8cd98f00b204e9800998ecf8427e"
    - "c4ca4238a0b923820dcc509a6f75849b"
    - "c81e728d9d4c2f636f067f89cc14862c"
```

#### not_in
Value is not in the provided list

```yaml
- field: tags.country
  operator: not_in
  value:
    - US
    - CA
    - UK
```

### Numeric Operators

#### greater_than
Numeric value greater than threshold

```yaml
- field: payload.failure_count
  operator: greater_than
  value: 5
```

#### less_than
Numeric value less than threshold

```yaml
- field: payload.cpu_usage
  operator: less_than
  value: 10
```

### Existence Operators

#### exists
Field exists (value can be any)

```yaml
- field: payload.error_code
  operator: exists
```

#### not_exists
Field does not exist

```yaml
- field: payload.optional_field
  operator: not_exists
```

### Pattern Operators

#### regex
Regex pattern match (currently substring matching)

```yaml
- field: payload.filename
  operator: regex
  value: ".*\\.exe$"
```

## Best Practices

### 1. Use Descriptive Names

❌ Bad:
```yaml
name: Rule 1
```

✅ Good:
```yaml
name: Suspicious Authentication from Unusual Location
```

### 2. Order Conditions by Restrictiveness

Place the most restrictive conditions first to fail fast:

```yaml
conditions:
  - field: event_type
    operator: in
    value: [authentication_failure, login_attempt]
  - field: payload.failure_count
    operator: greater_than
    value: 5
  - field: tags.environment
    operator: equals
    value: production
```

### 3. Use Appropriate Severity

- **critical**: Breach in progress, immediate incident response required
- **high**: Suspicious activity, needs investigation within hours
- **medium**: Notable security event, investigate within 24 hours
- **low**: Minor anomaly, informational
- **info**: Non-security event, for logging purposes

### 4. Provide Clear Indicators

Indicators should describe what was detected:

```yaml
indicators:
  - brute_force_attack
  - failed_authentication
  - suspicious_account_behavior
```

### 5. Include Remediation Guidance

Use enrichment fields to guide response:

```yaml
enrichment:
  recommendation: Reset user password and review account activity
  action: Lock account for manual review
  impact: Medium - affects user productivity
  soc_team: Yes
```

### 6. Document Complex Logic

For rules with multiple conditions, add clear descriptions:

```yaml
name: Suspicious Data Access Pattern
description: |
  Detects when a user accesses sensitive data outside their normal
  working hours from a location that differs from their baseline
  by more than 1000 miles. This indicates potential credential
  compromise or unauthorized access.
```

### 7. Test with Real Data

Ensure rules match intended events and avoid false positives:

- Test with normal operations data
- Test with attack simulation data
- Validate field paths are correct
- Verify numeric thresholds are appropriate

## Testing Rules

### Unit Testing in Code

```go
func TestSuspiciousLoginRule(t *testing.T) {
    detector := engine.NewDetector()
    
    rule := &engine.Rule{
        ID:       "rule_suspicious_login",
        Name:     "Suspicious Login",
        Severity: "high",
        Source:   "auth",
        Enabled:  true,
        Definition: engine.RuleDefinition{
            EventTypes: []string{"authentication_failure"},
            Conditions: []engine.Condition{
                {
                    Field:    "payload.failure_count",
                    Operator: "greater_than",
                    Value:    float64(3),
                },
            },
            Actions: []engine.Action{
                {
                    Type:       "alert",
                    Indicators: []string{"suspicious_authentication"},
                },
            },
        },
    }
    
    detector.AddRule(rule)
    
    payload := json.RawMessage(`{"failure_count": 5}`)
    event := &engine.TelemetryEvent{
        Source:    "auth",
        EventType: "authentication_failure",
        Payload:   payload,
    }
    
    alerts := detector.Detect(event)
    assert.Equal(t, 1, len(alerts))
    assert.Equal(t, "high", alerts[0].Severity)
}
```

### Manual Testing

```bash
# Start the service
./detection-engine --rules-dir ./rules

# Test with curl
curl -X POST http://localhost:8080/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "auth",
    "event_type": "authentication_failure",
    "payload": {
      "username": "testuser",
      "failure_count": 5
    }
  }'
```

## Common Patterns

### Brute Force Detection

```yaml
id: brute_force_detection
name: Brute Force Attack Detection
description: Detects multiple failed login attempts
severity: high
source: authentication
enabled: true
definition:
  event_types:
    - authentication_failure
  conditions:
    - field: payload.failure_count
      operator: greater_than
      value: 5
  actions:
    - type: alert
      indicators:
        - brute_force_attempt
        - account_lockout_recommended
      enrichment:
        action: Lock account
```

### Malware Detection

```yaml
id: malware_hash_match
name: Known Malware Detection
description: Detects execution of known malware
severity: critical
source: endpoint
enabled: true
definition:
  event_types:
    - file_execution
  conditions:
    - field: payload.file_hash
      operator: in
      value:
        - "hash_of_malware_1"
        - "hash_of_malware_2"
  actions:
    - type: alert
      indicators:
        - known_malware
        - file_hash_match
      enrichment:
        action: Quarantine file immediately
```

### Data Exfiltration Detection

```yaml
id: data_exfiltration
name: Data Exfiltration
description: Detects unusual large data transfers
severity: high
source: network
enabled: true
definition:
  event_types:
    - network_traffic
  conditions:
    - field: payload.bytes_transferred
      operator: greater_than
      value: 1073741824  # 1GB
    - field: payload.destination
      operator: starts_with
      value: "external:"
  actions:
    - type: alert
      indicators:
        - data_exfiltration
```

### Privilege Escalation Detection

```yaml
id: privilege_escalation
name: Privilege Escalation Attempt
description: Detects suspicious privilege elevation
severity: high
source: authentication
enabled: true
definition:
  event_types:
    - privilege_change
  conditions:
    - field: payload.old_privilege_level
      operator: equals
      value: user
    - field: payload.new_privilege_level
      operator: equals
      value: admin
    - field: tags.environment
      operator: equals
      value: production
  actions:
    - type: alert
      indicators:
        - privilege_escalation
      enrichment:
        recommendation: Review privilege change request
```

### Insider Threat Detection

```yaml
id: insider_threat
name: Potential Insider Threat
description: Detects behaviors indicative of insider threat
severity: high
source: endpoint_dlp
enabled: true
definition:
  event_types:
    - data_copy
    - usb_device_connected
  conditions:
    - field: event_type
      operator: in
      value:
        - data_copy
        - usb_device_connected
    - field: payload.file_classification
      operator: equals
      value: confidential
  actions:
    - type: alert
      indicators:
        - insider_threat
        - data_access_anomaly
      enrichment:
        recommendation: Investigate user activity logs
```

## Rule Validation Checklist

Before deploying a rule, verify:

- ✅ Rule ID is unique
- ✅ Rule name is descriptive
- ✅ Severity level is appropriate
- ✅ Description explains detection logic
- ✅ At least one event_type is specified
- ✅ At least one condition is specified
- ✅ All field paths are valid
- ✅ All operators are supported
- ✅ Numeric thresholds are reasonable
- ✅ List values are in proper format
- ✅ Test rule with sample events
- ✅ Verify no false positives
- ✅ Verify matches intended attacks

## Advanced Topics

### Dynamic Thresholds

Consider environment-specific thresholds:

```yaml
definition:
  conditions:
    - field: tags.environment
      operator: equals
      value: production
    - field: payload.response_time_ms
      operator: greater_than
      value: 5000  # 5 seconds for production
```

### Time-Based Rules

(Future enhancement) Rules could consider time windows:

```yaml
definition:
  conditions:
    - field: payload.failure_count
      operator: greater_than
      value: 5
    - field: payload.time_window_seconds
      operator: less_than
      value: 300  # All failures in 5 minutes
```

### Correlation Rules

(Future enhancement) Correlate multiple event types:

```yaml
definition:
  event_types:
    - login_success
    - file_access
    - database_query
  conditions:
    # All events must occur within a time window
```
