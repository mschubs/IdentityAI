"""
Agents package initialization.
This module exposes the various agent classes used in the identity verification system.
"""

from .document_agent import DocumentParsingAgent
from .face_verification_agent import FaceVerificationAgent
from .osint_agent import OSINTAgent
from .decision_agent import DecisionAgent
from .reverse_image_agent import ReverseImageAgent
from .orchestrator import OrchestratorAgent, OrchestratorStatus
from .document_agent_helpers.face_detection import detect_primary_faces
__all__ = [
    'DocumentParsingAgent',
    'FaceVerificationAgent',
    'OSINTAgent',
    'DecisionAgent',
    'ReverseImageAgent',
    'OrchestratorAgent',
    'OrchestratorStatus',
    'detect_primary_faces'
]

__version__ = '0.1.0'
