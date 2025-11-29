"""
Genesis Pipeline - Entry Point
Demonstrates the complete workflow with a test query
"""

import asyncio
import os
import json
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from src.state import create_initial_state
from src.graph import genesis_pipeline
from src.logger_config import logger
from src.database import (
    init_database,
    create_project,
    update_project_status,
    save_project_artifacts,
    get_project,
    ProjectStatus
)

# Load environment variables
load_dotenv()

# Initialize database on import
init_database()


async def run_genesis_pipeline(user_idea: str, project_id: Optional[int] = None):
    """
    Execute the Genesis Pipeline with a user idea
    
    Args:
        user_idea: Raw user input describing their project
        project_id: Optional existing project ID (if None, creates new project)
        
    Returns:
        Tuple of (final_state, project_id)
    """
    from src.database import get_db
    
    db = get_db()
    project = None
    
    try:
        # Create or get project record
        if project_id is None:
            project = create_project(user_idea, db)
            project_id = project.id
            logger.info(f"Created new project with ID: {project_id}")
        else:
            project = get_project(project_id, db)
            if not project:
                raise ValueError(f"Project with ID {project_id} not found")
            # Update existing project
            project.user_idea = user_idea
            project.status = ProjectStatus.PENDING
            db.commit()
            logger.info(f"Using existing project ID: {project_id}")
        
        logger.info("=" * 80)
        logger.info("GENESIS PIPELINE INITIATED")
        logger.info("=" * 80)
        logger.info(f"User Idea: {user_idea}")
        logger.info(f"Project ID: {project_id}")
        
        # Update status to running
        update_project_status(project_id, ProjectStatus.RUNNING, db)
        
        # Create initial state
        initial_state = create_initial_state(user_idea)
        initial_state["execution_metadata"]["start_time"] = datetime.utcnow().isoformat()
        initial_state["execution_metadata"]["project_id"] = project_id
        
        # Execute the pipeline
        logger.info("Starting agent orchestration...")
        final_state = await genesis_pipeline.ainvoke(initial_state)
        
        final_state["execution_metadata"]["end_time"] = datetime.utcnow().isoformat()
        
        # Save outputs to files
        output_dir = f"output/project_{project_id}"
        artifacts_dict = save_output(final_state, output_dir)
        
        # Save artifact paths to database
        save_project_artifacts(project_id, artifacts_dict, output_dir, db)
        
        # Update project status to completed
        update_project_status(project_id, ProjectStatus.COMPLETED, db)
        
        logger.info("=" * 80)
        logger.info("GENESIS PIPELINE COMPLETED")
        logger.info("=" * 80)
        
        # Log summary
        logger.info("Pipeline Summary:", extra={
            'agent': 'pipeline_summary',
            'status': 'complete',
            'files_generated': len(final_state.get('source_code', {})),
            'execution_time': 'calculated',
            'project_id': project_id
        })
        
        return final_state, project_id
        
    except Exception as e:
        # Update project status to failed
        if project_id:
            try:
                update_project_status(project_id, ProjectStatus.FAILED, db)
            except:
                pass  # Don't fail if status update fails
        
        logger.error(f"Pipeline failed: {str(e)}", extra={
            'agent': 'pipeline',
            'status': 'error',
            'project_id': project_id
        })
        raise
    finally:
        db.close()


def save_output(final_state: dict, output_dir: str = "output") -> dict:
    """
    Save all pipeline outputs to files
    
    Args:
        final_state: The completed state from the pipeline
        output_dir: Directory to save outputs
        
    Returns:
        Dictionary mapping artifact types to file paths
    """
    os.makedirs(output_dir, exist_ok=True)
    
    artifacts = {}
    
    # Save PRD
    prd_path = f"{output_dir}/PRD.md"
    with open(prd_path, "w", encoding="utf-8") as f:
        f.write(final_state["prd_content"])
    artifacts["prd"] = prd_path
    
    # Save brand assets
    brand_path = f"{output_dir}/brand_guide.json"
    with open(brand_path, "w", encoding="utf-8") as f:
        json.dump(final_state["brand_assets"], f, indent=2)
    artifacts["brand_assets"] = brand_path
    
    # Save architecture
    arch_path = f"{output_dir}/architecture.json"
    with open(arch_path, "w", encoding="utf-8") as f:
        json.dump(final_state["architecture_map"], f, indent=2)
    artifacts["architecture"] = arch_path
    
    # Save source code files
    code_dir = f"{output_dir}/source_code"
    os.makedirs(code_dir, exist_ok=True)
    for filename, code in final_state["source_code"].items():
        # Create subdirectories if needed
        filepath = os.path.join(code_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)
    artifacts["source_code"] = code_dir
    
    # Save marketing plan
    marketing_path = f"{output_dir}/marketing_plan.md"
    with open(marketing_path, "w", encoding="utf-8") as f:
        f.write(final_state["marketing_plan"])
    artifacts["marketing_plan"] = marketing_path
    
    # Save install guide if it exists
    if "install_guide" in final_state:
        install_path = f"{output_dir}/INSTALL_GUIDE.md"
        with open(install_path, "w", encoding="utf-8") as f:
            f.write(final_state["install_guide"])
        artifacts["install_guide"] = install_path
    
    logger.info(f"All outputs saved to {output_dir}/")
    return artifacts


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
    final_state, project_id = await run_genesis_pipeline(user_idea)
    
    logger.info(f"Project saved with ID: {project_id}")
    
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