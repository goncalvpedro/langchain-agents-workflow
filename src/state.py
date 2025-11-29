"""
State Definition for Genesis Pipeline
Manages the shared state between all AI agents
"""

from typing import TypedDict, Annotated, Sequence, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class GenesisState(TypedDict):
    """
    Central state object that flows through the entire pipeline.
    Each agent reads from and writes to specific keys.
    """
    # Input
    user_idea: str
    
    # Agent Outputs
    prd_content: str  # Agent 1: Product Owner
    brand_assets: Dict[str, Any]  # Agent 2: Creative Director
    architecture_map: Dict[str, Any]  # Agent 3: Solutions Architect
    source_code: Dict[str, str]  # Agent 4: Lead Developer (filename -> code)
    marketing_plan: str  # Agent 5: Growth Hacker
    
    # Conversation History
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Metadata
    execution_metadata: Dict[str, Any]  # Tracks timing, tokens, errors


def create_initial_state(user_idea: str) -> GenesisState:
    """
    Factory function to create a clean initial state.
    
    Args:
        user_idea: The raw user input describing their project
        
    Returns:
        GenesisState with initialized values
    """
    return GenesisState(
        user_idea=user_idea,
        prd_content="",
        brand_assets={},
        architecture_map={},
        source_code={},
        marketing_plan="",
        messages=[],
        execution_metadata={
            "start_time": None,
            "end_time": None,
            "total_tokens": 0,
            "agent_timings": {}
        }
    )