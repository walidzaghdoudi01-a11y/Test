package rules

import (
    "os"
    "path/filepath"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestLoadYAMLRule(t *testing.T) {
    loader := NewRuleLoader(".")

    content := []byte(`
id: test_rule_001
name: Test Rule
description: A test rule
severity: high
source: test
enabled: true
definition:
  event_types:
    - test_event
  conditions:
    - field: event_type
      operator: equals
      value: test_event
  actions:
    - type: alert
      indicators:
        - test_indicator
`)

    rule, err := loader.loadYAML(content)
    require.NoError(t, err)
    assert.Equal(t, "test_rule_001", rule.ID)
    assert.Equal(t, "Test Rule", rule.Name)
    assert.Equal(t, "high", rule.Severity)
    assert.True(t, rule.Enabled)
    assert.Equal(t, "test", rule.Source)
}

func TestLoadJSONRule(t *testing.T) {
    loader := NewRuleLoader(".")

    content := []byte(`{
        "id": "test_rule_002",
        "name": "Test JSON Rule",
        "description": "A JSON rule",
        "severity": "critical",
        "source": "test",
        "enabled": true,
        "definition": {
            "event_types": ["json_event"],
            "conditions": [{"field": "event_type", "operator": "equals", "value": "json_event"}],
            "actions": []
        }
    }`)

    rule, err := loader.loadJSON(content)
    require.NoError(t, err)
    assert.Equal(t, "test_rule_002", rule.ID)
    assert.Equal(t, "Test JSON Rule", rule.Name)
    assert.Equal(t, "critical", rule.Severity)
}

func TestValidateRuleNameRequired(t *testing.T) {
    loader := NewRuleLoader(".")

    content := []byte(`
severity: high
source: test
definition:
  event_types:
    - test_event
  conditions:
    - field: test
      operator: equals
      value: test
`)

    rule, err := loader.loadYAML(content)
    assert.Error(t, err)
    assert.Nil(t, rule)
    assert.Contains(t, err.Error(), "name is required")
}

func TestValidateSeverityRequired(t *testing.T) {
    loader := NewRuleLoader(".")

    content := []byte(`
name: Test Rule
source: test
definition:
  event_types:
    - test_event
  conditions: []
`)

    rule, err := loader.loadYAML(content)
    assert.Error(t, err)
    assert.Nil(t, rule)
    assert.Contains(t, err.Error(), "severity is required")
}

func TestValidateInvalidSeverity(t *testing.T) {
    loader := NewRuleLoader(".")

    content := []byte(`
name: Test Rule
severity: invalid_severity
source: test
definition:
  event_types:
    - test_event
  conditions: []
`)

    rule, err := loader.loadYAML(content)
    assert.Error(t, err)
    assert.Nil(t, rule)
    assert.Contains(t, err.Error(), "invalid severity")
}

func TestValidateEventTypesRequired(t *testing.T) {
    loader := NewRuleLoader(".")

    content := []byte(`
name: Test Rule
severity: high
source: test
definition:
  event_types: []
  conditions: []
`)

    rule, err := loader.loadYAML(content)
    assert.Error(t, err)
    assert.Nil(t, rule)
    assert.Contains(t, err.Error(), "at least one event type")
}

func TestValidateConditionsRequired(t *testing.T) {
    loader := NewRuleLoader(".")

    content := []byte(`
name: Test Rule
severity: high
source: test
definition:
  event_types:
    - test_event
  conditions: []
`)

    rule, err := loader.loadYAML(content)
    assert.Error(t, err)
    assert.Nil(t, rule)
    assert.Contains(t, err.Error(), "at least one condition")
}

func TestValidSeverities(t *testing.T) {
    loader := NewRuleLoader(".")

    severities := []string{"critical", "high", "medium", "low", "info"}

    for _, severity := range severities {
        content := []byte(`
name: Test Rule
severity: ` + severity + `
source: test
definition:
  event_types:
    - test_event
  conditions:
    - field: test
      operator: equals
      value: test
`)

        rule, err := loader.loadYAML(content)
        require.NoError(t, err, "severity %s should be valid", severity)
        assert.Equal(t, severity, rule.Severity)
    }
}

func TestLoadFromFileYAML(t *testing.T) {
    tmpDir := t.TempDir()
    ruleFile := filepath.Join(tmpDir, "test_rule.yaml")

    content := []byte(`
id: file_test_001
name: File Test Rule
severity: medium
source: test
enabled: true
definition:
  event_types:
    - file_event
  conditions:
    - field: event_type
      operator: equals
      value: file_event
  actions: []
`)

    err := os.WriteFile(ruleFile, content, 0644)
    require.NoError(t, err)

    loader := NewRuleLoader(tmpDir)
    rule, err := loader.LoadFromFile(ruleFile)
    require.NoError(t, err)
    assert.Equal(t, "file_test_001", rule.ID)
    assert.Equal(t, "File Test Rule", rule.Name)
}

func TestLoadFromFileJSON(t *testing.T) {
    tmpDir := t.TempDir()
    ruleFile := filepath.Join(tmpDir, "test_rule.json")

    content := []byte(`{
        "id": "json_file_test",
        "name": "JSON File Test Rule",
        "severity": "low",
        "source": "test",
        "enabled": true,
        "definition": {
            "event_types": ["json_event"],
            "conditions": [{"field": "test", "operator": "equals", "value": "test"}],
            "actions": []
        }
    }`)

    err := os.WriteFile(ruleFile, content, 0644)
    require.NoError(t, err)

    loader := NewRuleLoader("")
    rule, err := loader.LoadFromFile(ruleFile)
    require.NoError(t, err)
    assert.Equal(t, "json_file_test", rule.ID)
    assert.Equal(t, "JSON File Test Rule", rule.Name)
}

func TestLoadFromDir(t *testing.T) {
    tmpDir := t.TempDir()

    rule1Content := []byte(`
id: dir_test_001
name: Dir Test Rule 1
severity: high
source: test
enabled: true
definition:
  event_types:
    - test_event
  conditions:
    - field: test
      operator: equals
      value: test
  actions: []
`)

    rule2Content := []byte(`{
        "id": "dir_test_002",
        "name": "Dir Test Rule 2",
        "severity": "medium",
        "source": "test",
        "enabled": true,
        "definition": {
            "event_types": ["test_event"],
            "conditions": [{"field": "test", "operator": "equals", "value": "test"}],
            "actions": []
        }
    }`)

    err := os.WriteFile(filepath.Join(tmpDir, "rule1.yaml"), rule1Content, 0644)
    require.NoError(t, err)

    err = os.WriteFile(filepath.Join(tmpDir, "rule2.json"), rule2Content, 0644)
    require.NoError(t, err)

    loader := NewRuleLoader(tmpDir)
    rules, err := loader.LoadFromDir(tmpDir)
    require.NoError(t, err)
    assert.Equal(t, 2, len(rules))
}

func TestLoadFromDirIgnoresNonRuleFiles(t *testing.T) {
    tmpDir := t.TempDir()

    ruleContent := []byte(`
id: ignore_test_001
name: Ignore Test Rule
severity: high
source: test
enabled: true
definition:
  event_types:
    - test_event
  conditions:
    - field: test
      operator: equals
      value: test
  actions: []
`)

    err := os.WriteFile(filepath.Join(tmpDir, "rule.yaml"), ruleContent, 0644)
    require.NoError(t, err)

    err = os.WriteFile(filepath.Join(tmpDir, "readme.txt"), []byte("This should be ignored"), 0644)
    require.NoError(t, err)

    err = os.WriteFile(filepath.Join(tmpDir, "config.ini"), []byte("This should also be ignored"), 0644)
    require.NoError(t, err)

    loader := NewRuleLoader(tmpDir)
    rules, err := loader.LoadFromDir(tmpDir)
    require.NoError(t, err)
    assert.Equal(t, 1, len(rules))
}

func TestLoadFromFileInvalidFormat(t *testing.T) {
    tmpDir := t.TempDir()
    ruleFile := filepath.Join(tmpDir, "test_rule.txt")

    err := os.WriteFile(ruleFile, []byte("invalid"), 0644)
    require.NoError(t, err)

    loader := NewRuleLoader(tmpDir)
    rule, err := loader.LoadFromFile(ruleFile)
    assert.Error(t, err)
    assert.Nil(t, rule)
    assert.Contains(t, err.Error(), "unsupported file format")
}
