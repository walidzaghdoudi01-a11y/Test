package alert

import (
	"context"
	"testing"
	"time"

	"github.com/detection-engine/internal/engine"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestInMemoryPublisherPublish(t *testing.T) {
	publisher := NewInMemoryPublisher()

	alert := &engine.Alert{
		ID:       "alert_001",
		RuleID:   "rule_001",
		RuleName: "Test Rule",
		Severity: "high",
		Timestamp: time.Now().UnixMilli(),
		EventID:  "event_001",
		Indicators: []string{"indicator1", "indicator2"},
		Enrichment: map[string]string{
			"action": "investigate",
		},
		Description: "Test alert",
		Metadata: map[string]string{
			"source": "test",
		},
	}

	ctx := context.Background()
	err := publisher.Publish(ctx, alert)
	require.NoError(t, err)

	alerts := publisher.GetAlerts()
	require.Equal(t, 1, len(alerts))
	assert.Equal(t, "alert_001", alerts[0].ID)
	assert.Equal(t, "high", alerts[0].Severity)
}

func TestInMemoryPublisherMultipleAlerts(t *testing.T) {
	publisher := NewInMemoryPublisher()

	ctx := context.Background()

	for i := 1; i <= 5; i++ {
		alert := &engine.Alert{
			ID:        "alert_" + string(rune(i)),
			RuleID:    "rule_001",
			RuleName:  "Test Rule",
			Severity:  "medium",
			Timestamp: time.Now().UnixMilli(),
			EventID:   "event_" + string(rune(i)),
		}
		err := publisher.Publish(ctx, alert)
		require.NoError(t, err)
	}

	alerts := publisher.GetAlerts()
	assert.Equal(t, 5, len(alerts))
}

func TestInMemoryPublisherClear(t *testing.T) {
	publisher := NewInMemoryPublisher()

	ctx := context.Background()
	alert := &engine.Alert{
		ID:     "alert_001",
		RuleID: "rule_001",
	}
	err := publisher.Publish(ctx, alert)
	require.NoError(t, err)

	alerts := publisher.GetAlerts()
	assert.Equal(t, 1, len(alerts))

	publisher.Clear()
	alerts = publisher.GetAlerts()
	assert.Equal(t, 0, len(alerts))
}

func TestInMemoryPublisherClose(t *testing.T) {
	publisher := NewInMemoryPublisher()
	err := publisher.Close()
	assert.NoError(t, err)
}

func TestInMemoryPublisherGetAlertsIsolation(t *testing.T) {
	publisher := NewInMemoryPublisher()

	ctx := context.Background()
	alert1 := &engine.Alert{
		ID:     "alert_001",
		RuleID: "rule_001",
	}
	err := publisher.Publish(ctx, alert1)
	require.NoError(t, err)

	// Get alerts and modify the returned slice
	alerts1 := publisher.GetAlerts()
	assert.Equal(t, 1, len(alerts1))

	// Add another alert
	alert2 := &engine.Alert{
		ID:     "alert_002",
		RuleID: "rule_002",
	}
	err = publisher.Publish(ctx, alert2)
	require.NoError(t, err)

	// Get alerts again - should have 2 now
	alerts2 := publisher.GetAlerts()
	assert.Equal(t, 2, len(alerts2))

	// First slice should still have 1
	assert.Equal(t, 1, len(alerts1))
}
