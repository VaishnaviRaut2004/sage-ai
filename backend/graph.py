from langgraph.graph import StateGraph, END
from backend.graph_state import AgentState
from backend.agents.conversation_agent import conversation_agent_node
from backend.agents.pharmacy_agent import pharmacy_agent_node
from backend.agents.inventory_agent import inventory_agent_node
from backend.agents.prediction_agent import prediction_agent_node
from backend.agents.action_agent import action_agent_node

# Create the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("conversation_agent", conversation_agent_node)
workflow.add_node("pharmacy_design_agent", pharmacy_agent_node)
workflow.add_node("inventory_agent", inventory_agent_node)
workflow.add_node("prediction_agent", prediction_agent_node)
workflow.add_node("action_agent", action_agent_node)

# Define edges
workflow.set_entry_point("conversation_agent")

def route_after_conversation(state: AgentState):
    if state.get("intent_type") == "ordering":
        return "pharmacy_design_agent"
    return "prediction_agent" # Non-orders can still trigger predictions if requested

workflow.add_conditional_edges("conversation_agent", route_after_conversation)

def route_after_pharmacy(state: AgentState):
    if not state.get("validation_passed"):
        return END
    return "inventory_agent"

workflow.add_conditional_edges("pharmacy_design_agent", route_after_pharmacy)

def route_after_inventory(state: AgentState):
    if not state.get("validation_passed") or not state.get("stock_sufficient"):
        return END
    return "prediction_agent"

workflow.add_conditional_edges("inventory_agent", route_after_inventory)

workflow.add_edge("prediction_agent", "action_agent")
workflow.add_edge("action_agent", END)

# Compile graph
app_graph = workflow.compile()
