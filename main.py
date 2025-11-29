"""
Genesis Pipeline - Entry Point
Demonstrates the complete workflow with a test query
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from src.state import create_initial_state
from src.graph import genesis_pipeline
from src.logger_config import logger

# Load environment variables
load_dotenv()


async def run_genesis_pipeline(user_idea: str):
    """
    Execute the Genesis Pipeline with a user idea
    
    Args:
        user_idea: Raw user input describing their project
        
    Returns:
        Final state with all agent outputs
    """
    logger.info("=" * 80)
    logger.info("GENESIS PIPELINE INITIATED")
    logger.info("=" * 80)
    logger.info(f"User Idea: {user_idea}")
    
    # Create initial state
    initial_state = create_initial_state(user_idea)
    initial_state["execution_metadata"]["start_time"] = datetime.utcnow().isoformat()
    
    try:
        # Execute the pipeline
        logger.info("Starting agent orchestration...")
        final_state = await genesis_pipeline.ainvoke(initial_state)
        
        final_state["execution_metadata"]["end_time"] = datetime.utcnow().isoformat()
        
        logger.info("=" * 80)
        logger.info("GENESIS PIPELINE COMPLETED")
        logger.info("=" * 80)
        
        # Log summary
        logger.info("Pipeline Summary:", extra={
            'agent': 'pipeline_summary',
            'status': 'complete',
            'files_generated': len(final_state.get('source_code', {})),
            'execution_time': 'calculated'
        })
        
        return final_state
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", extra={
            'agent': 'pipeline',
            'status': 'error'
        })
        raise


def save_output(final_state: dict, output_dir: str = "output"):
    """
    Save all pipeline outputs to files
    
    Args:
        final_state: The completed state from the pipeline
        output_dir: Directory to save outputs
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Save PRD
    with open(f"{output_dir}/PRD.md", "w") as f:
        f.write(final_state["prd_content"])
    
    # Save brand assets
    with open(f"{output_dir}/brand_guide.json", "w") as f:
        json.dump(final_state["brand_assets"], f, indent=2)
    
    # Save architecture
    with open(f"{output_dir}/architecture.json", "w") as f:
        json.dump(final_state["architecture_map"], f, indent=2)
    
    # Save source code files
    code_dir = f"{output_dir}/source_code"
    os.makedirs(code_dir, exist_ok=True)
    for filename, code in final_state["source_code"].items():
        # Create subdirectories if needed
        filepath = f"{code_dir}/{filename}"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(code)
    
    # Save marketing plan
    with open(f"{output_dir}/marketing_plan.md", "w") as f:
        f.write(final_state["marketing_plan"])
    
    logger.info(f"All outputs saved to {output_dir}/")


async def main():
    """
    Main execution function with test query
    """
    
    # Verify OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # Test user idea
    user_idea = """
    I want to build a productivity app for remote teams that combines 
    task management with virtual coworking spaces. Users can create 
    "focus rooms" where team members can work together in real-time, 
    see each other's progress, and use Pomodoro timers. The app should 
    have gamification elements and integrate with Slack and Google Calendar.
    """
    
    # Run the pipeline
    final_state = await run_genesis_pipeline(user_idea)
    
    # Save outputs
    save_output(final_state)
    
    # Print summary
    print("\n" + "=" * 80)
    print("GENESIS PIPELINE COMPLETE")
    print("=" * 80)
    print(f"\n✅ PRD Generated: {len(final_state['prd_content'])} characters")
    print(f"✅ Brand Assets: {len(final_state['brand_assets'])} elements")
    print(f"✅ Architecture: {len(final_state['architecture_map'])} components")
    print(f"✅ Source Files: {len(final_state['source_code'])} files")
    print(f"✅ Marketing Plan: {len(final_state['marketing_plan'])} characters")
    print(f"\n📁 All outputs saved to ./output/")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())