"""FastAPI service that processes PDFs via Azure OpenAI."""
from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Annotated, Any, Dict

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from jose import JWTError, jwt
from pydantic import BaseModel, Field, HttpUrl

from azureopenaicall import process_pdf_file

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ValueProtect PDF Processor", version="1.0.0")

DATA_DIR = Path("data")
DOWNLOADS_DIR = DATA_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")
JWT_ISSUER = os.getenv("JWT_ISSUER")
PDF_DOWNLOAD_TIMEOUT = float(os.getenv("PDF_DOWNLOAD_TIMEOUT", "60"))
MAX_FILE_SIZE_MB = float(os.getenv("MAX_PDF_SIZE_MB", "25"))


class ProcessPdfRequest(BaseModel):
    pdf_url: HttpUrl = Field(..., description="Publicly reachable URL pointing to the PDF to analyze.")
    prompt: str | None = Field(
        None,
        description="Optional custom instructions that replace the default structured extraction prompt.",
    )
    output_basename: str | None = Field(
        None,
        max_length=80,
        description="Optional base filename (no extension) for saving the structured output.",
    )


class ProcessPdfResponse(BaseModel):
    saved_path: str
    saved_as_json: bool
    parsed_json: Dict[str, Any] | None
    raw_output: str


async def _download_pdf(source_url: str) -> Path:
    """Download the PDF to a temporary location and return the path."""
    target_path = DOWNLOADS_DIR / f"{uuid.uuid4().hex}.pdf"

    try:
        async with httpx.AsyncClient(timeout=PDF_DOWNLOAD_TIMEOUT) as client:
            async with client.stream("GET", str(source_url)) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to download PDF: {exc}",
                    ) from exc

                total_bytes = 0
                with target_path.open("wb") as file_obj:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        total_bytes += len(chunk)
                        if total_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
                            raise HTTPException(
                                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                detail="PDF exceeds maximum allowed size.",
                            )
                        file_obj.write(chunk)
    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to connect to PDF source: {source_url}. Ensure the service is running and accessible.",
        ) from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout while downloading PDF from {source_url}",
        ) from exc
    except HTTPException:
        raise
    except Exception:
        if target_path.exists():
            target_path.unlink(missing_ok=True)
        raise

    if not target_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF download failed for an unknown reason.",
        )

    return target_path


def _verify_jwt(
    authorization: Annotated[str | None, Header(alias="Authorization")]
) -> Dict[str, Any]:
    """Ensure the request Authorization header contains a valid JWT."""
    if not JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET is not configured on the server.",
        )

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()
    # Allow multiple algorithms - adjust based on your token issuer's configuration
    decode_kwargs: Dict[str, Any] = {"algorithms": ["HS256", "RS256"]}

    if JWT_AUDIENCE:
        decode_kwargs["audience"] = JWT_AUDIENCE
    else:
        decode_kwargs.setdefault("options", {})["verify_aud"] = False

    if JWT_ISSUER:
        decode_kwargs["issuer"] = JWT_ISSUER
    else:
        # Disable issuer verification if not configured
        decode_kwargs.setdefault("options", {})["verify_iss"] = False

    try:
        payload = jwt.decode(token, JWT_SECRET, **decode_kwargs)
        # Log the actual issuer for debugging
        logger.info("Token decoded successfully. Issuer: %s", payload.get("iss"))
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return payload


@app.get("/health", tags=["health"])
async def healthcheck() -> Dict[str, str]:
    """Simple readiness probe for orchestrators."""
    return {"status": "ok"}


@app.post("/process-pdf", response_model=ProcessPdfResponse, tags=["processing"])
async def process_pdf_endpoint(
    request: ProcessPdfRequest,
    _: Dict[str, Any] = Depends(_verify_jwt),
) -> ProcessPdfResponse:
    """Download a PDF, run Azure OpenAI extraction, and persist the structured result."""
    pdf_path: Path | None = None

    try:
        pdf_path = await _download_pdf(request.pdf_url)
        logger.info("Downloaded PDF from %s to %s", request.pdf_url, pdf_path)

        result = await run_in_threadpool(
            process_pdf_file,
            pdf_path,
            request.prompt,
            request.output_basename,
        )

        saved_path = result["saved_path"]
        if isinstance(saved_path, Path):
            saved_path = str(saved_path)

        return ProcessPdfResponse(
            saved_path=str(saved_path),
            saved_as_json=bool(result.get("saved_as_json")),
            parsed_json=result.get("parsed_json"),
            raw_output=result.get("raw_output", ""),
        )
    finally:
        if pdf_path and pdf_path.exists():
            try:
                pdf_path.unlink()
            except OSError:
                logger.warning("Unable to delete temporary file %s", pdf_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
