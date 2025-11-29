"""
Database Models and Utilities for Genesis Pipeline
Handles persistence of projects and artifacts
"""

import os
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship, joinedload, selectinload
from enum import Enum

Base = declarative_base()


class ProjectStatus(str, Enum):
    """Project execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(Base):
    """Project model - stores user ideas and pipeline execution status"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_idea = Column(Text, nullable=False)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to artifacts
    artifacts = relationship("Artifact", back_populates="project", cascade="all, delete-orphan")


class Artifact(Base):
    """Artifact model - stores file paths to generated outputs"""
    __tablename__ = "artifacts"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    artifact_type = Column(String(50), nullable=False)  # 'prd', 'brand_assets', 'architecture', 'source_code', 'marketing_plan', 'install_guide'
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to project
    project = relationship("Project", back_populates="artifacts")


# Database connection management
_engine = None
_SessionLocal = None


def get_database_url() -> str:
    """
    Get database URL from environment variable or use default
    
    Returns:
        Database connection string
    """
    return os.getenv(
        "DATABASE_URL",
        "postgresql://genesis_user:genesis2024@localhost:5432/genesis_pipeline"
    )


def init_database():
    """
    Initialize database connection and create tables
    """
    global _engine, _SessionLocal
    
    database_url = get_database_url()
    _engine = create_engine(database_url, pool_pre_ping=True)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    
    # Create all tables
    Base.metadata.create_all(bind=_engine)


def get_db() -> Session:
    """
    Get database session (dependency injection pattern)
    
    Returns:
        Database session
    """
    if _SessionLocal is None:
        init_database()
    
    db = _SessionLocal()
    try:
        return db
    finally:
        pass  # Session will be closed by caller


def create_project(user_idea: str, db: Optional[Session] = None) -> Project:
    """
    Create a new project record
    
    Args:
        user_idea: The user's project idea
        db: Optional database session (creates new if not provided)
        
    Returns:
        Created Project instance
    """
    should_close = False
    if db is None:
        db = get_db()
        should_close = True
    
    try:
        project = Project(
            user_idea=user_idea,
            status=ProjectStatus.PENDING
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    finally:
        if should_close:
            db.close()


def update_project_status(
    project_id: int,
    status: ProjectStatus,
    db: Optional[Session] = None
) -> Project:
    """
    Update project status
    
    Args:
        project_id: Project ID
        status: New status
        db: Optional database session
        
    Returns:
        Updated Project instance
    """
    should_close = False
    if db is None:
        db = get_db()
        should_close = True
    
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project with id {project_id} not found")
        
        project.status = status
        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)
        return project
    finally:
        if should_close:
            db.close()


def add_artifact(
    project_id: int,
    artifact_type: str,
    file_path: str,
    db: Optional[Session] = None
) -> Artifact:
    """
    Add an artifact (file path) to a project
    
    Args:
        project_id: Project ID
        artifact_type: Type of artifact ('prd', 'brand_assets', etc.)
        file_path: Path to the artifact file
        db: Optional database session
        
    Returns:
        Created Artifact instance
    """
    should_close = False
    if db is None:
        db = get_db()
        should_close = True
    
    try:
        artifact = Artifact(
            project_id=project_id,
            artifact_type=artifact_type,
            file_path=file_path
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return artifact
    finally:
        if should_close:
            db.close()


def get_project(project_id: int, db: Optional[Session] = None) -> Optional[Project]:
    """
    Get a project by ID with its artifacts (eagerly loaded)
    
    Args:
        project_id: Project ID
        db: Optional database session
        
    Returns:
        Project instance or None if not found
    """
    should_close = False
    if db is None:
        db = get_db()
        should_close = True
    
    try:
        # Use selectinload for one-to-many relationships (more reliable than joinedload)
        project = db.query(Project).options(selectinload(Project.artifacts)).filter(Project.id == project_id).first()
        
        if project:
            # Force materialization of artifacts while session is still open
            # Access all attributes we'll need later
            artifacts = list(project.artifacts)
            # Access basic project attributes to ensure they're loaded
            _ = project.id, project.user_idea, project.status, project.created_at, project.updated_at
        
        return project
    finally:
        if should_close:
            db.close()


def get_all_projects(db: Optional[Session] = None, limit: int = 100) -> List[Project]:
    """
    Get all projects ordered by creation date (newest first)
    Artifacts are eagerly loaded to avoid DetachedInstanceError
    
    Args:
        db: Optional database session
        limit: Maximum number of projects to return
        
    Returns:
        List of Project instances
    """
    should_close = False
    if db is None:
        db = get_db()
        should_close = True
    
    try:
        # Eagerly load artifacts using selectinload
        projects = db.query(Project).options(selectinload(Project.artifacts)).order_by(Project.created_at.desc()).limit(limit).all()
        
        # Force materialization of artifacts for each project while session is open
        for project in projects:
            _ = list(project.artifacts)
        
        return projects
    finally:
        if should_close:
            db.close()


def save_project_artifacts(
    project_id: int,
    artifacts: Dict[str, str],
    output_dir: str = "output",
    db: Optional[Session] = None
) -> List[Artifact]:
    """
    Save all artifacts from a completed pipeline run
    
    Args:
        project_id: Project ID
        artifacts: Dictionary mapping artifact types to file paths (can be absolute or relative)
        output_dir: Base output directory (used for reference, paths in artifacts should already be correct)
        db: Optional database session
        
    Returns:
        List of created Artifact instances
    """
    created_artifacts = []
    should_close = False
    if db is None:
        db = get_db()
        should_close = True
    
    try:
        for artifact_type, file_path in artifacts.items():
            # Store the path as-is (already includes output_dir from save_output)
            # Convert to absolute path for consistency
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)
            
            artifact = add_artifact(project_id, artifact_type, file_path, db)
            created_artifacts.append(artifact)
        
        return created_artifacts
    finally:
        if should_close:
            db.close()

