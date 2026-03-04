# Dependencies

## Internal Dependencies
```mermaid
graph LR
    Frontend --> Backend
    Backend.Routers --> Backend.Agents
    Backend.Agents --> Backend.Services
    Backend.Services --> Backend.Models
```

### Frontend depends on Backend
- **Type**: Runtime
- **Reason**: API Data fetching

## External Dependencies
### OpenAI
- **Version**: Latest via LangChain
- **Purpose**: LLM Inference
- **License**: Proprietary API
