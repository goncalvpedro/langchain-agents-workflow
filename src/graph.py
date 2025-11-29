"""
LangGraph Construction - The Genesis Pipeline Workflow
Orchestrates the 5 agents with parallel execution and synchronization
"""

from langgraph.graph import StateGraph, END
from src.state import GenesisState
from src.nodes import (
    agent_product_owner,
    agent_creative_director,
    agent_solutions_architect,
    agent_lead_developer,
    agent_growth_hacker
)
from src.logger_config import logger


def create_genesis_graph():
    """
    Constructs the LangGraph workflow for the Genesis Pipeline.
    
    Graph Structure:
    START -> Product Owner -> [Creative Director || Solutions Architect] 
    -> Lead Developer -> Growth Hacker -> END
    
    Returns:
        Compiled StateGraph ready for execution
    """
    
    # Initialize the graph
    workflow = StateGraph(GenesisState)
    
    # Add nodes (agents)
    workflow.add_node("product_owner", agent_product_owner)
    workflow.add_node("creative_director", agent_creative_director)
    workflow.add_node("solutions_architect", agent_solutions_architect)
    workflow.add_node("lead_developer", agent_lead_developer)
    workflow.add_node("growth_hacker", agent_growth_hacker)
    
    # Define edges (workflow)
    
    # Entry point: Start with Product Owner
    workflow.set_entry_point("product_owner")
    
    # After PRD, branch to parallel agents
    workflow.add_edge("product_owner", "creative_director")
    workflow.add_edge("product_owner", "solutions_architect")
    
    # Both parallel agents feed into Lead Developer
    # LangGraph automatically waits for both to complete
    workflow.add_edge("creative_director", "lead_developer")
    workflow.add_edge("solutions_architect", "lead_developer")
    
    # Lead Developer feeds into Growth Hacker
    workflow.add_edge("lead_developer", "growth_hacker")
    
    # Growth Hacker is the terminal node
    workflow.add_edge("growth_hacker", END)
    
    # Compile the graph
    app = workflow.compile()
    
    logger.info("Genesis Pipeline graph compiled successfully")
    
    return app


# Export the compiled graph
genesis_pipeline = create_genesis_graph()