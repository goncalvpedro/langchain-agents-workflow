"""
Streamlit Frontend for Genesis Pipeline
Web-based interface for running and monitoring pipeline executions
"""

import streamlit as st
import asyncio
import os
import json
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from src.database import (
    init_database,
    get_all_projects,
    get_project,
    ProjectStatus
)
from main import run_genesis_pipeline
from src.logger_config import logger

# Load environment variables
load_dotenv()

# Initialize database
init_database()

# Page configuration
st.set_page_config(
    page_title="Genesis Pipeline",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        font-weight: bold;
        display: inline-block;
    }
    .status-pending { background-color: #ffc107; color: #000; }
    .status-running { background-color: #17a2b8; color: #fff; }
    .status-completed { background-color: #28a745; color: #fff; }
    .status-failed { background-color: #dc3545; color: #fff; }
    .project-card {
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)


def get_status_badge(status: ProjectStatus) -> str:
    """Get HTML badge for project status"""
    status_class = f"status-{status.value}"
    return f'<span class="status-badge {status_class}">{status.value.upper()}</span>'


def format_timestamp(timestamp: datetime) -> str:
    """Format datetime for display"""
    if timestamp:
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return "N/A"


@st.cache_data(ttl=5)
def load_projects(limit: int = 50):
    """Load projects from database (cached for 5 seconds)"""
    try:
        return get_all_projects(limit=limit)
    except Exception as e:
        logger.error(f"Error loading projects: {str(e)}")
        return []


def display_project_history():
    """Display project history in sidebar"""
    st.sidebar.header("📚 Project History")
    
    projects = load_projects(limit=50)
    
    if not projects:
        st.sidebar.info("No projects yet. Launch your first pipeline!")
        return None
    
    # Filter options
    filter_status = st.sidebar.selectbox(
        "Filter by Status",
        ["All", "Completed", "Running", "Failed", "Pending"],
        key="status_filter"
    )
    
    # Filter projects
    if filter_status != "All":
        status_map = {
            "Completed": ProjectStatus.COMPLETED,
            "Running": ProjectStatus.RUNNING,
            "Failed": ProjectStatus.FAILED,
            "Pending": ProjectStatus.PENDING
        }
        projects = [p for p in projects if p.status == status_map[filter_status]]
    
    # Display projects
    selected_project_id = None
    for project in projects:
        with st.sidebar.expander(f"Project #{project.id} - {get_status_badge(project.status)}", expanded=False):
            st.write(f"**Created:** {format_timestamp(project.created_at)}")
            st.write(f"**Status:** {project.status.value}")
            st.write(f"**Idea:** {project.user_idea[:100]}...")
            
            if st.button(f"View Details", key=f"view_{project.id}"):
                selected_project_id = project.id
                st.session_state.selected_project_id = project.id
    
    return selected_project_id


def display_project_details(project_id: int):
    """Display detailed view of a project"""
    from src.database import get_db
    
    # Get project and artifacts within a session context
    db = get_db()
    try:
        project = get_project(project_id, db)
        
        if not project:
            st.error(f"Project {project_id} not found")
            return
        
        # Access artifacts while session is still open and extract data
        artifacts_list = []
        if project.artifacts:
            for artifact in project.artifacts:
                # Extract all data we need from artifacts before closing session
                artifacts_list.append({
                    'artifact_type': artifact.artifact_type,
                    'file_path': artifact.file_path,
                    'created_at': artifact.created_at
                })
        
        # Store project data we need (since we'll close the session)
        project_data = {
            'id': project.id,
            'status': project.status,
            'created_at': project.created_at,
            'updated_at': project.updated_at,
            'user_idea': project.user_idea
        }
    finally:
        db.close()
    
    # Now display using the stored data and artifacts
    st.header(f"Project #{project_data['id']}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", project_data['status'].value.upper())
    with col2:
        st.metric("Created", format_timestamp(project_data['created_at']))
    with col3:
        st.metric("Updated", format_timestamp(project_data['updated_at']))
    
    st.subheader("User Idea")
    st.write(project_data['user_idea'])
    
    # Display artifacts (already loaded as a list)
    
    if artifacts_list:
        st.subheader("Generated Artifacts")
        artifact_types = {}
        for artifact in artifacts_list:
            artifact_type = artifact['artifact_type']
            if artifact_type not in artifact_types:
                artifact_types[artifact_type] = []
            artifact_types[artifact_type].append(artifact)
        
        for artifact_type, artifacts in artifact_types.items():
            with st.expander(f"{artifact_type.replace('_', ' ').title()} ({len(artifacts)})"):
                for artifact in artifacts:
                    file_path = artifact['file_path']
                    st.write(f"📄 {file_path}")
                    if os.path.exists(file_path):
                        try:
                            if file_path.endswith('.md'):
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    st.markdown(f.read())
                            elif file_path.endswith('.json'):
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    st.json(json.load(f))
                        except Exception as e:
                            st.error(f"Error reading file: {str(e)}")
                    else:
                        st.warning(f"File not found: {file_path}")
    else:
        st.info("No artifacts generated yet. Artifacts will appear here once the pipeline completes.")


def run_pipeline_async(user_idea: str):
    """Run pipeline in async context"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        final_state, project_id = loop.run_until_complete(run_genesis_pipeline(user_idea))
        loop.close()
        return project_id, None
    except Exception as e:
        return None, str(e)


def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🚀 Genesis Pipeline</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar - Project History
    selected_project_id = display_project_history()
    
    # Main content area
    if 'selected_project_id' in st.session_state and st.session_state.selected_project_id:
        # Display selected project details
        display_project_details(st.session_state.selected_project_id)
    else:
        # New project form
        st.header("✨ Create New Project")
        
        user_idea = st.text_area(
            "Enter your project idea:",
            height=200,
            placeholder="Describe your project idea here...\n\nExample: I want to build a productivity app for remote teams that combines task management with virtual coworking spaces..."
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            launch_button = st.button("🚀 Launch Pipeline", type="primary", use_container_width=True)
        
        # Check if pipeline is already running
        if 'pipeline_running' in st.session_state and st.session_state.pipeline_running:
            st.warning("⚠️ Pipeline is currently running. Please wait...")
            st.info("Check the Project History sidebar to monitor progress.")
        
        # Launch pipeline
        if launch_button:
            if not user_idea or len(user_idea.strip()) < 10:
                st.error("Please enter a detailed project idea (at least 10 characters)")
            elif not os.getenv("OPENAI_API_KEY"):
                st.error("❌ OPENAI_API_KEY not found in environment variables. Please configure it in your .env file.")
            else:
                with st.spinner("🚀 Launching Genesis Pipeline..."):
                    st.session_state.pipeline_running = True
                    
                    # Run pipeline
                    project_id, error = run_pipeline_async(user_idea.strip())
                    
                    if error:
                        st.error(f"❌ Pipeline failed: {error}")
                        st.session_state.pipeline_running = False
                    elif project_id:
                        st.success(f"✅ Pipeline completed! Project ID: {project_id}")
                        st.session_state.pipeline_running = False
                        st.session_state.selected_project_id = project_id
                        st.rerun()
        
        # Instructions
        with st.expander("ℹ️ How it works"):
            st.markdown("""
            **Genesis Pipeline** uses AI agents to transform your idea into a complete project:
            
            1. **Product Owner** - Creates a comprehensive PRD
            2. **Creative Director** - Designs brand identity
            3. **Solutions Architect** - Designs technical architecture
            4. **Lead Developer** - Generates source code
            5. **Growth Hacker** - Creates marketing strategy
            6. **Onboarding Specialist** - Generates installation guide
            
            The pipeline typically takes 2-5 minutes to complete.
            """)
        
        # Status display for running pipelines
        if 'pipeline_running' in st.session_state and st.session_state.pipeline_running:
            st.info("💡 Tip: Check the Project History sidebar to see your project's progress in real-time!")
    
    # Auto-refresh for running projects
    if 'pipeline_running' in st.session_state and st.session_state.pipeline_running:
        st.rerun()


if __name__ == "__main__":
    main()

