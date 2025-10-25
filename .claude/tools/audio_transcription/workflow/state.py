"""State definition for the audio transcription workflow."""

from typing import TypedDict, Optional, List, Dict, Any


class TranscriptionState(TypedDict, total=False):
    """State for the audio transcription workflow."""
    
    # Input
    audio_path: str
    output_path: Optional[str]
    transcription_mode: str
    
    # Processing settings
    chunk_duration_minutes: int
    max_workers: int
    
    # Session management
    session_id: str
    temp_dir: str
    
    # Audio processing
    audio_duration: float
    audio_chunks: List[Dict[str, Any]]
    
    # Transcription results
    chunk_transcriptions: List[Dict[str, Any]]
    final_transcript: str
    
    # Metadata
    metadata: Dict[str, Any]
    
    # Error handling
    error: Optional[str]
    retry_count: int
    max_retries: int
