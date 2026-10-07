from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import engine, Base, get_db, SessionLocal
from models import Job, JobStatus, Certificate, CertificateStatus
from schemas import JobCreate, JobResponse
from generator import generate_certificate
import os
import uuid

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bulk Certificate Generator")

def process_job(job_id: int):
    # This function is executed as a background task.
    # We use a separate DB session so we don't interfere with the request session.
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        
        job.status = JobStatus.PROCESSING
        db.commit()
        
        certificates = db.query(Certificate).filter(Certificate.job_id == job_id).all()
        for cert in certificates:
            # We don't want to stop the whole job if one fails
            try:
                # generate a unique filename
                filename = f"{job_id}_{cert.id}_{uuid.uuid4().hex[:8]}.pdf"
                file_path = generate_certificate(cert.recipient_name, filename)
                
                cert.status = CertificateStatus.SUCCESS
                cert.file_path = file_path
                db.commit()
            except Exception as e:
                # Catch specific exception and log it
                db.rollback()
                # Update status of this specific cert
                cert.status = CertificateStatus.FAILED
                cert.error_message = str(e)
                db.commit()
                
        # All certificates processed, mark job completed
        job.status = JobStatus.COMPLETED
        db.commit()
    finally:
        db.close()


@app.post("/jobs/", response_model=JobResponse, status_code=202)
def create_job(job_in: JobCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not job_in.recipients:
        raise HTTPException(status_code=400, detail="At least one recipient must be provided")

    job = Job(status=JobStatus.PENDING)
    db.add(job)
    db.commit()
    db.refresh(job)
    
    for recipient in job_in.recipients:
        cert = Certificate(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=recipient.email,
            status=CertificateStatus.PENDING
        )
        db.add(cert)
        
    db.commit()
    
    # Offload the heavy generation process to a background task
    background_tasks.add_task(process_job, job.id)
    
    db.refresh(job)
    return job

@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/certificates/{cert_id}/download")
def download_certificate(cert_id: int, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    if cert.status != CertificateStatus.SUCCESS or not cert.file_path:
        raise HTTPException(status_code=400, detail="Certificate is not available yet or failed to generate")
        
    if not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="Certificate file missing")
        
    safe_name = cert.recipient_name.replace(' ', '_').replace('/', '_')
    return FileResponse(
        path=cert.file_path, 
        filename=f"certificate_{safe_name}.pdf",
        media_type="application/pdf"
    )
