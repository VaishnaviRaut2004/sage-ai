# Failure Minimization Strategy (AGENTS.md Alignment)

## Core Issue Addressed
The UI bug where an order was confirmed despite the medicine not existing was a symptom of an orchestration mismatch. The system was temporarily trusting probabilistic output (`intent_type: ordering` from the Conversation Agent LLM) and passing it directly to the deterministic UI, bypassing the backend validation (`pharmacy_agent`).

## Mitigation Strategy Implemented

In alignment with the `AGENTS.md` 3-Layer Architecture principles:

### 1. Enforcing Deterministic Boundaries
- **Action**: Modified `chat.py` to mask the raw LLM intent if deterministic validation fails. 
- **Principle Check**: Pushes complexity into deterministic code (`chat.py` overrides the probabilistic layer). The UI will now strictly rely on the validation boolean rather than the LLM's guess.

### 2. Strict Type Enforcement on LLMs
- **Action**: Completely removed raw JSON string parsing from `conversation_agent.py`. Replaced it with Langchain's `with_structured_output(ConversationResponse)` using Pydantic `BaseModel`.
- **Principle Check**: Probabilistic tools (LLMs) are now forced by the orchestration layer to return strictly typed structures. This eliminates hallucinatory keys, missing required fields, and markdown parsing errors.

### 3. Comprehensive Edge-Case Testing
- **Action**: Moving forward to the `Units Generation` phase of the AI-DLC workflow. 
- **Principle Check**: We are generating robust `pytest` and `playwright` suites to continuously evaluate these deterministic safety nets (the Layer 3 Python execution scripts) against edge cases.

## Future Recommendations
- Do not expose raw LLM `intent_types` directly to the frontend.
- Bind all Langchain nodes to strictly defined Pydantic `BaseModels`.
- Always implement a fallback validation layer between an LLM decision-maker and a database-writing action node.
