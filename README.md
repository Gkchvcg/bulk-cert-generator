# Bulk Certificate Generator

A bulk certificate generation backend API built with FastAPI. It allows you to submit a list of recipients and generates PDF certificates asynchronously.

## Technology Stack
- **Python 3**
- **FastAPI**: Web framework for building the API
- **SQLAlchemy + SQLite**: Relational database ORM (SQLite used for simplicity and ease of setup)
- **ReportLab**: Library to generate PDF certificates
- **Pytest**: Testing framework

## Setup Project

1. Clone or download the repository.
2. Ensure you have Python 3 installed.
3. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install the required dependencies:
   ```bash
   pip install fastapi uvicorn sqlalchemy pydantic reportlab pytest httpx python-multipart email-validator dnspython
   ```

## Running the Application

1. Make sure your virtual environment is activated.
2. Start the FastAPI development server using `uvicorn`:
   ```bash
   uvicorn main:app --reload
   ```
3. The server will start at `http://127.0.0.1:8000`. You can access the interactive Swagger documentation at `http://127.0.0.1:8000/docs`.

## Running Tests

1. Make sure your virtual environment is activated.
2. Run pytest:
   ```bash
   PYTHONPATH=. pytest tests/
   ```

## API Usage

### Submit a Certificate Generation Request

Send a POST request to `/jobs/` to initiate a generation job. The API handles processing asynchronously in the background.

**Endpoint:** `POST /jobs/`

**Request Body:**
```json
{
  "recipients": [
    {"name": "Alice Johnson", "email": "alice@example.com"},
    {"name": "Bob Smith", "email": "bob@example.com"}
  ]
}
```

**Response:**
Returns the newly created job ID and its current status (`PENDING`).

### Check Job Status

You can retrieve the status of a specific job and all of its associated certificates. 
This tells you which generations succeeded and which failed.

**Endpoint:** `GET /jobs/{job_id}`

**Response:**
```json
{
  "id": 1,
  "status": "COMPLETED",
  "created_at": "2023-10-27T10:00:00Z",
  "certificates": [
    {
      "id": 1,
      "recipient_name": "Alice Johnson",
      "recipient_email": "alice@example.com",
      "status": "SUCCESS",
      "file_path": "generated_certificates/1_1_uuid.pdf",
      "error_message": null
    },
    {
      "id": 2,
      "recipient_name": "Bob Smith",
      "recipient_email": "bob@example.com",
      "status": "FAILED",
      "file_path": null,
      "error_message": "Some internal error occurred"
    }
  ]
}
```

### Retrieve Generated Certificates

Once a certificate shows a status of `SUCCESS`, it can be downloaded.

**Endpoint:** `GET /certificates/{certificate_id}/download`

This endpoint returns the actual PDF file for the certificate.

## Design Decisions

- **FastAPI**: Chosen for its built-in async capabilities, ease of validation with Pydantic, and automatic Swagger documentation.
- **SQLite Database**: A relational database is used (as per requirements). SQLite is used because it requires zero configuration for this specific test assignment. In production, this can be swapped for PostgreSQL simply by changing the `DATABASE_URL` in `database.py`.
- **Background Processing**: The processing handles certificates in bulk. Instead of keeping the HTTP request open during PDF generation (which could timeout for a large number of certificates), we return a `202 Accepted` response immediately. `BackgroundTasks` provided by FastAPI is used to process the PDFs in the background without needing a complex message queue setup (like Celery/Redis), keeping the project lightweight and simple to run while meeting the requirement.
- **Error Handling**: A failure in one certificate generation (e.g. invalid characters for the font) will be caught individually and its status marked as `FAILED`. It doesn't halt the loop; the rest of the job will continue processing.
