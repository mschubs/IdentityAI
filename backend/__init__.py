"""
Backend package initialization.
This module serves as the entry point for the backend package and exposes core functionality.
"""

from .server import app
from .similarity import compare_faces, compare_face_encodings
from .main import run_groq_agent

# Import all agents through the agents package
from .agents import (
    DocumentParsingAgent,
    FaceVerificationAgent,
    OSINTAgent,
    DecisionAgent,
    ReverseImageAgent,
    OrchestratorAgent,
    OrchestratorStatus
)

__all__ = [
    # Main FastAPI application
    'app',
    
    # Core functionality
    'compare_faces',
    'compare_face_encodings',
    'run_groq_agent',
    
    # Agents
    'DocumentParsingAgent',
    'FaceVerificationAgent',
    'OSINTAgent',
    'DecisionAgent',
    'ReverseImageAgent',
    'OrchestratorAgent',
    'OrchestratorStatus'
]

__version__ = '0.1.0'
