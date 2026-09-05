"""
Automated Pytest for CLI batch command and FastAPI API endpoints.
"""
import sys
import os
import csv
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import AuditLogger, PHIGuard, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel
from cli import main
from agents.api import app


# --- CLI Batch Tests ---

def test_cli_batch_processing():
    """Test that CLI batch command processes CSV and produces output."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'task_id', 'target_identifier', 'primary_metric',
            'secondary_metric', 'is_critical_flag', 'status_descriptor'
        ])
        writer.writeheader()
        writer.writerow({
            'task_id': 'BATCH-01',
            'target_identifier': 'TARGET-B1',
            'primary_metric': '28.4',
            'secondary_metric': '14.2',
            'is_critical_flag': 'True',
            'status_descriptor': 'DISCORDANT'
        })
        writer.writerow({
            'task_id': 'BATCH-02',
            'target_identifier': 'TARGET-B2',
            'primary_metric': '12.0',
            'secondary_metric': '4.1',
            'is_critical_flag': 'False',
            'status_descriptor': 'NOMINAL'
        })
        input_path = f.name

    output_path = tempfile.mktemp(suffix='.csv')

    try:
        exit_code = main(['batch', '-i', input_path, '-o', output_path])
        assert exit_code == 0
        assert os.path.exists(output_path)

        with open(output_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['overall_urgency'] in ['ELEVATED_RISK', 'CRITICAL_STAT_PANIC', 'ROUTINE']
            assert 'audit_hash' in rows[0]
    finally:
        os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_cli_batch_empty_csv():
    """Test that CLI batch handles empty CSV gracefully."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'task_id', 'target_identifier', 'primary_metric',
            'secondary_metric', 'is_critical_flag', 'status_descriptor'
        ])
        writer.writeheader()
        input_path = f.name

    output_path = tempfile.mktemp(suffix='.csv')

    try:
        exit_code = main(['batch', '-i', input_path, '-o', output_path])
        assert exit_code == 0
        assert os.path.exists(output_path)

        with open(output_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0
    finally:
        os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)


# --- API Endpoint Tests ---

def test_api_health():
    """Test health endpoint returns expected structure."""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["service"] == "thyroid-ultrasound-ti-rads-agent"


def test_api_metrics():
    """Test metrics endpoint returns operational data."""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "dossiers_processed_total" in data
    assert "audit_blocks_total" in data
    assert data["system_status"] == "NOMINAL_OPTIMAL"


def test_api_audit_endpoint():
    """Test audit endpoint processes payload and returns dossier."""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    payload = {
        "task_id": "API-TEST-01",
        "target_identifier": "TARGET-API-01",
        "primary_metric": 12.0,
        "secondary_metric": 4.0,
        "status_descriptor": "NOMINAL",
        "is_critical_flag": False
    }
    response = client.post("/api/audit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "API-TEST-01"
    assert data["overall_urgency"] == "ROUTINE"
    assert "audit_hash" in data
    assert len(data["audit_hash"]) > 0


def test_api_audit_critical_escalation():
    """Test audit endpoint escalates critical payloads correctly."""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    payload = {
        "task_id": "API-CRIT-01",
        "target_identifier": "TARGET-CRIT-01",
        "primary_metric": 35.0,
        "secondary_metric": 15.0,
        "status_descriptor": "DISCORDANT_ANOMALY",
        "is_critical_flag": True
    }
    response = client.post("/api/audit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_urgency"] == "CRITICAL_STAT_PANIC"
    assert data["critical_alerts_count"] > 0


def test_api_chat_endpoint():
    """Test chat endpoint processes queries without PHI."""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.post("/api/chat", json={"query": "What is the system status?"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert len(data["response"]) > 0


def test_api_chat_blocks_phi():
    """Test chat endpoint rejects queries containing PHI."""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.post("/api/chat", json={"query": "Patient MRN-12345 has a nodule"})
    assert response.status_code == 400


def test_api_audit_logs_endpoint():
    """Test audit logs endpoint returns trail with integrity check."""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/api/audit/logs")
    assert response.status_code == 200
    data = response.json()
    assert "audit_trail" in data
    assert "verified" in data


# --- Additional Security Tests ---

def test_phi_guard_redaction():
    """Test that PHI guard properly redacts sensitive data."""
    text = "Patient John Doe MRN-994827 phone 555-123-4567"
    redacted = PHIGuard.redact_phi(text)
    assert "John Doe" not in redacted
    assert "MRN-994827" not in redacted
    assert "555-123-4567" not in redacted
    assert "[REDACTED_IDENTIFIER]" in redacted


def test_phi_guard_email_detection():
    """Test that PHI guard detects email addresses."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Contact patient at john.doe@hospital.org")


def test_audit_trail_integrity():
    """Test that audit trail maintains cryptographic integrity."""
    from agents.base import AuditTrail
    trail = AuditTrail(secret_key="test-key-for-integrity")
    trail.log("test_actor", "test_tier", "TEST_EVENT", {"key": "value"})
    trail.log("test_actor", "test_tier", "TEST_EVENT_2", {"key2": "value2"})
    assert trail.verify_integrity() is True
    assert len(trail.get_trail()) == 2


def test_audit_trail_tamper_detection():
    """Test that audit trail detects tampering."""
    from agents.base import AuditTrail
    trail = AuditTrail(secret_key="test-key-for-tamper")
    trail.log("test_actor", "test_tier", "TEST_EVENT", {"key": "value"})
    # Tamper with the entry
    trail.logs[0]["event_type"] = "TAMPERED"
    assert trail.verify_integrity() is False
