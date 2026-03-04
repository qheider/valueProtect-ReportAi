import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")


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


def build_input_blocks(file_id: str, user_prompt: str) -> list[dict]:
    """Prepare the Responses API input payload with the uploaded file."""
    if not user_prompt:
        user_prompt = (
            "Review the uploaded PDF. Extract structured data as JSON, including any tables, "
            "financial figures, dates, entities, and key findings. "
            "If there is a paragraph extract the text of that paragraph and include it in the output JSON under a 'paragraph' key."
        )

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


def main():
    """Upload a PDF to Azure OpenAI and request structured analysis."""
    validate_environment()

    pdf_path = prompt_for_pdf_path()
    user_prompt = input(
        "Enter your analysis request (press Enter for default JSON extraction): "
    ).strip()

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=subscription_key,
    )

    print(f"Uploading {pdf_path.name} to Azure OpenAI...")
    with pdf_path.open("rb") as pdf_file:
        uploaded_file = client.files.create(file=pdf_file, purpose="assistants")

    print(f"Uploaded file ID: {uploaded_file.id}")

    inputs = build_input_blocks(uploaded_file.id, user_prompt)

    print("Requesting structured analysis from GPT-4.1...")
    response = client.responses.create(
        model=deployment,
        input=inputs,
        max_output_tokens=int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "6000")),
        temperature=float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0")),
    )

    result_text = extract_response_content(response)
    print("\n=== Model Output ===")
    print(result_text)

    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{pdf_path.stem}_structured_output.json"
    try:
        parsed = json.loads(result_text)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2)
        print(f"\nSaved structured JSON to {output_file}")
    except json.JSONDecodeError:
        fallback_path = output_file.with_suffix(".txt")
        with open(fallback_path, "w", encoding="utf-8") as f:
            f.write(result_text)
        print(
            "\nModel output was not valid JSON. Saved raw text instead for manual review."
        )


if __name__ == "__main__":
    main()
