"""Transcription node - handles all 4 transcription modes."""

import asyncio
import os
import json
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from tqdm import tqdm
from config import AudioTranscriptionConfig


def transcribe_chunks(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transcribe audio chunks using the specified mode.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with transcriptions
    """
    mode = state['transcription_mode']
    chunks = state['audio_chunks']
    max_workers = state['max_workers']
    
    print(f"\nTranscribing {len(chunks)} chunks using '{mode}' mode...")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=AudioTranscriptionConfig.OPENAI_API_KEY)
    
    try:
        if mode == "no_timestamps":
            transcriptions = _transcribe_no_timestamps(client, chunks, max_workers)
        elif mode == "whisper_only":
            transcriptions = _transcribe_whisper_only(client, chunks, max_workers)
        elif mode == "hybrid":
            transcriptions = _transcribe_hybrid(client, chunks, max_workers, state)
        elif mode == "sliding_window":
            transcriptions = _transcribe_sliding_window(client, chunks, max_workers, state)
        else:
            raise ValueError(f"Unknown transcription mode: {mode}")
        
        state['chunk_transcriptions'] = transcriptions
        state['error'] = None
        
        return state
        
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        state['error'] = str(e)
        return state


def _transcribe_no_timestamps(
    client: OpenAI,
    chunks: List[Dict[str, Any]],
    max_workers: int
) -> List[Dict[str, Any]]:
    """Transcribe using gpt-4o-transcribe only (no timestamps)."""
    
    def transcribe_chunk(chunk_info):
        chunk_num = chunk_info['chunk_num']
        chunk_path = chunk_info['path']
        
        with open(chunk_path, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model=AudioTranscriptionConfig.GPT_TRANSCRIBE_MODEL,
                file=audio_file,
                response_format="text"
            )
        
        return {
            'chunk_num': chunk_num,
            'text': response,
            'start_time': chunk_info['start_time'],
            'end_time': chunk_info['end_time']
        }
    
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(transcribe_chunk, chunk): chunk for chunk in chunks}
        
        with tqdm(total=len(chunks), desc="Transcribing", unit="chunk") as pbar:
            for future in as_completed(futures):
                result = future.result()
                results[result['chunk_num']] = result
                pbar.update(1)
    
    # Return in order
    return [results[i] for i in sorted(results.keys())]


def _transcribe_whisper_only(
    client: OpenAI,
    chunks: List[Dict[str, Any]],
    max_workers: int
) -> List[Dict[str, Any]]:
    """Transcribe using Whisper with word-level timestamps."""
    
    def transcribe_chunk(chunk_info):
        chunk_num = chunk_info['chunk_num']
        chunk_path = chunk_info['path']
        
        with open(chunk_path, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model=AudioTranscriptionConfig.WHISPER_MODEL,
                file=audio_file,
                response_format=AudioTranscriptionConfig.WHISPER_RESPONSE_FORMAT,
                timestamp_granularities=["word"]
            )
        
        # Format with timestamps
        text_with_timestamps = _format_whisper_timestamps(
            response.words,
            chunk_info['start_time']
        )
        
        return {
            'chunk_num': chunk_num,
            'text': text_with_timestamps,
            'start_time': chunk_info['start_time'],
            'end_time': chunk_info['end_time'],
            'words': response.words
        }
    
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(transcribe_chunk, chunk): chunk for chunk in chunks}
        
        with tqdm(total=len(chunks), desc="Transcribing (Whisper)", unit="chunk") as pbar:
            for future in as_completed(futures):
                result = future.result()
                results[result['chunk_num']] = result
                pbar.update(1)
    
    return [results[i] for i in sorted(results.keys())]


def _transcribe_hybrid(
    client: OpenAI,
    chunks: List[Dict[str, Any]],
    max_workers: int,
    state: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Transcribe using both models in parallel, then combine."""
    
    def transcribe_chunk_both(chunk_info):
        chunk_num = chunk_info['chunk_num']
        chunk_path = chunk_info['path']
        
        with open(chunk_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        # Transcribe with both models in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            # GPT-4o transcribe
            gpt_future = executor.submit(
                lambda: client.audio.transcriptions.create(
                    model=AudioTranscriptionConfig.GPT_TRANSCRIBE_MODEL,
                    file=("audio.wav", audio_data),
                    response_format="text"
                )
            )
            
            # Whisper
            whisper_future = executor.submit(
                lambda: client.audio.transcriptions.create(
                    model=AudioTranscriptionConfig.WHISPER_MODEL,
                    file=("audio.wav", audio_data),
                    response_format=AudioTranscriptionConfig.WHISPER_RESPONSE_FORMAT,
                    timestamp_granularities=["word"]
                )
            )
            
            gpt_text = gpt_future.result()
            whisper_response = whisper_future.result()
        
        return {
            'chunk_num': chunk_num,
            'gpt_text': gpt_text,
            'whisper_words': whisper_response.words,
            'start_time': chunk_info['start_time'],
            'end_time': chunk_info['end_time']
        }
    
    # Transcribe all chunks
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(transcribe_chunk_both, chunk): chunk for chunk in chunks}
        
        with tqdm(total=len(chunks), desc="Transcribing (Hybrid)", unit="chunk") as pbar:
            for future in as_completed(futures):
                result = future.result()
                results[result['chunk_num']] = result
                pbar.update(1)
    
    ordered_results = [results[i] for i in sorted(results.keys())]
    
    # Combine using LLM
    print("Combining transcriptions with LLM...")
    combined = _combine_with_llm(client, ordered_results)
    
    return combined


def _transcribe_sliding_window(
    client: OpenAI,
    chunks: List[Dict[str, Any]],
    max_workers: int,
    state: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Transcribe using Whisper first, then GPT-4o with context."""
    
    # Step 1: Transcribe all chunks with Whisper
    print("Step 1: Transcribing with Whisper...")
    whisper_results = _transcribe_whisper_only(client, chunks, max_workers)
    
    # Step 2: Use Whisper text as context for GPT-4o
    print("Step 2: Refining with GPT-4o using Whisper context...")
    
    def refine_chunk(idx):
        chunk_info = chunks[idx]
        whisper_result = whisper_results[idx]
        chunk_path = chunk_info['path']
        
        # Get context from previous chunk
        context = ""
        if idx > 0:
            prev_words = whisper_results[idx - 1].get('words', [])
            if prev_words:
                context_words = prev_words[-AudioTranscriptionConfig.SLIDING_WINDOW_CONTEXT_WORDS:]
                context = " ".join([w.word for w in context_words])
        
        # Create prompt with context
        prompt = "Transcribe this audio accurately."
        if context:
            prompt += f" Previous context: ...{context}"
        
        with open(chunk_path, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model=AudioTranscriptionConfig.GPT_TRANSCRIBE_MODEL,
                file=audio_file,
                response_format="text",
                prompt=prompt
            )
        
        # Combine GPT text with Whisper timestamps
        return {
            'chunk_num': chunk_info['chunk_num'],
            'text': response,
            'whisper_words': whisper_result.get('words', []),
            'start_time': chunk_info['start_time'],
            'end_time': chunk_info['end_time']
        }
    
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(refine_chunk, i): i for i in range(len(chunks))}
        
        with tqdm(total=len(chunks), desc="Refining", unit="chunk") as pbar:
            for future in as_completed(futures):
                result = future.result()
                results[result['chunk_num']] = result
                pbar.update(1)
    
    ordered_results = [results[i] for i in sorted(results.keys())]
    
    # Map timestamps to refined text
    print("Mapping timestamps to refined text...")
    final_results = _map_timestamps_to_text(client, ordered_results)
    
    return final_results


def _format_whisper_timestamps(words: List[Any], chunk_start_time: float) -> str:
    """Format Whisper words with timestamps."""
    if not words:
        return ""
    
    lines = []
    current_line = []
    current_time = None
    
    for word in words:
        word_start = chunk_start_time + word.start
        
        if current_time is None:
            current_time = word_start
        
        current_line.append(word.word)
        
        # Start new line every ~10 seconds or at sentence end
        if (word_start - current_time > 10) or word.word.strip().endswith(('.', '!', '?')):
            timestamp = _format_timestamp(current_time)
            lines.append(f"[{timestamp}] {' '.join(current_line).strip()}")
            current_line = []
            current_time = None
    
    # Add remaining words
    if current_line:
        timestamp = _format_timestamp(current_time if current_time else chunk_start_time)
        lines.append(f"[{timestamp}] {' '.join(current_line).strip()}")
    
    return "\n".join(lines)


def _format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _combine_with_llm(client: OpenAI, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Use LLM to combine GPT and Whisper transcriptions."""
    combined = []
    
    for result in results:
        gpt_text = result['gpt_text']
        whisper_words = result.get('whisper_words', [])
        
        if not whisper_words:
            # No timestamps available
            combined.append({
                'chunk_num': result['chunk_num'],
                'text': gpt_text,
                'start_time': result['start_time'],
                'end_time': result['end_time']
            })
            continue
        
        # Create prompt for LLM
        whisper_text = " ".join([w.word for w in whisper_words])
        
        prompt = f"""Combine these two transcriptions of the same audio, using the first for accuracy and the second for timing:

<accurate_text>
{gpt_text}
</accurate_text>

<timed_words>
{whisper_text}
</timed_words>

Output the accurate text with sentence-level timestamps in format: [HH:MM:SS] Sentence.
Use the word timings to determine sentence start times."""
        
        response = client.chat.completions.create(
            model=AudioTranscriptionConfig.GPT_LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=AudioTranscriptionConfig.LLM_TEMPERATURE
        )
        
        combined_text = response.choices[0].message.content
        
        combined.append({
            'chunk_num': result['chunk_num'],
            'text': combined_text,
            'start_time': result['start_time'],
            'end_time': result['end_time']
        })
    
    return combined


def _map_timestamps_to_text(client: OpenAI, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Map Whisper timestamps to GPT-refined text."""
    final = []
    
    for result in results:
        gpt_text = result['text']
        whisper_words = result.get('whisper_words', [])
        chunk_start = result['start_time']
        
        if not whisper_words:
            final.append({
                'chunk_num': result['chunk_num'],
                'text': gpt_text,
                'start_time': result['start_time'],
                'end_time': result['end_time']
            })
            continue
        
        # Use LLM to map timestamps
        whisper_text_with_times = []
        for w in whisper_words:
            time = _format_timestamp(chunk_start + w.start)
            whisper_text_with_times.append(f"[{time}] {w.word}")
        
        prompt = f"""Map timestamps from word-level timings to this refined text:

<refined_text>
{gpt_text}
</refined_text>

<word_timings>
{' '.join(whisper_text_with_times)}
</word_timings>

Output the refined text with sentence-level timestamps: [HH:MM:SS] Sentence."""
        
        response = client.chat.completions.create(
            model=AudioTranscriptionConfig.GPT_LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=AudioTranscriptionConfig.LLM_TEMPERATURE
        )
        
        final.append({
            'chunk_num': result['chunk_num'],
            'text': response.choices[0].message.content,
            'start_time': result['start_time'],
            'end_time': result['end_time']
        })
    
    return final
