.PHONY: help build test lint fmt clean docker-build docker-run install-tools

help:
	@echo "Detection Engine Makefile"
	@echo "========================"
	@echo ""
	@echo "Available targets:"
	@echo "  build          - Build the detection engine binary"
	@echo "  test           - Run all tests"
	@echo "  test-verbose   - Run tests with verbose output"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  lint           - Run golangci-lint (if installed)"
	@echo "  fmt            - Format code with gofmt"
	@echo "  fmt-check      - Check code formatting without modification"
	@echo "  clean          - Remove build artifacts"
	@echo "  docker-build   - Build Docker image"
	@echo "  docker-run     - Run Docker container"
	@echo "  install-tools  - Install development tools"
	@echo "  run            - Run the service locally"
	@echo "  run-debug      - Run with debug output"

build:
	@echo "Building detection-engine..."
	go build -o detection-engine ./cmd/detection-engine
	@echo "Build complete: ./detection-engine"

install-tools:
	@echo "Installing development tools..."
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	go install golang.org/x/tools/cmd/goimports@latest
	@echo "Tools installed"

test:
	@echo "Running tests..."
	go test ./...

test-verbose:
	@echo "Running tests (verbose)..."
	go test -v ./...

test-coverage:
	@echo "Running tests with coverage..."
	go test -cover ./...
	@echo ""
	@echo "Generating coverage report..."
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

lint:
	@if command -v golangci-lint > /dev/null; then \
		echo "Running golangci-lint..."; \
		golangci-lint run ./...; \
	else \
		echo "golangci-lint not installed. Run 'make install-tools' to install it."; \
	fi

fmt:
	@echo "Formatting code..."
	gofmt -s -w .
	@if command -v goimports > /dev/null; then \
		echo "Organizing imports..."; \
		goimports -w .; \
	fi
	@echo "Formatting complete"

fmt-check:
	@echo "Checking code formatting..."
	@if [ -z "$$(gofmt -l .)" ]; then \
		echo "Code is properly formatted"; \
	else \
		echo "Code formatting issues found:"; \
		gofmt -l .; \
		exit 1; \
	fi

clean:
	@echo "Cleaning build artifacts..."
	rm -f detection-engine
	rm -f coverage.out coverage.html
	go clean -cache -testcache
	@echo "Clean complete"

docker-build:
	@echo "Building Docker image..."
	docker build -t detection-engine:latest .
	docker tag detection-engine:latest detection-engine:latest
	@echo "Docker image built: detection-engine:latest"

docker-run:
	@echo "Running Docker container..."
	docker run -p 8080:8080 \
		-v $$(pwd)/rules:/app/rules:ro \
		detection-engine:latest

run: build
	@echo "Starting detection engine..."
	./detection-engine --rules-dir ./rules --http :8080

run-debug: build
	@echo "Starting detection engine with debug output..."
	./detection-engine --rules-dir ./rules --http :8080 2>&1 | tee detection.log

run-with-kafka: build
	@echo "Starting detection engine with Kafka..."
	./detection-engine \
		--rules-dir ./rules \
		--http :8080 \
		--kafka-brokers localhost:9092 \
		--kafka-topic detection-alerts

test-single:
	@if [ -z "$(TEST)" ]; then \
		echo "Usage: make test-single TEST=path/to/test"; \
		exit 1; \
	fi
	go test -v ./$(TEST) -run .

version:
	@echo "Go version:"
	@go version
	@echo ""
	@echo "Module info:"
	@head -3 go.mod

vendor:
	@echo "Downloading dependencies..."
	go mod download
	go mod tidy
	@echo "Dependencies ready"

all: clean fmt test lint build
	@echo "All tasks complete"

.DEFAULT_GOAL := help
