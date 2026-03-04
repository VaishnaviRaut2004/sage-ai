# Requirement Verification Questions

Please provide answers to the following clarifying questions to help me define the exact requirements for testing the AI agent workflow with multiple edge cases. 

Fill in your answers after the `[Answer]:` blocks.

---

## Question 1: Scope of Edge Cases
Which specific categories of edge cases should we focus on testing? (You can select multiple or provide custom cases)

A) **Input Handling**: Unrecognized/misspelled medicine names, extremely high quantities, empty messages.
B) **Prescription Vision**: Blurry images, non-prescription images, conflicting text vs. image data.
C) **Agent Conversation State**: Interrupting the flow, changing topics mid-order, complex multi-turn requests.
D) **Security/Auth**: Unauthenticated access attempts, invalid tokens, simulated prompt injections.
X) Other (please describe after [Answer]: tag below)

[Answer]: 
A) **Input Handling**: Unrecognized/misspelled medicine names, extremely high quantities, empty messages.
B) **Prescription Vision**: Blurry images, non-prescription images, conflicting text vs. image data.
C) **Agent Conversation State**: Interrupting the flow, changing topics mid-order, complex multi-turn requests.
D) **Security/Auth**: Unauthenticated access attempts, invalid tokens, simulated prompt injections.
---

## Question 2: Testing Methodology
How would you like these tests to be implemented and executed?

A) **Automated Backend Tests**: New `pytest` suites focusing on the LangGraph agents and FastAPI routers directly.
B) **End-to-End Automation**: Playwright/Cypress scripts testing the full UI flow.
C) **LangSmith Evaluations**: Creating datasets in LangSmith to continuously evaluate the AI agent outputs.
D) **Manual/Scripted UI verification**: A script or documented process for manual verification via the UI.
X) Other (please describe after [Answer]: tag below)

[Answer]: 
A) **Automated Backend Tests**: New `pytest` suites focusing on the LangGraph agents and FastAPI routers directly.
B) **End-to-End Automation**: Playwright/Cypress scripts testing the full UI flow.
C) **LangSmith Evaluations**: Creating datasets in LangSmith to continuously evaluate the AI agent outputs.
---

## Question 3: Error Handling & Graceful Degradation
When the AI agent encounters an edge case it cannot handle (e.g., completely incomprehensible input), what is the desired graceful fallback behavior?

A) Return a standard polite error message asking for clarification.
B) Escalate the conversation to be visible/flagged for the Pharmacist Dashboard.
C) Terminate the active graph state and reset the conversation.
X) Other (please describe after [Answer]: tag below)

[Answer]: 
A) Return a standard polite error message asking for clarification.
---

## Question: Security Extensions
Should security extension rules be enforced for this project?

A) Yes — enforce all SECURITY rules as blocking constraints (recommended for production-grade applications)
B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)
X) Other (please describe after [Answer]: tag below)

[Answer]: 

B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)