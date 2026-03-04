from pydantic import BaseModel, Field
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.graph_state import AgentState

class ConversationResponse(BaseModel):
    intent_type: str = Field(description="One of: 'ordering', 'refill_inquiry', 'general', 'prescription_upload'")
    medicine: Optional[str] = Field(None, description="The name of the medicine, if mentioned")
    quantity: Optional[int] = Field(None, description="The ordered quantity, if mentioned")
    dosage_frequency: Optional[str] = Field(None, description="The dosage frequency, if mentioned")
    reply: str = Field(description="A friendly conversational reply back to the user")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(ConversationResponse)

async def conversation_agent_node(state: AgentState):
    # Extract recent history (last 10 turns) to give the agent memory without context bloat
    recent_history = state.get("chat_history", [])[-10:]
    
    # Build prescription awareness
    rx_context = state.get("prescription_context", "")
    rx_instruction = f"\n\nPRESCRIPTION CONTEXT: {rx_context}" if rx_context else ""
    
    messages = [
        ("system", "You are the Conversation Agent for Dhanvan-SageAI, an expert pharmacy system. "
                   "Analyze the patient's input. "
                   "Determine their intent ('ordering', 'refill_inquiry', 'general', 'prescription_upload'). "
                   "Extract any mentioned medicine name, quantity, and dosage frequency. "
                   "CRITICAL: If the user wants to order a medicine but has NOT specified the quantity, set intent_type to 'general' and ask for the quantity. Once you have the medicine name AND quantity, set intent to 'ordering'. Dosage frequency is optional — do NOT keep asking for it repeatedly. "
                   "IMPORTANT: If the patient says 'order it' or 'order these' and there is a PRESCRIPTION CONTEXT below, use the FIRST medicine from the prescription. Set intent to 'ordering' with that medicine name and quantity. "
                   "IMPORTANT: Always remember the conversation context below."
                   + rx_instruction)
    ]
    
    # Inject history
    for msg in recent_history:
        role = "assistant" if msg["role"] == "assistant" else "user"
        messages.append((role, msg["content"]))
        
    messages.append(("user", state["input_text"]))
    
    prompt = ChatPromptTemplate.from_messages(messages)
    chain = prompt | structured_llm
    
    try:
        response: ConversationResponse = await chain.ainvoke({"input_text": state["input_text"]})
        
        state["intent_type"] = response.intent_type
        state["extracted_entities"] = {
            "medicine": response.medicine,
            "quantity": response.quantity or 1,
            "dosage_frequency": response.dosage_frequency
        }
        state["agent_reply"] = response.reply
    except Exception as e:
        print(f"Agent Parsing Error: {e}")
        state["intent_type"] = "error"
        state["extracted_entities"] = {}
        state["agent_reply"] = "I had trouble understanding that clearly. Could you specify the medicine name, quantity, and dosage frequency?"
        
    return state

