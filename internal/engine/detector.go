package engine

import (
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
)

// Detector is the main detection engine
type Detector struct {
	rules    map[string]*Rule
	matchers map[string]Matcher
	mu       sync.RWMutex
}

// NewDetector creates a new detector instance
func NewDetector() *Detector {
	return &Detector{
		rules: make(map[string]*Rule),
		matchers: map[string]Matcher{
			"builtin": &BuiltinMatchers{},
		},
	}
}

// AddRule adds a rule to the detector
func (d *Detector) AddRule(rule *Rule) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	if rule.ID == "" {
		rule.ID = uuid.New().String()
	}
	if rule.CreatedAt == 0 {
		rule.CreatedAt = time.Now().UnixMilli()
	}
	rule.UpdatedAt = time.Now().UnixMilli()

	d.rules[rule.ID] = rule
	return nil
}

// GetRule retrieves a rule by ID
func (d *Detector) GetRule(id string) (*Rule, bool) {
	d.mu.RLock()
	defer d.mu.RUnlock()

	rule, ok := d.rules[id]
	return rule, ok
}

// ListRules returns all rules
func (d *Detector) ListRules() []*Rule {
	d.mu.RLock()
	defer d.mu.RUnlock()

	rules := make([]*Rule, 0, len(d.rules))
	for _, rule := range d.rules {
		rules = append(rules, rule)
	}
	return rules
}

// Detect runs detection rules against a telemetry event
func (d *Detector) Detect(event *TelemetryEvent) []*Alert {
	d.mu.RLock()
	rules := make([]*Rule, 0, len(d.rules))
	for _, rule := range d.rules {
		if rule.Enabled {
			rules = append(rules, rule)
		}
	}
	d.mu.RUnlock()

	var alerts []*Alert

	for _, rule := range rules {
		if d.matchesRule(event, rule) {
			alert := d.createAlert(event, rule)
			alerts = append(alerts, alert)
		}
	}

	return alerts
}

// matchesRule checks if an event matches a rule
func (d *Detector) matchesRule(event *TelemetryEvent, rule *Rule) bool {
	// Check event type
	if len(rule.Definition.EventTypes) > 0 {
		matched := false
		for _, eventType := range rule.Definition.EventTypes {
			if eventType == event.EventType {
				matched = true
				break
			}
		}
		if !matched {
			return false
		}
	}

	// Check conditions (all must pass)
	matcher := d.matchers["builtin"]
	for _, condition := range rule.Definition.Conditions {
		if !matcher.Match(event, condition) {
			return false
		}
	}

	return true
}

// createAlert creates an alert from a matched rule
func (d *Detector) createAlert(event *TelemetryEvent, rule *Rule) *Alert {
	alert := &Alert{
		ID:          uuid.New().String(),
		RuleID:      rule.ID,
		RuleName:    rule.Name,
		Severity:    rule.Severity,
		Timestamp:   time.Now().UnixMilli(),
		EventID:     event.ID,
		Indicators:  []string{},
		Enrichment:  make(map[string]string),
		Description: rule.Description,
		Metadata: map[string]string{
			"rule_source":  rule.Source,
			"event_source": event.Source,
		},
	}

	// Process actions
	for _, action := range rule.Definition.Actions {
		if action.Type == "alert" {
			alert.Indicators = append(alert.Indicators, action.Indicators...)
			for k, v := range action.Enrichment {
				alert.Enrichment[k] = v
			}
		}
	}

	return alert
}

// RegisterMatcher registers a custom matcher
func (d *Detector) RegisterMatcher(name string, matcher Matcher) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	if name == "" {
		return fmt.Errorf("matcher name cannot be empty")
	}
	if matcher == nil {
		return fmt.Errorf("matcher cannot be nil")
	}

	d.matchers[name] = matcher
	return nil
}
