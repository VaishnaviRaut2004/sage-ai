import os
from typing import TypedDict, Annotated, List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from langchain_openai import ChatOpenAI
from backend.agents.pharmacist_tools import (
    get_low_stock_report,
    get_refill_alerts,
    restock_medicine,
    get_order_history
)

# 1. State Definition
class PharmacistState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# 2. Tool Array
pharmacist_tools = [
    get_low_stock_report, 
    get_refill_alerts, 
    restock_medicine, 
    get_order_history
]

# 3. Model Logic
def call_pharmacist_model(state: PharmacistState):
    messages = state["messages"]
    
    system_prompt = """You are an Agentic Pharmacy Operations Assistant for licensed pharmacists.
Your role is to help summarize inventory, process patient refill alerts, autonomously restock medications, and review active order histories based on the pharmacist's natural language instructions.

CAPABILITIES:
1. `get_low_stock_report`: Check inventory for items below a certain stock threshold.
2. `get_refill_alerts`: Check for upcoming or overdue refill predictions for patients.
3. `restock_medicine`: Add stock to a specific medicine. Always confirm the actual medicine name and quantity being restocked the user wants. If ambiguous, ask clarifying questions before restocking.
4. `get_order_history`: Look at recent patient orders optionally filtering by their name/ID.

RULES:
- When presenting data, use clear and easily readable styling (bullet points, summaries).
- Do not make up patient names or inventory details; always query the database using your tools.
- Provide actionable recommendations when surfacing reports (e.g., if you show low stock, ask if they want you to easily restock them).
- Be professional, concise, and helpful. Always adopt the persona of an expert AI assistant to a pharmacist.
"""

    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "openai/gpt-4o-mini"),
        temperature=0,
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )
    
    # Bind tools to let LLM decide when to call them
    model_with_tools = llm.bind_tools(pharmacist_tools)
    
    sys_msg = SystemMessage(content=system_prompt)
    
    # Filter out SystemMessages from state just in case, to avoid duplication
    filtered_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    
    response = model_with_tools.invoke([sys_msg] + filtered_messages)
    return {"messages": [response]}

# 4. Graph Architecture
workflow = StateGraph(PharmacistState)

# Nodes
workflow.add_node("agent", call_pharmacist_model)
workflow.add_node("tools", ToolNode(pharmacist_tools))

# Edges
workflow.add_edge(START, "agent")

# Condition: After agent speaks, does it want to call a tool or end this turn?
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

# Memory
pharmacist_memory = MemorySaver()

# Final Graph Compilation
pharmacist_supervisor = workflow.compile(checkpointer=pharmacist_memory)
