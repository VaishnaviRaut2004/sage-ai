# U_BACKEND_QA: Code Generation Plan

This document outlines the code generation steps for the `U_BACKEND_QA` unit of work. This unit covers the Pytest suite for the FastAPI backend and Motor DB logic.

## Prerequisites
- [x] Ensure `pytest`, `pytest-asyncio`, and `httpx` dependencies are installed (Already verified in previous OCR tests).

## Code Generation Steps
- [ ] **Step 1: Setup Test Infrastructure**
  - Create `backend/tests/conftest.py` with mock database fixtures or test DB connections.
  - Configure `pytest.ini` for asyncio.

- [ ] **Step 2: Endpoint Integration Tests (`test_api.py`)**
  - Write tests for `POST /api/auth/register` and `/api/auth/login`.
  - Write tests for Pharmacist Dashboard endpoints (`GET /api/inventory`, `GET /api/orders`, `PATCH /api/orders/{id}/status`).
  - Write tests for `POST /api/chat` using mock LLM responses to avoid external API calls during basic QA.

- [ ] **Step 3: Service Layer Tests (`test_services.py` & `test_ocr.py`)**
  - Expand the OCR test to mock internal extraction logic.
  - Test `pdf_service.py` invoice generation.

- [ ] **Step 4: Agent Logic Tests (`test_agents.py`)**
  - Test the deterministic checks within `pharmacy_agent.py` (medicine existence, logic trees).

## Completion Criteria
When these steps are marked complete, the `U_BACKEND_QA` unit will be ready for the Build and Test phase.
