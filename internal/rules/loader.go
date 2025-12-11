package rules

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/detection-engine/internal/engine"
	"gopkg.in/yaml.v3"
)

// RuleLoader handles loading rules from files
type RuleLoader struct {
	rulesDir string
}

// NewRuleLoader creates a new rule loader
func NewRuleLoader(rulesDir string) *RuleLoader {
	return &RuleLoader{
		rulesDir: rulesDir,
	}
}

// LoadFromFile loads a single rule from a file
func (rl *RuleLoader) LoadFromFile(filePath string) (*engine.Rule, error) {
	content, err := os.ReadFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	ext := filepath.Ext(filePath)
	if ext == ".yaml" || ext == ".yml" {
		return rl.loadYAML(content)
	} else if ext == ".json" {
		return rl.loadJSON(content)
	}

	return nil, fmt.Errorf("unsupported file format: %s", ext)
}

// LoadFromDir loads all rules from a directory
func (rl *RuleLoader) LoadFromDir(dirPath string) ([]*engine.Rule, error) {
	entries, err := os.ReadDir(dirPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read directory: %w", err)
	}

	var rules []*engine.Rule

	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}

		ext := filepath.Ext(entry.Name())
		if ext != ".yaml" && ext != ".yml" && ext != ".json" {
			continue
		}

		filePath := filepath.Join(dirPath, entry.Name())
		rule, err := rl.LoadFromFile(filePath)
		if err != nil {
			return nil, fmt.Errorf("failed to load rule from %s: %w", entry.Name(), err)
		}

		rules = append(rules, rule)
	}

	return rules, nil
}

// loadYAML unmarshals a YAML rule
func (rl *RuleLoader) loadYAML(content []byte) (*engine.Rule, error) {
	rule := &engine.Rule{}
	if err := yaml.Unmarshal(content, rule); err != nil {
		return nil, fmt.Errorf("failed to unmarshal YAML: %w", err)
	}

	if err := validateRule(rule); err != nil {
		return nil, err
	}

	return rule, nil
}

// loadJSON unmarshals a JSON rule
func (rl *RuleLoader) loadJSON(content []byte) (*engine.Rule, error) {
	rule := &engine.Rule{}
	if err := json.Unmarshal(content, rule); err != nil {
		return nil, fmt.Errorf("failed to unmarshal JSON: %w", err)
	}

	if err := validateRule(rule); err != nil {
		return nil, err
	}

	return rule, nil
}

// validateRule validates a rule's structure
func validateRule(rule *engine.Rule) error {
	if rule.Name == "" {
		return fmt.Errorf("rule name is required")
	}
	if rule.Severity == "" {
		return fmt.Errorf("rule severity is required")
	}

	validSeverities := map[string]bool{
		"critical": true,
		"high":     true,
		"medium":   true,
		"low":      true,
		"info":     true,
	}

	if !validSeverities[rule.Severity] {
		return fmt.Errorf("invalid severity: %s", rule.Severity)
	}

	if len(rule.Definition.EventTypes) == 0 {
		return fmt.Errorf("at least one event type must be specified")
	}

	if len(rule.Definition.Conditions) == 0 {
		return fmt.Errorf("at least one condition must be specified")
	}

	if rule.CreatedAt == 0 {
		rule.CreatedAt = time.Now().UnixMilli()
	}
	if rule.UpdatedAt == 0 {
		rule.UpdatedAt = time.Now().UnixMilli()
	}

	return nil
}
