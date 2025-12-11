package alert

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"

	"github.com/detection-engine/internal/engine"
	"github.com/segmentio/kafka-go"
)

// Publisher defines the interface for publishing alerts
type Publisher interface {
	Publish(ctx context.Context, alert *engine.Alert) error
	Close() error
}

// KafkaPublisher publishes alerts to Kafka
type KafkaPublisher struct {
	writer *kafka.Writer
	topic  string
	mu     sync.Mutex
}

// NewKafkaPublisher creates a new Kafka publisher
func NewKafkaPublisher(brokers []string, topic string) (*KafkaPublisher, error) {
	writer := &kafka.Writer{
		Addr:     kafka.TCP(brokers...),
		Topic:    topic,
		Balancer: &kafka.LeastBytes{},
	}

	return &KafkaPublisher{
		writer: writer,
		topic:  topic,
	}, nil
}

// Publish publishes an alert to Kafka
func (kp *KafkaPublisher) Publish(ctx context.Context, alert *engine.Alert) error {
	kp.mu.Lock()
	defer kp.mu.Unlock()

	data, err := json.Marshal(alert)
	if err != nil {
		return fmt.Errorf("failed to marshal alert: %w", err)
	}

	message := kafka.Message{
		Key:   []byte(alert.RuleID),
		Value: data,
	}

	return kp.writer.WriteMessages(ctx, message)
}

// Close closes the Kafka writer
func (kp *KafkaPublisher) Close() error {
	kp.mu.Lock()
	defer kp.mu.Unlock()

	return kp.writer.Close()
}

// InMemoryPublisher is an in-memory alert publisher for testing
type InMemoryPublisher struct {
	alerts []*engine.Alert
	mu     sync.RWMutex
}

// NewInMemoryPublisher creates a new in-memory publisher
func NewInMemoryPublisher() *InMemoryPublisher {
	return &InMemoryPublisher{
		alerts: make([]*engine.Alert, 0),
	}
}

// Publish adds an alert to the in-memory store
func (imp *InMemoryPublisher) Publish(ctx context.Context, alert *engine.Alert) error {
	imp.mu.Lock()
	defer imp.mu.Unlock()

	imp.alerts = append(imp.alerts, alert)
	return nil
}

// GetAlerts returns all published alerts
func (imp *InMemoryPublisher) GetAlerts() []*engine.Alert {
	imp.mu.RLock()
	defer imp.mu.RUnlock()

	result := make([]*engine.Alert, len(imp.alerts))
	copy(result, imp.alerts)
	return result
}

// Clear clears all alerts
func (imp *InMemoryPublisher) Clear() {
	imp.mu.Lock()
	defer imp.mu.Unlock()

	imp.alerts = make([]*engine.Alert, 0)
}

// Close is a no-op for in-memory publisher
func (imp *InMemoryPublisher) Close() error {
	return nil
}
