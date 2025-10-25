"""Audio processing node - handles audio format conversion and chunking."""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
from pydub import AudioSegment
from config import AudioTranscriptionConfig


def process_audio_chunks(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process audio file: validate format, convert to WAV, and chunk.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with audio chunks
    """
    audio_path = state['audio_path']
    session_id = state['session_id']
    temp_dir = state['temp_dir']
    chunk_duration_minutes = state['chunk_duration_minutes']
    
    try:
        # Validate audio file exists
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Validate file extension
        file_ext = Path(audio_path).suffix.lower()
        if file_ext not in AudioTranscriptionConfig.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported audio format: {file_ext}. "
                f"Supported formats: {', '.join(AudioTranscriptionConfig.SUPPORTED_FORMATS)}"
            )
        
        print(f"Loading audio file: {audio_path}")
        
        # Load audio file (pydub handles format conversion automatically)
        audio = AudioSegment.from_file(audio_path)
        
        # Get duration
        duration_seconds = len(audio) / 1000.0
        state['audio_duration'] = duration_seconds
        
        print(f"Audio duration: {duration_seconds:.2f} seconds ({duration_seconds/60:.2f} minutes)")
        
        # Create temp directories
        os.makedirs(temp_dir, exist_ok=True)
        chunks_dir = os.path.join(temp_dir, "chunks")
        os.makedirs(chunks_dir, exist_ok=True)
        
        # Convert to WAV if needed
        converted_path = os.path.join(temp_dir, "converted_audio.wav")
        audio.export(
            converted_path,
            format=AudioTranscriptionConfig.AUDIO_FORMAT,
            parameters=[
                "-ac", "1",  # Mono
                "-ar", str(AudioTranscriptionConfig.SAMPLE_RATE),  # Sample rate
                "-acodec", AudioTranscriptionConfig.AUDIO_CODEC  # Codec
            ]
        )
        
        print(f"Converted audio to WAV: {converted_path}")
        
        # Reload the converted audio
        audio = AudioSegment.from_wav(converted_path)
        
        # Calculate chunk size
        chunk_duration_ms = chunk_duration_minutes * 60 * 1000
        
        # Create chunks
        chunks = []
        chunk_num = 1
        
        for start_ms in range(0, len(audio), chunk_duration_ms):
            end_ms = min(start_ms + chunk_duration_ms, len(audio))
            chunk = audio[start_ms:end_ms]
            
            # Save chunk
            chunk_path = os.path.join(chunks_dir, f"chunk_{chunk_num:04d}.wav")
            chunk.export(chunk_path, format="wav")
            
            chunks.append({
                'chunk_num': chunk_num,
                'path': chunk_path,
                'start_time': start_ms / 1000.0,
                'end_time': end_ms / 1000.0,
                'duration': (end_ms - start_ms) / 1000.0
            })
            
            chunk_num += 1
        
        print(f"Created {len(chunks)} audio chunks")
        
        state['audio_chunks'] = chunks
        state['error'] = None
        
        return state
        
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        state['error'] = str(e)
        return state


def cleanup_temp_files(state: Dict[str, Any]) -> None:
    """
    Clean up temporary files after processing.
    
    Args:
        state: Current workflow state
    """
    temp_dir = state.get('temp_dir')
    
    if temp_dir and os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary files: {temp_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up temp files: {e}")
