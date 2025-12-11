package engine

import (
    "encoding/json"
    "reflect"
    "strings"
)

// BuiltinMatchers provides standard matching operations
type BuiltinMatchers struct{}

// Match applies built-in operators
func (m *BuiltinMatchers) Match(event *TelemetryEvent, condition Condition) bool {
    value := extractFieldValue(event, condition.Field)
    if value == nil {
        return false
    }

    switch condition.Operator {
    case "equals":
        return equals(value, condition.Value)
    case "not_equals":
        return !equals(value, condition.Value)
    case "contains":
        return contains(value, condition.Value)
    case "not_contains":
        return !contains(value, condition.Value)
    case "starts_with":
        return startsWithValue(value, condition.Value)
    case "ends_with":
        return endsWithValue(value, condition.Value)
    case "greater_than":
        return greaterThan(value, condition.Value)
    case "less_than":
        return lessThan(value, condition.Value)
    case "in":
        return in(value, condition.Value)
    case "not_in":
        return !in(value, condition.Value)
    case "regex":
        return regexMatch(value, condition.Value)
    case "exists":
        return value != nil
    case "not_exists":
        return value == nil
    default:
        return false
    }
}

// extractFieldValue extracts a value from the event by field path
func extractFieldValue(event *TelemetryEvent, field string) interface{} {
    parts := strings.Split(field, ".")

    switch parts[0] {
    case "id":
        if len(parts) == 1 {
            return event.ID
        }
    case "source":
        if len(parts) == 1 {
            return event.Source
        }
    case "event_type":
        if len(parts) == 1 {
            return event.EventType
        }
    case "tags":
        if len(parts) > 1 {
            if val, ok := event.Tags[parts[1]]; ok {
                return val
            }
            return nil
        }
    case "payload":
        if len(parts) > 1 {
            return extractFromPayload(event.Payload, parts[1:])
        }
    }
    return nil
}

// extractFromPayload extracts nested values from JSON payload
func extractFromPayload(payload json.RawMessage, path []string) interface{} {
    var data interface{}
    if err := json.Unmarshal(payload, &data); err != nil {
        return nil
    }

    for _, key := range path {
        switch v := data.(type) {
        case map[string]interface{}:
            data = v[key]
        default:
            return nil
        }
    }
    return data
}

// equals checks equality
func equals(value, expected interface{}) bool {
    return reflect.DeepEqual(toString(value), toString(expected))
}

// contains checks if value contains substring
func contains(value, substring interface{}) bool {
    return strings.Contains(toString(value), toString(substring))
}

// startsWithValue checks if value starts with prefix
func startsWithValue(value, prefix interface{}) bool {
    return strings.HasPrefix(toString(value), toString(prefix))
}

// endsWithValue checks if value ends with suffix
func endsWithValue(value, suffix interface{}) bool {
    return strings.HasSuffix(toString(value), toString(suffix))
}

// greaterThan checks if value is greater than threshold
func greaterThan(value, threshold interface{}) bool {
    vNum := toNumber(value)
    tNum := toNumber(threshold)
    return vNum > tNum
}

// lessThan checks if value is less than threshold
func lessThan(value, threshold interface{}) bool {
    vNum := toNumber(value)
    tNum := toNumber(threshold)
    return vNum < tNum
}

// in checks if value is in list
func in(value, list interface{}) bool {
    valStr := toString(value)
    switch v := list.(type) {
    case []interface{}:
        for _, item := range v {
            if toString(item) == valStr {
                return true
            }
        }
    }
    return false
}

// regexMatch checks regex match (simple implementation)
func regexMatch(value, pattern interface{}) bool {
    // For now, simple substring matching as fallback
    return strings.Contains(toString(value), toString(pattern))
}

// toString converts value to string
func toString(value interface{}) string {
    switch v := value.(type) {
    case string:
        return v
    case float64:
        return reflect.ValueOf(v).String()
    case int:
        return reflect.ValueOf(v).String()
    case bool:
        return reflect.ValueOf(v).String()
    default:
        return ""
    }
}

// toNumber converts value to float64
func toNumber(value interface{}) float64 {
    switch v := value.(type) {
    case float64:
        return v
    case int:
        return float64(v)
    case string:
        // Try to parse as number (not implemented for now)
        return 0
    default:
        return 0
    }
}
