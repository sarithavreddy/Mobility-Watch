from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.alert import AlertType, AlertPriority, AlertStatus


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    type: AlertType
    priority: AlertPriority
    status: AlertStatus
    message: str
    screenshot_path: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None


class AlertResolve(BaseModel):
    resolution_notes: Optional[str] = None
