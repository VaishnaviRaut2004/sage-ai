# Unit of Work Story Map

This document maps feature stories (from requirements) to their primary validation units to ensure comprehensive test coverage.

## `U_BACKEND_QA`
- **Story**: As a patient, I want to upload my prescription so the system can read it.
- **Story**: As a pharmacist, I want refill alert background jobs to decrement stock.
- **Story**: As the system, I must fail an order if the `pharmacy_agent` validation fails.

## `U_FRONTEND_E2E`
- **Story**: As a patient, I want to see my order rendered visually with the correct `₹` Rupee formatting.
- **Story**: As a pharmacist, I want to click 'Send Alert' and see a toast notification.
- **Story**: As a patient, I want a clear visual error if my requested medicine is not found.

## `U_LANGSMITH_EVAL`
- **Story**: As the system, I must accurately extract 'quantity' and 'dosage_frequency' from natural language.
- **Story**: As the system, I must correctly classify inputs into 'ordering', 'general', or 'refill_inquiry' intents.
