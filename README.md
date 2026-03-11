# ValueProtect Report AI API

FastAPI wrapper around the existing Azure OpenAI PDF analyzer. The service accepts a PDF URL, streams the file into a temporary workspace, runs GPT-based extraction, and persists the structured output locally just like the original script.

## Features
- REST endpoint `POST /process-pdf` secured with JWT Bearer tokens
- Automatic PDF download and size guarding before invoking Azure OpenAI
- Reusable extraction service that still supports the legacy CLI workflow
- Results saved to the `output/` folder as JSON (with `.txt` fallback) for downstream systems
- Health probe at `/health` for container orchestrators

## Prerequisites
- Python 3.10+
- Azure OpenAI deployment with access to the Responses API
- A shared secret (or compatible signing key) for issuing JWTs from the Spring Boot service

## Setup
1. Create/activate a virtual environment (example for PowerShell):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file (see *Environment Variables* below).

## Environment Variables
| Name | Description |
| --- | --- |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL (e.g., `https://my-resource.openai.azure.com/`). |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name for the GPT-4.1 (or compatible) model. |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key. |
| `AZURE_OPENAI_API_VERSION` | API version (e.g., `2024-02-01`). |
| `AZURE_OPENAI_MAX_TOKENS` | *(Optional)* Override max output tokens (default `6000`). |
| `AZURE_OPENAI_TEMPERATURE` | *(Optional)* Sampling temperature (default `0`). |
| `JWT_SECRET` | Symmetric key that Spring Boot uses to sign Bearer tokens. Required. |
| `JWT_ALGORITHM` | *(Optional)* Signing algorithm (default `HS256`). |
| `JWT_AUDIENCE` / `JWT_ISSUER` | *(Optional)* Audience/issuer claims to enforce. |
| `PDF_DOWNLOAD_TIMEOUT` | *(Optional)* Timeout (seconds) for downloading PDFs (default `60`). |
| `MAX_PDF_SIZE_MB` | *(Optional)* Reject PDFs larger than this size (default `25`). |
| `PDF_SSL_VERIFY` | *(Optional)* TLS certificate verification for PDF download (`true` by default). Set `false` only for local testing with self-signed certs. |
| `PDF_CA_BUNDLE` | *(Optional)* Path to a custom CA bundle file to trust when downloading PDFs over HTTPS. |
| `PORT` | *(Optional)* Port for `uvicorn` when running via `python main.py` (default `8000`). |

## Running the API
```bash
uvicorn main:app --reload
```
The server exposes:
- `GET /health` – readiness probe.
- `POST /process-pdf` – main processing endpoint (requires `Authorization: Bearer <token>`).

## Request / Response
### POST `/process-pdf`
**Headers**
```
Authorization: Bearer <JWT from Spring Boot>
Content-Type: application/json
```

**Payload**
```json
{
  "pdf_url": "https://example.com/report.pdf",
  "prompt": "Optional custom instructions",
  "output_basename": "optional-file-name"
}
```
- `pdf_url` must be an HTTPS URL accessible by the API host.
- `prompt` overrides the default structured extraction instructions.
- `output_basename` (alphanumeric, `_` or `-`) customizes the saved filename inside `output/`.

**Sample response**
```json
{
  "saved_path": "output/report_structured_output.json",
  "saved_as_json": true,
  "parsed_json": {"...": "..."},
  "raw_output": "... full model response ..."
}
```
If the model returns non-JSON text, the service saves a `.txt` file instead and `parsed_json` becomes `null`.

## Authentication
The API enforces JWT Bearer authentication. Spring Boot should mint tokens signed with the shared `JWT_SECRET` using the configured algorithm. For local testing you can generate a token with Python:
```python
from jose import jwt
payload = {"sub": "local-test-user"}
token = jwt.encode(payload, "super-secret", algorithm="HS256")
print(token)
```
Replace `"super-secret"` with the same secret you load in `.env`.

## Storage Behavior
- PDFs downloaded from URLs are saved under `data/downloads/` temporarily and deleted after processing.
- Structured outputs continue to land in `output/`, mirroring the legacy workflow.
- The CLI script (`python azureopenaicall.py`) still works for manual runs and now delegates to the same processing function used by the API.

## Postman Collection
A ready-to-use collection lives at `postman/valueprotect.postman_collection.json`. Import it into Postman, set the `base_url`, `jwt_token`, and `pdf_url` variables, and you can exercise the endpoint immediately.
