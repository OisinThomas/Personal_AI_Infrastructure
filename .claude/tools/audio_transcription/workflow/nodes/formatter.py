"""Output formatting node - creates final JSON output."""

import json
from typing import Dict, Any
from datetime import datetime


def format_output(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format transcription results into final JSON output.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with formatted output
    """
    try:
        transcriptions = state['chunk_transcriptions']
        
        # Combine all chunk transcriptions
        full_transcript = "\n\n".join([
            chunk['text'] for chunk in transcriptions
        ])
        
        # Calculate metadata
        mode = state['transcription_mode']
        duration = state['audio_duration']
        num_chunks = len(transcriptions)
        
        # Estimate cost (rough approximation)
        cost_per_minute = {
            'no_timestamps': 0.006,  # gpt-4o-transcribe only
            'whisper_only': 0.006,   # whisper-1 only
            'hybrid': 0.012,         # both models
            'sliding_window': 0.012  # both models
        }
        
        estimated_cost = (duration / 60) * cost_per_minute.get(mode, 0.006)
        
        # Build metadata
        metadata = {
            'transcription_mode': mode,
            'models_used': _get_models_used(mode),
            'chunks_processed': num_chunks,
            'duration_seconds': duration,
            'estimated_cost_usd': round(estimated_cost, 2)
        }
        
        state['final_transcript'] = full_transcript
        state['metadata'] = metadata
        state['error'] = None
        
        return state
        
    except Exception as e:
        print(f"Error formatting output: {str(e)}")
        state['error'] = str(e)
        return state


def _get_models_used(mode: str) -> list:
    """Get list of models used for a given mode."""
    models = {
        'no_timestamps': ['gpt-4o-transcribe'],
        'whisper_only': ['whisper-1'],
        'hybrid': ['gpt-4o-transcribe', 'whisper-1'],
        'sliding_window': ['whisper-1', 'gpt-4o-transcribe']
    }
    return models.get(mode, [])
