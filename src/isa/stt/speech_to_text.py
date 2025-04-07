import os
import time
import threading
from typing import Optional, Callable, Dict, Any, List
from dotenv import load_dotenv
from deepgram import DeepgramClient, PrerecordedOptions, FileSource, LiveOptions
from pydub import AudioSegment


class SpeechToText:
    """
    Handles speech-to-text conversion using Deepgram API.
    Supports both file-based transcription and live audio transcription.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the SpeechToText handler.

        Args:
            api_key: Deepgram API key. If None, will try to load from environment variables.
        """
        # Load environment variables if API key not provided
        if api_key is None:
            load_dotenv()
            api_key = os.environ.get("DEEPGRAM_API_KEY")

        if not api_key:
            raise ValueError(
                "Deepgram API key is required. Provide it directly or set DEEPGRAM_API_KEY environment variable.")

        # Initialize Deepgram client
        self.client = DeepgramClient(api_key)

        # Default transcription options
        self.default_options = {
            "model": "nova-2",
            "smart_format": True,
            "utterances": True,
            "punctuate": True,
            "diarize": True,
            "language": "cs"
        }

        # For tracking transcription progress
        self.is_transcribing = False
        self.current_job = None
        self.transcription_thread = None

        # Chunking configuration
        self.chunking_config = {
            # Files larger than this will be chunked (in MB)
            "size_threshold": 100,
            # Maximum duration for a single chunk (in minutes)
            "max_chunk_duration": 30,
            # Overlap between chunks to maintain context (in milliseconds)
            "chunk_overlap_ms": 2000
        }

    def transcribe_file(self,
                        file_path: str,
                        callback: Callable[[str, float], None] = None,
                        progress_callback: Callable[[float], None] = None,
                        options: Optional[Dict[str, Any]] = None,
                        force_chunking: bool = False) -> None:
        """
        Transcribe an audio file asynchronously.

        Args:
            file_path: Path to the audio file
            callback: Function to call with transcription result and processing time
            progress_callback: Function to call with progress updates (0.0 to 1.0)
            options: Custom transcription options to override defaults
            force_chunking: Force chunking even for small files
        """
        if self.is_transcribing:
            raise RuntimeError("A transcription is already in progress")

        self.is_transcribing = True
        self.current_job = file_path

        # Start transcription in a separate thread
        self.transcription_thread = threading.Thread(
            target=self._transcribe_file_task,
            args=(file_path, callback, progress_callback, options, force_chunking)
        )
        self.transcription_thread.daemon = True
        self.transcription_thread.start()

    def _transcribe_file_task(self,
                              file_path: str,
                              callback: Callable[[str, float], None],
                              progress_callback: Callable[[float], None],
                              options: Optional[Dict[str, Any]],
                              force_chunking: bool) -> None:
        """
        Internal method to handle file transcription in a separate thread.
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Get file size
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

            # Determine if we should chunk based on file size or forced chunking
            should_chunk = (file_size_mb > self.chunking_config["size_threshold"]) or force_chunking

            # For large files or when forced, split into chunks
            if should_chunk:
                # Update progress for processing start
                if progress_callback:
                    progress_callback(0.05)

                # Get audio duration if possible to make better chunking decisions
                try:
                    audio = AudioSegment.from_file(file_path)
                    duration_minutes = len(audio) / (1000 * 60)  # Convert ms to minutes

                    # If duration is less than threshold, don't chunk despite size
                    if duration_minutes < self.chunking_config["max_chunk_duration"] and not force_chunking:
                        should_chunk = False
                except Exception:
                    # If we can't determine duration, fall back to size-based decision
                    pass

                if should_chunk:
                    self._process_in_chunks(file_path, callback, progress_callback, options)
                else:
                    self._process_single_file(file_path, callback, progress_callback, options)
            else:
                self._process_single_file(file_path, callback, progress_callback, options)

        except Exception as e:
            # Handle errors
            if callback:
                callback(f"Error: {str(e)}", 0)
        finally:
            # Reset state
            self.is_transcribing = False
            self.current_job = None

    def _process_single_file(self,
                             file_path: str,
                             callback: Callable[[str, float], None],
                             progress_callback: Callable[[float], None],
                             options: Optional[Dict[str, Any]]) -> None:
        """Process a file as a single unit without chunking."""
        start_time = time.time()

        # Update progress for processing start
        if progress_callback:
            progress_callback(0.1)

        try:
            # Transcribe file
            transcription = self._process_audio_file(file_path, options)

            # Calculate processing time
            processing_time = time.time() - start_time

            # Final progress update
            if progress_callback:
                progress_callback(1.0)

            # Return result via callback
            if callback:
                callback(transcription, processing_time)
        except Exception as e:
            if callback:
                callback(f"Error processing file: {str(e)}", 0)

    def _process_in_chunks(self,
                           file_path: str,
                           callback: Callable[[str, float], None],
                           progress_callback: Callable[[float], None],
                           options: Optional[Dict[str, Any]]) -> None:
        """Process a file by splitting it into chunks with overlap."""
        start_time = time.time()

        try:
            # Load audio file
            audio = AudioSegment.from_file(file_path)

            # Calculate chunk size in milliseconds based on max duration
            chunk_size_ms = self.chunking_config["max_chunk_duration"] * 60 * 1000

            # Create chunks with overlap
            chunks = []
            for i in range(0, len(audio), chunk_size_ms):
                # Start position with consideration for overlap
                start_pos = max(0, i - self.chunking_config["chunk_overlap_ms"] if i > 0 else 0)
                # End position
                end_pos = min(len(audio), i + chunk_size_ms)
                # Extract chunk
                chunk = audio[start_pos:end_pos]
                chunks.append(chunk)

            total_chunks = len(chunks)
            all_transcriptions = []

            # Process each chunk
            for i, chunk in enumerate(chunks):
                if not self.is_transcribing:
                    break

                # Update progress
                if progress_callback:
                    progress_callback((i / total_chunks) * 0.9)  # Reserve 10% for final processing

                # Process chunk
                chunk_file = f"{file_path}_chunk_{i}.mp3"
                chunk.export(chunk_file, format="mp3")

                try:
                    # Transcribe chunk
                    transcription = self._process_audio_file(chunk_file, options)
                    all_transcriptions.append(transcription)
                finally:
                    # Clean up temporary chunk file
                    if os.path.exists(chunk_file):
                        os.remove(chunk_file)

            # Combine all transcriptions with smart joining
            full_transcription = self._smart_join_transcriptions(all_transcriptions)

            # Calculate processing time
            processing_time = time.time() - start_time

            # Final progress update
            if progress_callback:
                progress_callback(1.0)

            # Return result via callback
            if callback:
                callback(full_transcription, processing_time)

        except Exception as e:
            if callback:
                callback(f"Error processing chunks: {str(e)}", 0)

    def _smart_join_transcriptions(self, transcriptions: List[str]) -> str:
        """
        Join transcriptions with intelligent handling of overlaps and duplications.
        This is a simple implementation that could be improved with more sophisticated
        text analysis for better results.
        """
        if not transcriptions:
            return ""

        if len(transcriptions) == 1:
            return transcriptions[0]

        # Simple joining strategy - could be improved with more sophisticated text analysis
        result = transcriptions[0]

        for i in range(1, len(transcriptions)):
            current = transcriptions[i]

            # Try to find overlap between the end of the previous chunk and start of current
            # This is a simple approach - could be improved with more sophisticated algorithms
            min_overlap_len = 10  # Minimum characters to consider for overlap
            max_overlap_len = 100  # Maximum characters to look for overlap

            overlap_found = False

            # Look for overlapping text
            for overlap_len in range(min(max_overlap_len, len(result)), min_overlap_len, -1):
                end_of_prev = result[-overlap_len:]
                start_of_curr = current[:overlap_len]

                # If we find an overlap, join at that point
                if end_of_prev in start_of_curr:
                    overlap_pos = start_of_curr.find(end_of_prev)
                    result += current[overlap_len - overlap_pos:]
                    overlap_found = True
                    break
                elif start_of_curr in end_of_prev:
                    overlap_pos = end_of_prev.find(start_of_curr)
                    result = result[:-overlap_len + overlap_pos] + current
                    overlap_found = True
                    break

            # If no overlap found, just append with a space
            if not overlap_found:
                result += " " + current

        return result

    def _process_audio_file(self, file_path: str, custom_options: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a single audio file with Deepgram.

        Args:
            file_path: Path to the audio file
            custom_options: Custom options to override defaults

        Returns:
            Transcription text
        """
        # Combine default options with custom options
        merged_options = self.default_options.copy()
        if custom_options:
            merged_options.update(custom_options)

        # Create Deepgram options
        options = PrerecordedOptions(
            model=merged_options.get("model", "nova-2"),
            smart_format=merged_options.get("smart_format", True),
            utterances=merged_options.get("utterances", True),
            punctuate=merged_options.get("punctuate", True),
            diarize=merged_options.get("diarize", True),
            language=merged_options.get("language", "cs")
        )

        # Read file
        with open(file_path, "rb") as file:
            buffer_data = file.read()

        # Create payload
        payload: FileSource = {
            "buffer": buffer_data,
        }

        # Send to Deepgram
        response = self.client.listen.rest.v("1").transcribe_file(payload, options, timeout=300)

        # Extract transcription text
        if response and hasattr(response, "results") and hasattr(response.results, "channels"):
            # Get the transcript from the first channel
            transcript = response.results.channels[0].alternatives[0].transcript
            return transcript

        return ""

    def cancel_transcription(self) -> None:
        """Cancel the current transcription job if one is running."""
        if self.is_transcribing:
            self.is_transcribing = False
            # Thread will terminate on next iteration

    def get_available_models(self) -> List[str]:
        """
        Get a list of available Deepgram models.

        Returns:
            List of model names
        """
        # Currently hardcoded, but could be fetched from Deepgram API in the future
        return ["nova-2", "whisper-large", "whisper-medium", "whisper-small", "whisper-tiny"]

    def get_available_languages(self) -> List[Dict[str, str]]:
        """
        Get a list of available languages for transcription.

        Returns:
            List of language dictionaries with code and name
        """
        # Currently hardcoded with common languages, could be fetched from API
        return [
            {"code": "cs", "name": "Čeština"},
            {"code": "en", "name": "Angličtina"},
        ]

    # Placeholder for future live transcription support
    def prepare_live_transcription(self,
                                   callback: Callable[[str], None],
                                   options: Optional[Dict[str, Any]] = None) -> Any:
        """
        Prepare for live audio transcription.

        Args:
            callback: Function to call with transcription results
            options: Custom transcription options

        Returns:
            Connection object for live transcription
        """
        # Combine default options with custom options
        merged_options = self.default_options.copy()
        if options:
            merged_options.update(options)

        # Create Deepgram live options
        live_options = LiveOptions(
            model=merged_options.get("model", "nova-2"),
            smart_format=merged_options.get("smart_format", True),
            utterances=merged_options.get("utterances", True),
            punctuate=merged_options.get("punctuate", True),
            diarize=merged_options.get("diarize", True),
            language=merged_options.get("language", "cs"),
            encoding="linear16",
            channels=1,
            sample_rate=16000
        )

        # This is a placeholder for future implementation
        # In the future, this would return a connection object that can be used to send audio data
        return {
            "options": live_options,
            "callback": callback
        }