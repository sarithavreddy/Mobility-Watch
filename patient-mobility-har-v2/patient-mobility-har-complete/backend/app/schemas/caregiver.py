from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CaregiverBase(BaseModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    relationship_to_patient: Optional[str] = None
    additional_contact_info: Optional[str] = None


class CaregiverCreate(CaregiverBase):
    patient_ids: List[int] = []


class CaregiverUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    relationship_to_patient: Optional[str] = None
    additional_contact_info: Optional[str] = None


class PatientSummary(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CaregiverOut(CaregiverBase):
    id: int
    created_at: datetime
    patients: List[PatientSummary] = []

    model_config = ConfigDict(from_attributes=True)
