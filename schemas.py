from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime
from models import JobStatus, CertificateStatus

class RecipientBase(BaseModel):
    name: str
    email: EmailStr

class JobCreate(BaseModel):
    recipients: List[RecipientBase]

class CertificateResponse(BaseModel):
    id: int
    recipient_name: str
    recipient_email: str
    status: CertificateStatus
    file_path: Optional[str] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class JobResponse(BaseModel):
    id: int
    status: JobStatus
    created_at: datetime
    certificates: List[CertificateResponse]

    model_config = ConfigDict(from_attributes=True)
