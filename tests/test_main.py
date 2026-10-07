import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import shutil
import time

from main import app, get_db
from database import Base
from generator import OUTPUT_DIR

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

import main
main.SessionLocal = TestingSessionLocal

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def clean_generated_dir():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    yield
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

def test_create_job_and_progress_and_retrieve():
    response = client.post(
        "/jobs/",
        json={"recipients": [{"name": "Alice", "email": "alice@example.com"}, {"name": "Bob", "email": "bob@example.com"}]}
    )
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    job_id = data["id"]
    
    # Wait for background task
    time.sleep(1)
    
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    
    certificates = data["certificates"]
    assert len(certificates) == 2
    for cert in certificates:
        assert cert["status"] == "SUCCESS"
        assert cert["file_path"] is not None
        
        # Test download
        dl_response = client.get(f"/certificates/{cert['id']}/download")
        assert dl_response.status_code == 200
        assert dl_response.headers["content-type"] == "application/pdf"

def test_input_validation():
    # Invalid email
    response = client.post(
        "/jobs/",
        json={"recipients": [{"name": "Alice", "email": "not-an-email"}]}
    )
    assert response.status_code == 422
    
    # Missing recipients
    response = client.post(
        "/jobs/",
        json={"recipients": []}
    )
    assert response.status_code == 400

def test_individual_failure():
    # "Error User" will trigger an intentional failure in generator.py
    response = client.post(
        "/jobs/",
        json={"recipients": [{"name": "Error User", "email": "error@example.com"}, {"name": "Valid User", "email": "valid@example.com"}]}
    )
    assert response.status_code == 202
    job_id = response.json()["id"]
    
    time.sleep(1)
    
    response = client.get(f"/jobs/{job_id}")
    data = response.json()
    assert data["status"] == "COMPLETED"
    
    certs = {c["recipient_name"]: c for c in data["certificates"]}
    
    assert certs["Error User"]["status"] == "FAILED"
    assert "Simulated error" in certs["Error User"]["error_message"]
    
    assert certs["Valid User"]["status"] == "SUCCESS"
    assert certs["Valid User"]["file_path"] is not None
