package engine

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestDetectorAddRule(t *testing.T) {
	detector := NewDetector()
	rule := &Rule{
		Name:     "Test Rule",
		Severity: "high",
		Source:   "test",
		Enabled:  true,
		Definition: RuleDefinition{
			EventTypes: []string{"test_event"},
			Conditions: []Condition{
				{
					Field:    "event_type",
					Operator: "equals",
					Value:    "test_event",
				},
			},
			Actions: []Action{
				{
					Type:       "alert",
					Indicators: []string{"test_indicator"},
				},
			},
		},
	}

	err := detector.AddRule(rule)
	assert.NoError(t, err)
	assert.NotEmpty(t, rule.ID)
	assert.NotZero(t, rule.CreatedAt)
	assert.NotZero(t, rule.UpdatedAt)

	retrieved, ok := detector.GetRule(rule.ID)
	assert.True(t, ok)
	assert.Equal(t, rule.Name, retrieved.Name)
}

func TestDetectorListRules(t *testing.T) {
	detector := NewDetector()

	rules := detector.ListRules()
	assert.Equal(t, 0, len(rules))

	rule1 := &Rule{
		Name:     "Rule 1",
		Severity: "high",
		Source:   "test",
		Enabled:  true,
		Definition: RuleDefinition{
			EventTypes: []string{"event1"},
			Conditions: []Condition{},
			Actions:    []Action{},
		},
	}

	rule2 := &Rule{
		Name:     "Rule 2",
		Severity: "medium",
		Source:   "test",
		Enabled:  true,
		Definition: RuleDefinition{
			EventTypes: []string{"event2"},
			Conditions: []Condition{},
			Actions:    []Action{},
		},
	}

	detector.AddRule(rule1)
	detector.AddRule(rule2)

	rules = detector.ListRules()
	assert.Equal(t, 2, len(rules))
}

func TestDetectorDetectSimpleMatch(t *testing.T) {
	detector := NewDetector()

	rule := &Rule{
		Name:     "Simple Match Rule",
		Severity: "high",
		Source:   "test",
		Enabled:  true,
		Definition: RuleDefinition{
			EventTypes: []string{"login_attempt"},
			Conditions: []Condition{
				{
					Field:    "event_type",
					Operator: "equals",
					Value:    "login_attempt",
				},
			},
			Actions: []Action{
				{
					Type:       "alert",
					Indicators: []string{"suspicious_login"},
				},
			},
		},
	}

	detector.AddRule(rule)

	payload := json.RawMessage(`{"username": "user1"}`)
	event := &TelemetryEvent{
		ID:        "evt1",
		Source:    "auth",
		EventType: "login_attempt",
		Timestamp: time.Now().UnixMilli(),
		Payload:   payload,
		Tags:      map[string]string{},
	}

	alerts := detector.Detect(event)
	require.Equal(t, 1, len(alerts))
	assert.Equal(t, rule.ID, alerts[0].RuleID)
	assert.Equal(t, "high", alerts[0].Severity)
	assert.Contains(t, alerts[0].Indicators, "suspicious_login")
}

func TestDetectorDetectPayloadCondition(t *testing.T) {
	detector := NewDetector()

	rule := &Rule{
		Name:     "Payload Match Rule",
		Severity: "critical",
		Source:   "test",
		Enabled:  true,
		Definition: RuleDefinition{
			EventTypes: []string{"authentication_failure"},
			Conditions: []Condition{
				{
					Field:    "event_type",
					Operator: "equals",
					Value:    "authentication_failure",
				},
				{
					Field:    "payload.failure_count",
					Operator: "greater_than",
					Value:    float64(3),
				},
			},
			Actions: []Action{
				{
					Type:       "alert",
					Indicators: []string{"failed_login_attempts"},
					Enrichment: map[string]string{
						"recommendation": "Block user",
					},
				},
			},
		},
	}

	detector.AddRule(rule)

	payload := json.RawMessage(`{"failure_count": 5, "username": "attacker"}`)
	event := &TelemetryEvent{
		ID:        "evt2",
		Source:    "auth",
		EventType: "authentication_failure",
		Timestamp: time.Now().UnixMilli(),
		Payload:   payload,
		Tags:      map[string]string{},
	}

	alerts := detector.Detect(event)
	require.Equal(t, 1, len(alerts))
	assert.Equal(t, "critical", alerts[0].Severity)
	assert.Equal(t, "Block user", alerts[0].Enrichment["recommendation"])
}

