package engine

import "encoding/json"

// TelemetryEvent represents a normalized telemetry event
type TelemetryEvent struct {
	ID        string                 `json:"id"`
	Source    string                 `json:"source"`
	EventType string                 `json:"event_type"`
	Timestamp int64                  `json:"timestamp"`
	Payload   json.RawMessage        `json:"payload"`
	Tags      map[string]string      `json:"tags"`
}

// Rule represents a detection rule
type Rule struct {
	ID          string                 `json:"id" yaml:"id"`
	Name        string                 `json:"name" yaml:"name"`
	Description string                 `json:"description" yaml:"description"`
	Severity    string                 `json:"severity" yaml:"severity"`
	Source      string                 `json:"source" yaml:"source"`
	Enabled     bool                   `json:"enabled" yaml:"enabled"`
	CreatedAt   int64                  `json:"created_at" yaml:"created_at"`
	UpdatedAt   int64                  `json:"updated_at" yaml:"updated_at"`
	Definition  RuleDefinition         `json:"definition" yaml:"definition"`
}

// RuleDefinition contains the logic for rule matching
type RuleDefinition struct {
	EventTypes []string               `json:"event_types" yaml:"event_types"`
	Conditions []Condition            `json:"conditions" yaml:"conditions"`
	Actions    []Action               `json:"actions" yaml:"actions"`
}

// Condition represents a matching condition
type Condition struct {
	Field    string      `json:"field" yaml:"field"`
	Operator string      `json:"operator" yaml:"operator"`
	Value    interface{} `json:"value" yaml:"value"`
}

// Action represents an action to take when rule matches
type Action struct {
	Type       string            `json:"type" yaml:"type"`
	Indicators []string          `json:"indicators" yaml:"indicators"`
	Enrichment map[string]string `json:"enrichment" yaml:"enrichment"`
}

// Alert represents a detection alert
type Alert struct {
	ID         string            `json:"id"`
	RuleID     string            `json:"rule_id"`
	RuleName   string            `json:"rule_name"`
	Severity   string            `json:"severity"`
	Timestamp  int64             `json:"timestamp"`
	EventID    string            `json:"event_id"`
	Indicators []string          `json:"indicators"`
	Enrichment map[string]string `json:"enrichment"`
	Description string           `json:"description"`
	Metadata   map[string]string `json:"metadata"`
}

// Matcher provides interface for custom matchers
type Matcher interface {
	Match(event *TelemetryEvent, condition Condition) bool
}
