# Cloud OCR Integration Plan (AWS Textract)

Following the **3-Layer Architecture** defined in `AGENTS.md`:

## Layer 1: Directive
The goal is to extract plain text from prescription images reliably and deterministically without local hardware dependencies, utilizing Amazon AWS Textract.

## Layer 2: Orchestration
The FastAPI router `backend/routers/prescriptions.py` will handle the incoming HTTP multipart upload. It will call the deterministic execution script to get the OCR text, and then orchestrate the parsing of that unstructured text into strict JSON using the `gpt-4o-mini` LLM structured output.

## Layer 3: Execution
We will create a pure, deterministic Python script `backend/execution/aws_textract_ocr.py`.
This script will:
1. Accept image bytes.
2. Initialize the `boto3` Textract client (authenticating via `AWS_ACCESS_KEY_ID` in `.env`).
3. Send the bytes to the `detect_document_text` API synchronously.
4. Extract and return the concatenated `Blocks` of type `LINE`.
5. Gracefully handle network/auth errors.

### Implementation Steps:
1. **Dependencies:** Add `boto3` to `requirements.txt`.
2. **Execution Script:** Create `backend/execution/aws_textract_ocr.py` using `boto3.client('textract')`.
3. **Refactoring:** Modify `backend/routers/prescriptions.py` to import from the Textract execution layer instead of passing the image directly to the Vision LLM.

> [!IMPORTANT]
> To execute this plan, we need the AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`) saved in the `.env` file as specified by the user.
