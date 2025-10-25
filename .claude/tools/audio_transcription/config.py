"""Configuration settings for audio transcription."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AudioTranscriptionConfig:
    """Configuration for audio transcription."""
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_DEFAULT")
    
    # Default transcription mode
    DEFAULT_MODE = os.getenv("AUDIO_TRANSCRIPTION_MODE", "sliding_window")
    
    # Supported audio formats
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac']
    
    # Transcription modes
    MODES = {
        "no_timestamps": {
            "model": "gpt-4o-transcribe",
            "description": "High accuracy, no timestamps",
            "speed": "fast",
            "cost": "low"
        },
        "whisper_only": {
            "model": "whisper-1",
            "description": "Word-level timestamps",
            "speed": "fast",
            "cost": "low"
        },
        "hybrid": {
            "models": ["gpt-4o-transcribe", "whisper-1"],
            "description": "Best accuracy + sentence timestamps",
            "speed": "medium",
            "cost": "high"
        },
        "sliding_window": {
            "models": ["whisper-1", "gpt-4o-transcribe"],
            "description": "Perfect boundaries + timestamps (default)",
            "speed": "medium",
            "cost": "high"
        }
    }
    
    # Model configurations
    GPT_TRANSCRIBE_MODEL = "gpt-4o-transcribe"
    WHISPER_MODEL = "whisper-1"
    GPT_LLM_MODEL = "gpt-4o"
    
    # Audio processing settings
    AUDIO_FORMAT = "wav"
    AUDIO_CODEC = "pcm_s16le"
    SAMPLE_RATE = 16000  # Whisper-optimized
    CHUNK_MINUTES = int(os.getenv("AUDIO_CHUNK_MINUTES", "2"))
    MAX_WORKERS = int(os.getenv("AUDIO_MAX_WORKERS", "10"))
    
    # Sliding window settings
    SLIDING_WINDOW_EXTEND = 5  # Seconds to extend on each side
    SLIDING_WINDOW_CONTEXT_WORDS = 100  # Words from Whisper to include
    
    # LLM processing settings
    LLM_CHUNK_WORDS = 1000
    LLM_TEMPERATURE = 0.1
    
    # Whisper settings
    WHISPER_RESPONSE_FORMAT = "verbose_json"  # Required for timestamps
    
    # Output settings
    SAVE_INTERMEDIATE_OUTPUTS = os.getenv("SAVE_INTERMEDIATE_OUTPUTS", "false").lower() == "true"
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    # File paths
    TEMP_DIR = "temp/audio_transcription"
    
    @classmethod
    def get_temp_dir(cls, session_id: str) -> str:
        """Get the directory for a transcription session."""
        return os.path.join(cls.TEMP_DIR, f"session_{session_id}")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY_DEFAULT environment variable is required")
        
        if cls.DEFAULT_MODE not in cls.MODES:
            raise ValueError(f"Invalid AUDIO_TRANSCRIPTION_MODE: {cls.DEFAULT_MODE}")
        
        return True
