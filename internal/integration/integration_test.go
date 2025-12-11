package integration

import (
	"context"
	"encoding/json"
	"testing"
	"time"

	"github.com/detection-engine/internal/alert"
	"github.com/detection-engine/internal/engine"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestFullDetectionPipeline(t *testing.T) {
	// Initialize detector and publisher
	detector := engine.NewDetector()
	publisher := alert.NewInMemoryPublisher()

	// Create a detection rule
	rule := &engine.Rule{
		ID:          "rule_001",
		Name:        "Test Rule",
		Description: "Test rule for integration testing",
		Severity:    "high",
		Source:      "test",
		Enabled:     true,
		Definition: engine.RuleDefinition{
			EventTypes: []string{"test_event"},
			Conditions: []engine.Condition{
				{
					Field:    "event_type",
					Operator: "equals",
					Value:    "test_event",
				},
			},
			Actions: []engine.Action{
				{
					Type: "alert",
					Indicators: []string{
						"test_indicator_1",
						"test_indicator_2",
					},
					Enrichment: map[string]string{
						"recommendation": "Test recommendation",
						"action":         "Test action",
					},
				},
			},
		},
	}

	err := detector.AddRule(rule)
	require.NoError(t, err)

	// Create telemetry event
	payload := json.RawMessage(`{
		"field1": "value1",
		"field2": 42
	}`)

	event := &engine.TelemetryEvent{
		ID:        "event_001",
		Source:    "test_source",
		EventType: "test_event",
		Timestamp: time.Now().UnixMilli(),
		Payload:   payload,
		Tags: map[string]string{
			"env": "test",
		},
	}

	// Run detection
	alerts := detector.Detect(event)
	require.Equal(t, 1, len(alerts))

	// Publish alert
	ctx := context.Background()
	err = publisher.Publish(ctx, alerts[0])
	require.NoError(t, err)

	// Verify published alerts
	publishedAlerts := publisher.GetAlerts()
	require.Equal(t, 1, len(publishedAlerts))

	alert := publishedAlerts[0]
	assert.Equal(t, rule.ID, alert.RuleID)
	assert.Equal(t, rule.Name, alert.RuleName)
	assert.Equal(t, "high", alert.Severity)
	assert.Equal(t, event.ID, alert.EventID)
	assert.Contains(t, alert.Indicators, "test_indicator_1")
	assert.Contains(t, alert.Indicators, "test_indicator_2")
	assert.Equal(t, "Test recommendation", alert.Enrichment["recommendation"])
	assert.Equal(t, "Test action", alert.Enrichment["action"])
}

func TestMultipleRulesMultipleMatches(t *testing.T) {
	detector := engine.NewDetector()
	publisher := alert.NewInMemoryPublisher()

	// Create multiple rules
	rule1 := &engine.Rule{
		ID:       "rule_1",
		Name:     "Rule 1",
		Severity: "high",
		Source:   "test",
		Enabled:  true,
		Definition: engine.RuleDefinition{
			EventTypes: []string{"auth_event"},
			Conditions: []engine.Condition{
				{Field: "event_type", Operator: "equals", Value: "auth_event"},
			},
			Actions: []engine.Action{
				{Type: "alert", Indicators: []string{"indicator_1"}},
			},
		},
	}

	rule2 := &engine.Rule{
		ID:       "rule_2",
		Name:     "Rule 2",
		Severity: "medium",
		Source:   "test",
		Enabled:  true,
		Definition: engine.RuleDefinition{
			EventTypes: []string{"auth_event"},
			Conditions: []engine.Condition{
				{Field: "event_type", Operator: "equals", Value: "auth_event"},
				{Field: "tags.env", Operator: "equals", Value: "prod"},
			},
			Actions: []engine.Action{
				{Type: "alert", Indicators: []string{"indicator_2"}},
			},
		},
	}

	detector.AddRule(rule1)
	detector.AddRule(rule2)

	// Event matching both rules
	event := &engine.TelemetryEvent{
		ID:        "evt_001",
		Source:    "auth",
		EventType: "auth_event",
		Timestamp: time.Now().UnixMilli(),
		Payload:   json.RawMessage(`{}`),
		Tags: map[string]string{
			"env": "prod",
		},
	}

	alerts := detector.Detect(event)
	assert.Equal(t, 2, len(alerts))

	// Both rules should have triggered
	ruleIDs := make(map[string]bool)
	for _, a := range alerts {
		ruleIDs[a.RuleID] = true
	}
	assert.True(t, ruleIDs["rule_1"])
	assert.True(t, ruleIDs["rule_2"])

	// Publish all alerts
	ctx := context.Background()
	for _, a := range alerts {
		err := publisher.Publish(ctx, a)
		require.NoError(t, err)
	}

	// Verify all alerts published
	publishedAlerts := publisher.GetAlerts()
	assert.Equal(t, 2, len(publishedAlerts))
}

func TestComplexConditionEvaluation(t *testing.T) {
	detector := engine.NewDetector()

	// Rule with multiple conditions
	rule := &engine.Rule{
		ID:       "complex_rule",
		Name:     "Complex Condition Rule",
		Severity: "critical",
		Source:   "test",
		Enabled:  true,
		Definition: engine.RuleDefinition{
			EventTypes: []string{"network_event"},
			Conditions: []engine.Condition{
				{
					Field:    "event_type",
					Operator: "equals",
					Value:    "network_event",
				},
				{
					Field:    "payload.bytes_transferred",
					Operator: "greater_than",
					Value:    float64(1000000),
				},
				{
					Field:    "payload.destination",
					Operator: "starts_with",
					Value:    "external:",
				},
				{
					Field:    "tags.monitored",
					Operator: "equals",
					Value:    "true",
				},
			},
			Actions: []engine.Action{
				{
					Type:       "alert",
					Indicators: []string{"data_exfiltration"},
				},
			},
		},
	}

	detector.AddRule(rule)

	// Event matching all conditions
	payload := json.RawMessage(`{
		"bytes_transferred": 5000000,
		"destination": "external:192.168.1.1"
	}`)

	event := &engine.TelemetryEvent{
		ID:        "evt_complex",
		Source:    "network_monitor",
		EventType: "network_event",
		Timestamp: time.Now().UnixMilli(),
		Payload:   payload,
		Tags: map[string]string{
			"monitored": "true",
		},
	}

	alerts := detector.Detect(event)
	require.Equal(t, 1, len(alerts))
	assert.Equal(t, "critical", alerts[0].Severity)

	// Event with one condition failing
	payload2 := json.RawMessage(`{
		"bytes_transferred": 500000,
		"destination": "external:192.168.1.1"
	}`)

	event2 := &engine.TelemetryEvent{
		ID:        "evt_complex_2",
		Source:    "network_monitor",
		EventType: "network_event",
		Timestamp: time.Now().UnixMilli(),
		Payload:   payload2,
		Tags: map[string]string{
			"monitored": "true",
		},
	}

	alerts2 := detector.Detect(event2)
	assert.Equal(t, 0, len(alerts2))
}

func TestRuleDisabling(t *testing.T) {
	detector := engine.NewDetector()

	rule := &engine.Rule{
		ID:       "disabled_rule",
		Name:     "Disabled Rule",
		Severity: "high",
		Source:   "test",
		Enabled:  false, // Disabled
		Definition: engine.RuleDefinition{
			EventTypes: []string{"test_event"},
			Conditions: []engine.Condition{
				{Field: "event_type", Operator: "equals", Value: "test_event"},
			},
			Actions: []engine.Action{},
		},
	}

	detector.AddRule(rule)

	event := &engine.TelemetryEvent{
		ID:        "evt_disabled",
		Source:    "test",
		EventType: "test_event",
		Timestamp: time.Now().UnixMilli(),
		Payload:   json.RawMessage(`{}`),
		Tags:      map[string]string{},
	}

	alerts := detector.Detect(event)
	assert.Equal(t, 0, len(alerts))
}

func TestAlertEnrichment(t *testing.T) {
	detector := engine.NewDetector()
	publisher := alert.NewInMemoryPublisher()

	rule := &engine.Rule{
		ID:       "enrichment_rule",
		Name:     "Enrichment Test Rule",
		Severity: "medium",
		Source:   "test",
		Enabled:  true,
		Definition: engine.RuleDefinition{
			EventTypes: []string{"security_event"},
			Conditions: []engine.Condition{
				{Field: "event_type", Operator: "equals", Value: "security_event"},
			},
			Actions: []engine.Action{
				{
					Type:       "alert",
					Indicators: []string{"incident", "investigation"},
					Enrichment: map[string]string{
						"severity_level":   "medium",
						"soc_team_needed":  "yes",
						"escalation":       "within_2_hours",
						"customer_impact":  "potential",
						"remediation_time": "4_hours",
					},
				},
			},
		},
	}

	detector.AddRule(rule)

	event := &engine.TelemetryEvent{
		ID:        "evt_enrichment",
		Source:    "security_monitor",
		EventType: "security_event",
		Timestamp: time.Now().UnixMilli(),
		Payload:   json.RawMessage(`{}`),
		Tags:      map[string]string{},
	}

	alerts := detector.Detect(event)
	require.Equal(t, 1, len(alerts))

	ctx := context.Background()
	err := publisher.Publish(ctx, alerts[0])
	require.NoError(t, err)

	publishedAlerts := publisher.GetAlerts()
	assert.Equal(t, 1, len(publishedAlerts))

	alert := publishedAlerts[0]
	assert.Equal(t, "medium", alert.Enrichment["severity_level"])
	assert.Equal(t, "yes", alert.Enrichment["soc_team_needed"])
	assert.Equal(t, "within_2_hours", alert.Enrichment["escalation"])
	assert.Equal(t, "potential", alert.Enrichment["customer_impact"])
	assert.Equal(t, "4_hours", alert.Enrichment["remediation_time"])
}

func TestConcurrentDetection(t *testing.T) {
	detector := engine.NewDetector()

	rule := &engine.Rule{
		ID:       "concurrent_rule",
		Name:     "Concurrent Test Rule",
		Severity: "high",
		Source:   "test",
		Enabled:  true,
		Definition: engine.RuleDefinition{
			EventTypes: []string{"event"},
			Conditions: []engine.Condition{
				{Field: "event_type", Operator: "equals", Value: "event"},
			},
			Actions: []engine.Action{},
		},
	}

	detector.AddRule(rule)

	// Simulate concurrent event processing
	eventCount := 100
	alertsChan := make(chan []*engine.Alert, eventCount)

	for i := 1; i <= eventCount; i++ {
		go func(eventID int) {
			event := &engine.TelemetryEvent{
				ID:        "evt_" + string(rune(eventID)),
				Source:    "test",
				EventType: "event",
				Timestamp: time.Now().UnixMilli(),
				Payload:   json.RawMessage(`{}`),
				Tags:      map[string]string{},
			}
			alerts := detector.Detect(event)
			alertsChan <- alerts
		}(i)
	}

	// Collect results
	totalAlerts := 0
	for i := 0; i < eventCount; i++ {
		alerts := <-alertsChan
		totalAlerts += len(alerts)
	}

	assert.Equal(t, eventCount, totalAlerts)
}
