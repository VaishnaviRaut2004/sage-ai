# Unit of Work Dependency Matrix

This document maps the technical dependencies between the testing units.

| Source Unit | Target Dependency | Reason |
|:---|:---|:---|
| `U_FRONTEND_E2E` | `U_BACKEND_QA` | The E2E Playwright tests require the backend logic to be stable and predictable before running browser flows. |
| `U_LANGSMITH_EVAL` | `U_BACKEND_QA` | The LLM evaluations run directly against the Langchain agent nodes, which are proven functionally viable by the Backend QA unit. |

**Critical Path**: `U_BACKEND_QA` -> `U_LANGSMITH_EVAL` -> `U_FRONTEND_E2E`
