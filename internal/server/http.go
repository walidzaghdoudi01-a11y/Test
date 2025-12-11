package server

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/detection-engine/internal/alert"
	"github.com/detection-engine/internal/engine"
	"github.com/google/uuid"
)

// HTTPServer handles HTTP requests for the detection service
type HTTPServer struct {
	detector  *engine.Detector
	publisher alert.Publisher
	mux       *http.ServeMux
}

// NewHTTPServer creates a new HTTP server
func NewHTTPServer(detector *engine.Detector, publisher alert.Publisher) *HTTPServer {
	server := &HTTPServer{
		detector:  detector,
		publisher: publisher,
		mux:       http.NewServeMux(),
	}

	server.registerRoutes()
	return server
}

// registerRoutes registers HTTP routes
func (hs *HTTPServer) registerRoutes() {
	hs.mux.HandleFunc("/health", hs.healthHandler)
	hs.mux.HandleFunc("/ingest", hs.ingestHandler)
	hs.mux.HandleFunc("/rules", hs.rulesHandler)
	hs.mux.HandleFunc("/rules/", hs.ruleDetailHandler)
}

// healthHandler handles health checks
func (hs *HTTPServer) healthHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
}

// ingestHandler handles telemetry ingestion
func (hs *HTTPServer) ingestHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var event engine.TelemetryEvent
	if err := json.NewDecoder(r.Body).Decode(&event); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if err := validateEvent(&event); err != nil {
		http.Error(w, fmt.Sprintf("Validation error: %v", err), http.StatusBadRequest)
		return
	}

	if event.ID == "" {
		event.ID = uuid.New().String()
	}
	if event.Timestamp == 0 {
		event.Timestamp = time.Now().UnixMilli()
	}

	// Run detection
	alerts := hs.detector.Detect(&event)

	// Publish alerts
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	for _, a := range alerts {
		if err := hs.publisher.Publish(ctx, a); err != nil {
			fmt.Printf("Failed to publish alert: %v\n", err)
		}
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	response := map[string]interface{}{
		"event_id":     event.ID,
		"accepted":     true,
		"alerts_count": len(alerts),
		"message":      "Event processed successfully",
	}
	json.NewEncoder(w).Encode(response)
}

// rulesHandler handles rule listing
func (hs *HTTPServer) rulesHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	rules := hs.detector.ListRules()

	w.Header().Set("Content-Type", "application/json")
	response := map[string]interface{}{
		"rules": rules,
		"total": len(rules),
	}
	json.NewEncoder(w).Encode(response)
}

// ruleDetailHandler handles individual rule retrieval
func (hs *HTTPServer) ruleDetailHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	ruleID := r.URL.Path[len("/rules/"):]
	if ruleID == "" {
		http.Error(w, "Rule ID required", http.StatusBadRequest)
		return
	}

	rule, ok := hs.detector.GetRule(ruleID)
	if !ok {
		http.Error(w, "Rule not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(rule)
}

// validateEvent validates a telemetry event
func validateEvent(event *engine.TelemetryEvent) error {
	if event.Source == "" {
		return fmt.Errorf("source is required")
	}
	if event.EventType == "" {
		return fmt.Errorf("event_type is required")
	}
	if len(event.Payload) == 0 {
		return fmt.Errorf("payload is required")
	}
	return nil
}

// ListenAndServe starts the HTTP server
func (hs *HTTPServer) ListenAndServe(addr string) error {
	return http.ListenAndServe(addr, hs.mux)
}
