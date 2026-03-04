# Units of Work Definition

This document defines the functional units (epics/components) that make up the SageAI Pharmacy Automated QA Suite.

## Unit 1: Backend Integration Pipeline (U_BACKEND_QA)
- **Description**: Automated testing of the FastAPI backend and Langchain agent execution without the frontend.
- **Responsibilities**:
  - Test all REST API endpoints
  - Validate database insertion logic (Motor/MongoDB)
  - Verify action agent deterministic state mutations
  - Validate webhook firing events 
- **Tech Stack**: `pytest`, `pytest-asyncio`, `httpx`

## Unit 2: Voice & Visual Frontend E2E (U_FRONTEND_E2E)
- **Description**: End-to-end browser testing of the Patient and Pharmacist dashboards.
- **Responsibilities**:
  - Test login flow and JWT persistence
  - Validate UI state changes on Chat input
  - Verify Web Speech API mocking (if possible) or UI fallback
  - Assert correct rendering of Rupees (`₹`) and conditional Order Cards
- **Tech Stack**: `Playwright`, `TypeScript`

## Unit 3: LLM Evaluation Matrix (U_LANGSMITH_EVAL)
- **Description**: Offline evaluation of the probabilistic LLM components.
- **Responsibilities**:
  - Batch evaluate `conversation_agent` intent extraction accuracy
  - Measure structural conformance to Pydantic BaseModels
  - Validate rejection handling on edge-case user inputs
- **Tech Stack**: `LangSmith Evaluators`, `pytest`
