import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")

DEFAULT_ANALYSIS_PROMPT = (
    "Review the uploaded PDF. Extract structured data as JSON, including any tables, "
    "financial figures, dates, entities, and key findings. "
    "If there is a paragraph extract the text of that paragraph and include it in the output JSON under a 'paragraph' key."
)


def validate_environment():
    """Ensure all required environment variables are available."""
    missing = [
        name
        for name, value in {
            "AZURE_OPENAI_ENDPOINT": endpoint,
            "AZURE_OPENAI_DEPLOYMENT": deployment,
            "AZURE_OPENAI_API_KEY": subscription_key,
            "AZURE_OPENAI_API_VERSION": api_version,
        }.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )


def prompt_for_pdf_path() -> Path:
    """Return the hard-coded PDF path required by the workflow."""
    candidate = Path("data") / "page_3.pdf"

    if not candidate.exists():
        raise FileNotFoundError(
            f"PDF file '{candidate}' not found. Place the file at this location before running the script."
        )

    if candidate.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file at '{candidate}', found '{candidate.suffix}' instead.")

    return candidate


def _sanitize_basename(raw_name: Optional[str]) -> str:
    """Return a filesystem-friendly base name for output artifacts."""
    if not raw_name:
        return ""

    cleaned = [c if c.isalnum() or c in {"-", "_"} else "-" for c in raw_name.strip()]
    candidate = "".join(cleaned).strip("-_")
    return candidate or ""


def build_input_blocks(file_id: str, user_prompt: str) -> list[dict]:
    """Prepare the Responses API input payload with the uploaded file."""
    if not user_prompt:
        user_prompt = DEFAULT_ANALYSIS_PROMPT

    return [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": user_prompt},
                {"type": "input_file", "file_id": file_id},
            ],
        }
    ]


def extract_response_content(response) -> str:
    """Flatten a Responses API payload into printable text."""
    output_text = getattr(response, "output_text", None)
    if output_text:
        if isinstance(output_text, (list, tuple)):
            joined = "\n".join(str(block) for block in output_text if block)
            if joined.strip():
                return joined.strip()
        elif isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

    # New Responses API objects expose `output` with structured content blocks.
    output = getattr(response, "output", None)
    if output:
        parts: list[str] = []
        for item in output:
            content_blocks = None
            if hasattr(item, "content"):
                content_blocks = getattr(item, "content")
            elif isinstance(item, dict):
                content_blocks = item.get("content")
            if not content_blocks:
                continue
            for block in content_blocks:
                if isinstance(block, dict):
                    block_type = block.get("type")
                    if block_type in {"output_text", "text"}:
                        parts.append(block.get("text", ""))
                else:
                    text_value = getattr(block, "text", None)
                    if text_value:
                        parts.append(text_value)
        if parts:
            return "\n".join(filter(None, parts)).strip()

    # Fallback for legacy chat completions (shouldn't be hit now but keeps compatibility).
    choices = getattr(response, "choices", None)
    if choices:
        message = choices[0].message
        content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
        if isinstance(content, list):
            parts = [item.get("text", "") for item in content if isinstance(item, dict)]
            return "\n".join(parts).strip()
        if isinstance(content, str):
            return content

    return str(response)


def process_pdf_file(
    pdf_path: Path,
    user_prompt: Optional[str] = None,
    output_basename: Optional[str] = None,
) -> Dict[str, Any]:
    """Upload a PDF to Azure OpenAI, request analysis, and persist the structured output."""
    validate_environment()

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file '{pdf_path}' not found.")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, received '{pdf_path.suffix}' instead.")

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=subscription_key,
    )

    with pdf_path.open("rb") as pdf_file:
        uploaded_file = client.files.create(file=pdf_file, purpose="assistants")

    inputs = build_input_blocks(uploaded_file.id, user_prompt or DEFAULT_ANALYSIS_PROMPT)

    response = client.responses.create(
        model=deployment,
        input=inputs,
        max_output_tokens=int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "6000")),
        temperature=float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0")),
    )

    result_text = extract_response_content(response)

    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    base_name = _sanitize_basename(output_basename) or pdf_path.stem
    target_json = output_dir / f"{base_name}_structured_output.json"

    saved_path: Path
    parsed_payload: Optional[Dict[str, Any]] = None
    saved_as_json = False

    try:
        parsed_payload = json.loads(result_text)
        with target_json.open("w", encoding="utf-8") as f:
            json.dump(parsed_payload, f, indent=2)
        saved_path = target_json
        saved_as_json = True
    except json.JSONDecodeError:
        fallback_path = target_json.with_suffix(".txt")
        fallback_path.write_text(result_text, encoding="utf-8")
        saved_path = fallback_path

    return {
        "raw_output": result_text,
        "saved_path": saved_path,
        "saved_as_json": saved_as_json,
        "parsed_json": parsed_payload,
    }


def main():
    """CLI helper to keep backwards compatibility for local runs."""
    pdf_path = prompt_for_pdf_path()
    user_prompt = input(
        "Enter your analysis request (press Enter for default JSON extraction): "
    ).strip()

    result = process_pdf_file(pdf_path, user_prompt=user_prompt)

    print("\n=== Model Output ===")
    print(result["raw_output"])
    print(f"\nSaved output to {result['saved_path']}")


if __name__ == "__main__":
    main()
