# Thyroid Ultrasound Ti Rads Agent

> **Domain:** Diagnostic Radiology & Medical Imaging AI
> **Reference Guidelines & Standards:** American College of Radiology (ACR) TI-RADS & Fleischner Society

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## Overview

Thyroid Ultrasound Ti Rads Agent is an enterprise-grade distributed component analytical platform for diagnostic radiology. It performs multiparametric feature evaluation of thyroid nodules following ACR TI-RADS classification guidelines, with multi-worker consensus orchestration, cryptographic audit trails, and zero-PHI outbound protection.

---

## Key Capabilities

- **Multi-Worker Consensus Orchestration**: InvariantQCWorker, SafetyEscalationWorker, and ProtocolConformanceWorker evaluate tasks independently.
- **Deterministic Calculation Engine**: Strict compliance with ACR TI-RADS thresholds and classification rules.
- **Risk & Urgency Classification**: Multi-tier categorization (ROUTINE / ELEVATED_RISK / CRITICAL_STAT_PANIC) with automated recommendations.
- **Zero-PHI Outbound Interceptor**: AST and regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers.
- **Tamper-Evident HMAC-SHA256 Audit Trail**: Chained, cryptographically signed logs for every evaluation with integrity verification.
- **Active Learning Bayesian Calibration**: Dynamic worker reliability weight tracking with Brier calibration monitoring.
- **FastAPI REST API**: OpenAPI 3.1 endpoints with Prometheus operational telemetry.
- **Batch Processing**: CSV-based batch evaluation with audit hash output.

---

## Installation

### Prerequisites
- Python 3.9 or higher
- pip

### Setup
```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/thyroid-ultrasound-ti-rads-agent.git
cd thyroid-ultrasound-ti-rads-agent

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install pydantic fastapi uvicorn pytest

# Or install as a package
pip install -e .
```

---

## Usage

### 1. Guided Interactive CLI - Audit Single Task
```bash
python cli.py audit --task-id TASK-001 --target TARGET-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Supervisory Chat Query
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch FastAPI REST Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

---

## REST API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| GET | `/health` | Health and metadata check |
| GET | `/metrics` | Prometheus operational metrics |
| POST | `/api/audit` | Dispatch task payload across specialized workers |
| POST | `/api/chat` | Air-gapped supervisory conversational assistant |
| GET | `/api/audit/logs` | Retrieve and verify HMAC audit trail |

### Example API Request
```bash
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "TASK-001",
    "target_identifier": "TARGET-01",
    "primary_metric": 28.5,
    "secondary_metric": 14.2,
    "status_descriptor": "DISCORDANT",
    "is_critical_flag": true
  }'
```

---

## Input Data Schema

| Field | Type | Description | Requirement |
|:------|:-----|:------------|:------------|
| `task_id` | string | Unique task / case identifier | Required |
| `target_identifier` | string | Entity or specimen identifier | Required |
| `primary_metric` | float | Primary domain measurement or score | Required |
| `secondary_metric` | float | Secondary kinetic or confidence score | Optional (default: 0.0) |
| `status_descriptor` | string | Status code or phenotype descriptor | Optional (default: "NOMINAL") |
| `is_critical_flag` | boolean | Emergency escalation trigger | Optional (default: false) |

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|:---------|:------------|:--------|
| `AUDIT_SECRET_KEY` | Secret key for HMAC-SHA256 audit signing | Random per-session (set for production) |
| `MODEL_PROVIDER` | LLM provider selection | `mock` |

---

## Testing

### Run Full Test Suite
```bash
pytest -v
```

### Run Specific Test Modules
```bash
pytest tests/test_thyroid_ultrasound_ti_rads_agent.py -v
pytest tests/test_thyroid_tirads_ai.py -v
pytest tests/test_enrichment.py -v
pytest tests/test_cli_and_api.py -v
```

### High-Throughput Simulation Benchmark
```bash
python simulator.py 1000
```

---

## Container Deployment

### Docker
```bash
docker build -t thyroid-ultrasound-ti-rads-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key thyroid-ultrasound-ti-rads-agent
```

### Docker Compose
```bash
# Set production audit key
export AUDIT_SECRET_KEY=your-secure-production-key
docker-compose up -d
```

---

## Security Architecture

- **Zero-PHI Outbound Guard**: Blocks SSNs (`XXX-XX-XXXX`), MRNs (`MRN-XXXXXX`), phone numbers, email addresses, DOB patterns, and known placeholder names (John Doe, Jane Smith).
- **HMAC-SHA256 Audit Trail**: Each log entry is signed with HMAC-SHA256 and chained to the previous entry. Tampering with any entry invalidates the chain signature.
- **Secure Key Generation**: When `AUDIT_SECRET_KEY` is not set, a cryptographically secure random key is generated per session using `secrets.token_bytes(32)`.

---

## Project Structure

```
thyroid-ultrasound-ti-rads-agent/
├── agents/                      # Core distributed component workers
│   ├── __init__.py
│   ├── api.py                   # FastAPI REST endpoints
│   ├── base.py                  # Security, PHI guard, HMAC audit trail
│   ├── learning.py              # Bayesian calibration engine
│   ├── llm_factory.py           # LLM provider factory (mock/Ollama/Claude/OpenAI)
│   ├── metrics.py               # Prometheus metrics collector
│   ├── models.py                # Pydantic v2 data schemas
│   ├── streamer.py              # WebSocket telemetry broadcaster
│   ├── supervisor.py            # Multi-worker orchestrator
│   └── workers.py               # Specialized domain workers
├── thyroid_tirads_ai/           # Alternative implementation package
│   ├── __init__.py
│   ├── agents.py                # Sub-agent implementations
│   ├── cli.py                   # Package CLI entry point
│   ├── engine.py                # Core algorithmic engine
│   ├── models.py                # Data models
│   └── server.py                # FastAPI app factory
├── tests/                       # Automated test suite
│   ├── test_thyroid_ultrasound_ti_rads_agent.py
│   ├── test_thyroid_tirads_ai.py
│   ├── test_enrichment.py
│   └── test_cli_and_api.py
├── web/index.html               # Operations console UI
├── cli.py                       # Main CLI entry point
├── enrichment.py                # Domain enrichment feature engines
├── simulator.py                 # High-throughput stress simulator
├── Dockerfile                   # Container build config
├── docker-compose.yml           # Multi-service orchestration
├── pyproject.toml               # Package metadata and dependencies
├── sample.csv                   # Sample batch input
├── sample_payload.json          # Sample API payload
├── benchmark_dataset.json       # Golden benchmark test suite
├── openapi_spec.json            # OpenAPI 3.1 specification
└── LICENSE                      # MIT License
```

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## Author

**Dr. Abu Suraih Sakhri** - [GitHub](https://github.com/abusuraihsakhri)
