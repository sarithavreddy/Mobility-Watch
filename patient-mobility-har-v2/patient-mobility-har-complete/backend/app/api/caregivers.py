from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.caregiver import CaregiverCreate, CaregiverOut, CaregiverUpdate
from app.services import caregiver_service, patient_service

router = APIRouter(prefix="/api/v1/caregivers", tags=["Caregivers"])


def _get_or_404(db: Session, caregiver_id: int):
    caregiver = caregiver_service.get_caregiver(db, caregiver_id)
    if not caregiver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caregiver not found")
    return caregiver


def _get_patient_or_404(db: Session, patient_id: int):
    patient = patient_service.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.get("", response_model=List[CaregiverOut])
def list_caregivers(
    patient_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return caregiver_service.list_caregivers(db, patient_id)


@router.post("", response_model=CaregiverOut, status_code=status.HTTP_201_CREATED)
def create_caregiver(payload: CaregiverCreate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return caregiver_service.create_caregiver(db, payload)


@router.get("/{caregiver_id}", response_model=CaregiverOut)
def get_caregiver(caregiver_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return _get_or_404(db, caregiver_id)


@router.put("/{caregiver_id}", response_model=CaregiverOut)
def update_caregiver(
    caregiver_id: int, payload: CaregiverUpdate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
):
    caregiver = _get_or_404(db, caregiver_id)
    return caregiver_service.update_caregiver(db, caregiver, payload)


@router.delete("/{caregiver_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_caregiver(caregiver_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    caregiver = _get_or_404(db, caregiver_id)
    caregiver_service.delete_caregiver(db, caregiver)


@router.post("/{caregiver_id}/assign/{patient_id}", response_model=CaregiverOut)
def assign_caregiver(
    caregiver_id: int, patient_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
):
    caregiver = _get_or_404(db, caregiver_id)
    patient = _get_patient_or_404(db, patient_id)
    return caregiver_service.assign_to_patient(db, caregiver, patient)


@router.delete("/{caregiver_id}/assign/{patient_id}", response_model=CaregiverOut)
def unassign_caregiver(
    caregiver_id: int, patient_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
):
    caregiver = _get_or_404(db, caregiver_id)
    patient = _get_patient_or_404(db, patient_id)
    return caregiver_service.unassign_from_patient(db, caregiver, patient)
