"""Main LangGraph workflow for audio transcription."""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from .state import TranscriptionState
from .nodes.audio_processor import process_audio_chunks, cleanup_temp_files
from .nodes.transcriber import transcribe_chunks
from .nodes.formatter import format_output
from config import AudioTranscriptionConfig


def should_retry(state: TranscriptionState) -> str:
    """
    Determine if we should retry after an error.
    
    Args:
        state: Current workflow state
        
    Returns:
        Next node name or END
    """
    if state.get('error') and state.get('retry_count', 0) < state.get('max_retries', 3):
        print(f"Retrying... (attempt {state['retry_count']}/{state['max_retries']})")
        state['retry_count'] = state.get('retry_count', 0) + 1
        state['error'] = None
        return "transcribe"
    elif state.get('error'):
        print(f"Max retries reached. Error: {state['error']}")
        return END
    else:
        return "format"


def create_workflow() -> StateGraph:
    """
    Create the audio transcription workflow.
    
    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(TranscriptionState)
    
    # Add nodes
    workflow.add_node("process_audio", process_audio_chunks)
    workflow.add_node("transcribe", transcribe_chunks)
    workflow.add_node("format", format_output)
    
    # Define edges
    workflow.add_edge(START, "process_audio")
    workflow.add_edge("process_audio", "transcribe")
    
    # Conditional edge for error handling
    workflow.add_conditional_edges(
        "transcribe",
        should_retry,
        {
            "transcribe": "transcribe",
            "format": "format",
            END: END
        }
    )
    
    workflow.add_edge("format", END)
    
    return workflow.compile()


async def process_audio(
    audio_path: str,
    output_path: str = None,
    transcription_mode: str = None,
    chunk_minutes: int = None,
    max_workers: int = None
) -> Dict[str, Any]:
    """
    Process an audio file through the transcription workflow.
    
    Args:
        audio_path: Path to the audio file
        output_path: Optional output path for JSON (defaults to {audio_name}.json)
        transcription_mode: Transcription mode (defaults to config default)
        chunk_minutes: Chunk duration in minutes (defaults to config)
        max_workers: Number of parallel workers (defaults to config)
        
    Returns:
        Result dictionary with transcript and metadata
    """
    # Validate configuration
    AudioTranscriptionConfig.validate()
    
    # Set defaults
    if transcription_mode is None:
        transcription_mode = AudioTranscriptionConfig.DEFAULT_MODE
    
    if chunk_minutes is None:
        chunk_minutes = AudioTranscriptionConfig.CHUNK_MINUTES
    
    if max_workers is None:
        max_workers = AudioTranscriptionConfig.MAX_WORKERS
    
    # Generate session ID
    session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    temp_dir = AudioTranscriptionConfig.get_temp_dir(session_id)
    
    # Determine output path
    if output_path is None:
        audio_name = os.path.splitext(os.path.basename(audio_path))[0]
        audio_dir = os.path.dirname(os.path.abspath(audio_path))
        output_path = os.path.join(audio_dir, f"{audio_name}.json")
    
    # Create initial state
    initial_state = {
        'audio_path': audio_path,
        'output_path': output_path,
        'transcription_mode': transcription_mode,
        'chunk_duration_minutes': chunk_minutes,
        'max_workers': max_workers,
        'session_id': session_id,
        'temp_dir': temp_dir,
        'retry_count': 0,
        'max_retries': AudioTranscriptionConfig.MAX_RETRIES
    }
    
    print(f"\n{'='*60}")
    print(f"Audio Transcription")
    print(f"{'='*60}")
    print(f"Input: {audio_path}")
    print(f"Output: {output_path}")
    print(f"Mode: {transcription_mode}")
    print(f"Chunk size: {chunk_minutes} minutes")
    print(f"Workers: {max_workers}")
    print(f"{'='*60}\n")
    
    # Create and run workflow
    app = create_workflow()
    
    try:
        # Run the workflow
        result = await app.ainvoke(initial_state)
        
        if result.get('error'):
            print(f"\n❌ Transcription failed: {result['error']}")
            return {
                'success': False,
                'error': result['error'],
                'output_path': output_path
            }
        
        # Save output
        output_data = {
            'source_file': audio_path,
            'duration_seconds': result['audio_duration'],
            'transcription_mode': transcription_mode,
            'created_at': datetime.now().isoformat(),
            'transcript': result['final_transcript'],
            'metadata': result['metadata']
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Transcription complete!")
        print(f"📁 Output: {output_path}")
        print(f"⏱️  Duration: {result['audio_duration']:.1f}s ({result['audio_duration']/60:.1f} min)")
        print(f"💰 Estimated cost: ${result['metadata']['estimated_cost_usd']:.2f}")
        
        return {
            'success': True,
            'output_path': output_path,
            'transcript': result['final_transcript'],
            'metadata': result['metadata']
        }
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'output_path': output_path
        }
    
    finally:
        # Clean up temp files
        cleanup_temp_files(initial_state)
