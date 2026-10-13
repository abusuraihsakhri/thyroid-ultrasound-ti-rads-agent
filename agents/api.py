"""
FastAPI REST API Server for Thyroid Ultrasound Ti Rads Agent.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from thyroid_tirads_ai.tirads import score_tirads
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Thyroid Ultrasound Ti Rads Agent API",
    description="Enterprise Distributed Component Platform (Radiology & Neuroimaging Systems)",
    version="3.0.0-ENTERPRISE",
)


class TIRADSRequest(BaseModel):
    composition: str
    size_cm: float = Field(gt=0, allow_inf_nan=False)
    echogenicity: str | None = None
    shape: str | None = None
    margin: str | None = None
    echogenic_foci: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "thyroid-ultrasound-ti-rads-agent", "domain": "Radiology & Neuroimaging Systems", "standard": "ACR RADS / Fleischner Society / ASPECTS Guidelines", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        raise HTTPException(status_code=422, detail="Sensitive identifiers detected in audit request")
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException:
        raise HTTPException(status_code=400, detail="Sensitive identifiers detected in chat request")


@app.post("/api/ti-rads")
def api_tirads(req: TIRADSRequest):
    """Score manually described adult thyroid nodules with ACR TI-RADS."""
    try:
        return score_tirads(**req.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