func TestDetectorDetectNoMatch(t *testing.T) {
	detector := NewDetector()

	rule := &Rule{
		Name:     "No Match Rule",
		Severity: "medium",
		Source:   "test",
		Enabled:  true,
		Definition: RuleDefinition{
			EventTypes: []string{"malware_detected"},
			Conditions: []Condition{
				{
					Field:    "event_type",
					Operator: "equals",
					Value:    "malware_detected",
				},
			},
			Actions: []Action{},
		},
	}

	detector.AddRule(rule)

	payload := json.RawMessage(`{"severity": "low"}`)
	event := &TelemetryEvent{
		ID:        "evt3",
		Source:    "av",
		EventType: "file_scanned",
		Timestamp: time.Now().UnixMilli(),
		Payload:   payload,
		Tags:      map[string]string{},
	}

	alerts := detector.Detect(event)
	assert.Equal(t, 0, len(alerts))
}

func TestDetectorDetectDisabledRule(t *testing.T) {
	detector := NewDetector()

	rule := &Rule{
		Name:     "Disabled Rule",
		Severity: "high",
		Source:   "test",
		Enabled:  false,
		Definition: RuleDefinition{
			EventTypes: []string{"test_event"},
			Conditions: []Condition{
				{
					Field:    "event_type",
					Operator: "equals",
					Value:    "test_event",
				},
			},
			Actions: []Action{},
		},
	}

	detector.AddRule(rule)

	payload := json.RawMessage(`{}`)
	event := &TelemetryEvent{
		ID:        "evt4",
		Source:    "test",
		EventType: "test_event",
		Timestamp: time.Now().UnixMilli(),
		Payload:   payload,
		Tags:      map[string]string{},
	}

	alerts := detector.Detect(event)
	assert.Equal(t, 0, len(alerts))
}

func TestDetectorDetectWithTags(t *testing.T) {
	detector := NewDetector()

	rule := &Rule{
		Name:     "Tag Match Rule",
		Severity: "medium",
		Source:   "test",
		Enabled:  true,
		Definition: RuleDefinition{
			EventTypes: []string{"access_log"},
			Conditions: []Condition{
				{
					Field:    "tags.environment",
					Operator: "equals",
					Value:    "production",
				},
			},
			Actions: []Action{},
		},
	}

	detector.AddRule(rule)

	payload := json.RawMessage(`{}`)
	event := &TelemetryEvent{
		ID:        "evt5",
		Source:    "webserver",
		EventType: "access_log",
		Timestamp: time.Now().UnixMilli(),
		Payload:   payload,
		Tags: map[string]string{
			"environment": "production",
			"region":      "us-east-1",
		},
	}

	alerts := detector.Detect(event)
	require.Equal(t, 1, len(alerts))
}

func TestDetectorMultipleConditions(t *testing.T) {
	detector := NewDetector()

	rule := &Rule{
		Name:     "Multi Condition Rule",
		Severity: "high",
		Source:   "test",
		Enabled:  true,
		Definition: RuleDefinition{
			EventTypes: []string{"network_traffic"},
			Conditions: []Condition{
				{
					Field:    "event_type",
					Operator: "equals",
					Value:    "network_traffic",
				},
				{
					Field:    "payload.destination",
					Operator: "starts_with",
					Value:    "external:",
				},
				{
					Field:    "payload.bytes",
					Operator: "greater_than",
					Value:    float64(1000000000),
				},
			},
			Actions: []Action{
				{
					Type:       "alert",
					Indicators: []string{"data_exfiltration"},
				},
			},
		},
	}

	detector.AddRule(rule)

	payload := json.RawMessage(`{"destination": "external:192.168.1.1", "bytes": 2000000000}`)
	event := &TelemetryEvent{
		ID:        "evt6",
		Source:    "network_monitor",
		EventType: "network_traffic",
		Timestamp: time.Now().UnixMilli(),
		Payload:   payload,
		Tags:      map[string]string{},
	}

	alerts := detector.Detect(event)
	require.Equal(t, 1, len(alerts))
	assert.Contains(t, alerts[0].Indicators, "data_exfiltration")
}
