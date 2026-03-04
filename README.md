# Azure OpenAI PDF Analyzer

This application analyzes PDF documents using Azure OpenAI GPT-4 model.

## Features

- **PDF Text Extraction**: Automatically extracts text from PDF files
- **Smart Analysis**: Uses Azure OpenAI to provide comprehensive document analysis
- **Interactive Querying**: Ask specific questions about your PDF content
- **Command Line Support**: Run with PDF path as argument or interactive mode

## Setup

1. **Virtual Environment**: Already configured in `venv/` folder
2. **Dependencies**: Install with `pip install -r requirements.txt`
3. **Environment Variables**: Configure your Azure OpenAI credentials in `.env`

## Usage

### Method 1: Command Line Argument
```bash
python azureopenaicall.py "path/to/your/document.pdf"
```

### Method 2: Interactive Mode
```bash
python azureopenaicall.py
# Then enter PDF path when prompted
```

## Example Usage

```bash
# Analyze a research paper
python azureopenaicall.py "research_paper.pdf"

# Analyze with specific question
python azureopenaicall.py "contract.pdf"
# When prompted: "What are the key terms and conditions?"
```

## What the Analysis Includes

1. **Document Summary**: Overview of the content
2. **Key Points**: Main themes and findings
3. **Important Details**: Critical information extracted
4. **Conclusions**: Recommendations or conclusions from the document
5. **Custom Answers**: Responses to your specific questions

## Supported File Types

- PDF files (.pdf extension required)
- Text-based PDFs (scanned images may not extract properly)

## Configuration

Adjust analysis behavior in `.env` file:
- `AZURE_OPENAI_MAX_TOKENS`: Response length (default: 4000)
- `AZURE_OPENAI_TEMPERATURE`: Creativity level (0.1 for factual, 1.0 for creative)

## Error Handling

The script handles common errors:
- File not found
- Invalid file format
- PDF reading errors
- API connection issues

## Virtual Environment Commands

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the script
python azureopenaicall.py

# Deactivate when done
deactivate
```