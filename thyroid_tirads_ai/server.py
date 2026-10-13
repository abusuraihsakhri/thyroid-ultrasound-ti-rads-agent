"""
FastAPI REST API Server for ThyroidUltrasound Sentinel: ACR TI-RADS Multiparametric Feature Agent.
"""
from typing import Dict, Any
from .models import FrontierPayload
from .agents import ThyroidUSCoordinator
from .tirads import score_tirads

coordinator = ThyroidUSCoordinator()


def create_app():
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, Field

        app = FastAPI(
            title="ThyroidUltrasound Sentinel: ACR TI-RADS Multiparametric Feature Agent",
            description="Evaluates thyroid nodule composition, echogenicity, shape (taller-than-wide), margins, and echogenic foci for FNA guidance.",
            version="2.0.0-FRONTIER",
        )

        class TaskRequest(BaseModel):
            task_id: str = "TASK-2026-001"
            target_identifier: str = "TARGET-BIO-KEY"
            primary_metric: float = 28.5
            secondary_metric: float = 14.2
            status_descriptor: str = "DISCORDANT_ANOMALY"
            is_critical_flag: bool = True
            attributes: Dict[str, Any] = {}

        class TIRADSRequest(BaseModel):
            composition: str
            size_cm: float = Field(gt=0, allow_inf_nan=False)
            echogenicity: str | None = None
            shape: str | None = None
            margin: str | None = None
            echogenic_foci: list[str] = Field(default_factory=list)

        class ChatRequest(BaseModel):
            query: str

        @app.get("/health")
        def health():
            return {"status": "HEALTHY", "system": "thyroid-ultrasound-ti-rads-agent", "domain": "Endocrinology AI", "version": "2.0.0-FRONTIER"}

        @app.post("/api/audit")
        def api_audit(req: TaskRequest):
            payload = FrontierPayload(
                task_id=req.task_id,
                target_identifier=req.target_identifier,
                primary_metric=req.primary_metric,
                secondary_metric=req.secondary_metric,
                status_descriptor=req.status_descriptor,
                is_critical_flag=req.is_critical_flag,
                attributes=req.attributes,
            )
            return coordinator.process(payload)

        @app.post("/api/ti-rads")
        def api_tirads(req: TIRADSRequest):
            try:
                return score_tirads(**req.model_dump())
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

        @app.post("/api/chat")
        def api_chat(req: ChatRequest):
            return {"response": coordinator.query_supervisory_chat(req.query)}

        return app
    except ImportError:
        return None
