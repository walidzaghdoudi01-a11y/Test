#!/usr/bin/env python3
"""
Validation script to verify the audit logging system structure.
"""
import os
import sys

def check_file(path, description):
    """Check if a file exists."""
    exists = os.path.isfile(path)
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {path}")
    return exists

def check_dir(path, description):
    """Check if a directory exists."""
    exists = os.path.isdir(path)
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {path}")
    return exists

def main():
    """Validate project structure."""
    print("=== Audit Logging System Structure Validation ===\n")
    
    all_checks = []
    
    # Root files
    print("Root Configuration Files:")
    all_checks.append(check_file("README.md", "README"))
    all_checks.append(check_file(".gitignore", "Git ignore"))
    all_checks.append(check_file("requirements.txt", "Requirements"))
    all_checks.append(check_file("docker-compose.yml", "Docker Compose"))
    all_checks.append(check_file("Makefile", "Makefile"))
    all_checks.append(check_file("pytest.ini", "Pytest config"))
    all_checks.append(check_file(".env.example", "Environment example"))
    all_checks.append(check_file("setup.sh", "Setup script"))
    all_checks.append(check_file("CONTRIBUTING.md", "Contributing guide"))
    print()
    
    # Audit Service
    print("Audit Service:")
    all_checks.append(check_dir("audit-service", "Service directory"))
    all_checks.append(check_file("audit-service/app/main.py", "Main application"))
    all_checks.append(check_file("audit-service/app/core/config.py", "Configuration"))
    all_checks.append(check_file("audit-service/app/core/security.py", "Security functions"))
    all_checks.append(check_file("audit-service/app/db/database.py", "Database setup"))
    all_checks.append(check_file("audit-service/app/models/schemas.py", "Data schemas"))
    all_checks.append(check_file("audit-service/app/services/audit_service.py", "Audit service"))
    all_checks.append(check_file("audit-service/app/services/retention_service.py", "Retention service"))
    all_checks.append(check_file("audit-service/app/api/routes/events.py", "Events routes"))
    all_checks.append(check_file("audit-service/app/api/routes/query.py", "Query routes"))
    all_checks.append(check_file("audit-service/app/api/routes/health.py", "Health routes"))
    print()
    
    # Audit Client
    print("Audit Client Library:")
    all_checks.append(check_dir("audit-client", "Client directory"))
    all_checks.append(check_file("audit-client/setup.py", "Client setup"))
    all_checks.append(check_file("audit-client/audit_client/__init__.py", "Client init"))
    all_checks.append(check_file("audit-client/audit_client/client.py", "Client implementation"))
    all_checks.append(check_file("audit-client/audit_client/models.py", "Client models"))
    print()
    
    # Database
    print("Database:")
    all_checks.append(check_dir("database", "Database directory"))
    all_checks.append(check_file("database/alembic.ini", "Alembic config"))
    all_checks.append(check_file("database/alembic/env.py", "Alembic environment"))
    all_checks.append(check_file("database/alembic/script.py.mako", "Migration template"))
    all_checks.append(check_file("database/alembic/versions/001_initial_schema.py", "Initial migration"))
    print()
    
    # Tests
    print("Tests:")
    all_checks.append(check_dir("tests", "Tests directory"))
    all_checks.append(check_file("tests/conftest.py", "Test fixtures"))
    all_checks.append(check_file("tests/test_immutability.py", "Immutability tests"))
    all_checks.append(check_file("tests/test_retention.py", "Retention tests"))
    all_checks.append(check_file("tests/test_api.py", "API tests"))
    all_checks.append(check_file("tests/test_client.py", "Client tests"))
    all_checks.append(check_file("tests/test_integration.py", "Integration tests"))
    print()
    
    # Documentation
    print("Documentation:")
    all_checks.append(check_dir("docs", "Docs directory"))
    all_checks.append(check_file("docs/schema.md", "Schema documentation"))
    all_checks.append(check_file("docs/retention.md", "Retention documentation"))
    all_checks.append(check_file("docs/compliance.md", "Compliance documentation"))
    print()
    
    # Dashboards
    print("Dashboards:")
    all_checks.append(check_dir("dashboards", "Dashboards directory"))
    all_checks.append(check_file("dashboards/query_samples.md", "Query samples"))
    print()
    
    # Examples
    print("Examples:")
    all_checks.append(check_dir("examples", "Examples directory"))
    all_checks.append(check_file("examples/basic_usage.py", "Basic usage example"))
    all_checks.append(check_file("examples/archival_example.py", "Archival example"))
    print()
    
    # Docker
    print("Docker:")
    all_checks.append(check_dir("docker", "Docker directory"))
    all_checks.append(check_file("docker/Dockerfile", "Dockerfile"))
    print()
    
    # Summary
    total = len(all_checks)
    passed = sum(all_checks)
    failed = total - passed
    
    print("\n" + "=" * 50)
    print(f"Total checks: {total}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print("=" * 50)
    
    if failed == 0:
        print("\n✓ All structure checks passed!")
        return 0
    else:
        print(f"\n✗ {failed} checks failed. Please review missing files.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
