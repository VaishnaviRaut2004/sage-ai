# API Documentation

## REST APIs
### Chat Endpoint
- **Method**: POST
- **Path**: /api/chat
- **Purpose**: Process user natural language input
- **Request**: `{ "message": "string" }`
- **Response**: `{ "text": "string", "order_card": object, "trace_url": "string" }`

### Orders Endpoint
- **Method**: GET
- **Path**: /api/orders
- **Purpose**: Fetch user or all orders
- **Request**: None (Auth Header required)
- **Response**: `[ OrderObject ]`

## Internal APIs
### Database Service
- **Methods**: `get_db()`, `get_collection(name)`
- **Parameters**: collection name
- **Return Types**: Motor Collection

## Data Models
### Order Model
- **Fields**: order_id, patient_id, medicine_name, quantity, status
- **Relationships**: Patient, Medicine
- **Validation**: Pydantic BaseModel validation
