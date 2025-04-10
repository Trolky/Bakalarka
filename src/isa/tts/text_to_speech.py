import requests
import os
import tempfile
from requests.auth import HTTPDigestAuth
import logging
import wave
from typing import List

logger = logging.getLogger(__name__)


class TextToSpeech:
    """
    Service for text-to-speech conversion using a private TTS API.
    """

    # Available voices
    VOICES = {
        "czech_male": "Oldrich30",
        "czech_female": "Ilona30",
        "english_female": "Emma30",
        "english_male": "Tim30"
    }

    def __init__(self):
        self.api_url = "https://ryzen2.megaword.cz:9998/tts-AZUPP/v4/synth"
        self.username = "reichm"
        self.password = "AZUPP-TTSserver"

    def synthesize_speech(self, text, voice="czech_male", output_format="wav", output_path=None) -> str:
        """
        Convert text to speech using the TTS API.

        Args:
            text (str): The text to convert to speech
            voice (str): The voice to use (one of the keys in VOICES)
            output_format (str): The output audio format (wav, mp3, etc.)
            output_path (str, optional): Path to save the audio file. If None, a temporary file is created.

        Returns:
            str: Path to the generated audio file
        """
        if not text:
            logger.error("No text provided for TTS conversion")
            raise ValueError("Text cannot be empty")

        # Get the engine name from the voice key
        engine = self.VOICES.get(voice)
        if not engine:
            if voice in self.VOICES.values():
                # If the user provided the engine name directly
                engine = voice
            else:
                logger.error(f"Invalid voice: {voice}")
                raise ValueError(f"Invalid voice. Available voices: {list(self.VOICES.keys())}")

        # Create output path if not provided
        if not output_path:
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"tts_output_{hash(text)[:8]}.{output_format}")

        # Prepare request data
        data = {
            "engine": engine,
            "format": output_format,
            "text": text
        }

        try:
            # Make the API request with digest authentication
            response = requests.post(
                self.api_url,
                data=data,
                auth=HTTPDigestAuth(self.username, self.password),
                stream=True
            )

            # Check if request was successful
            response.raise_for_status()

            # Save the audio file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"TTS conversion successful. Audio saved to: {output_path}")
            return output_path

        except requests.exceptions.RequestException as e:
            logger.error(f"TTS API request failed: {str(e)}")
            raise RuntimeError(f"Failed to convert text to speech: {str(e)}")

    def get_available_voices(self) -> dict:
        """
        Returns a dictionary of available voices.

        Returns:
            dict: Dictionary mapping voice names to engine IDs
        """
        return self.VOICES

    def process_text_chunks(self, text, language="czech", output_format="wav",
                            output_dir=None, chunk_size=1000) -> List[str]:
        """
        Process a text by splitting it into chunks and converting them to speech.

        Args:
            text (str): The text to convert to speech
            language (str): Language of the text ("czech" or "english")
            output_format (str): Output audio format
            output_dir (str, optional): Directory to save audio files. If None, temp directory is used.
            chunk_size (int): Maximum size of each text chunk

        Returns:
            list: List of paths to the generated audio files
        """
        # Split the text into chunks
        chunks = self._split_text_into_chunks(text, chunk_size)

        # Create output directory if not provided
        if not output_dir:
            output_dir = tempfile.gettempdir()
        else:
            os.makedirs(output_dir, exist_ok=True)

        # Determine the voice based on the language
        voice = f"{language}_male"  # Default to male voice

        audio_paths = []
        for i, chunk in enumerate(chunks):
            # Generate a filename for the audio file
            filename = f"chunk_{i + 1}.{output_format}"
            output_path = os.path.join(output_dir, filename)

            # Convert the text chunk to speech
            audio_path = self.synthesize_speech(
                text=chunk,
                voice=voice,
                output_format=output_format,
                output_path=output_path
            )

            audio_paths.append(audio_path)

        return audio_paths

    def generate_single_audio_file(self, text, voice="czech_male", output_format="wav", output_path=None,
                                   chunk_size=4000, progress_callback=None) -> str:
        """
        Generate a single audio file from a large text by processing in chunks and combining the results.

        Args:
            text (str): The text to convert to speech
            voice (str): The voice to use (one of the keys in VOICES)
            output_format (str): Output audio format (currently only 'wav' supports proper combining)
            output_path (str): Path to save the final audio file
            chunk_size (int): Maximum size of each text chunk
            progress_callback (callable, optional): Function to call with progress updates (0-100)

        Returns:
            str: Path to the generated audio file
        """
        if not text:
            logger.error("No text provided for TTS conversion")
            raise ValueError("Text cannot be empty")

        if not output_path:
            raise ValueError("Output path must be specified for generating a single audio file")

        # Ensure the output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        if len(text) <= chunk_size:
            # Text is small enough for direct conversion
            if progress_callback:
                progress_callback(10)  # Show initial progress

            try:
                # Try direct conversion
                audio_path = self.synthesize_speech(
                    text=text,
                    voice=voice,
                    output_format=output_format,
                    output_path=output_path
                )

                if progress_callback:
                    progress_callback(100)  # Complete progress

                logger.info(f"Single audio file generated: {output_path}")
                return output_path
            except Exception as e:
                # If direct conversion fails for some reason, fall back to chunking
                logger.warning(f"Direct conversion failed despite small text size: {str(e)}")
                logger.info("Falling back to chunking method")
        else:
            # Text is too large, use chunking directly without trying direct conversion
            logger.info(f"Text length ({len(text)} chars) exceeds direct conversion limit, using chunks")

        # Process with chunks
        return self._generate_audio_with_chunks(
            text=text,
            voice=voice,
            output_format=output_format,
            output_path=output_path,
            chunk_size=chunk_size,
            progress_callback=progress_callback
        )

    def _generate_audio_with_chunks(self, text, voice, output_format, output_path, chunk_size=4000,
                                    progress_callback=None) -> str:
        """
        Generate audio by processing text in chunks and combining the results.

        Args:
            text (str): The text to convert to speech
            voice (str): The voice to use
            output_format (str): Output audio format
            output_path (str): Path to save the final audio file
            chunk_size (int): Maximum size of each text chunk
            progress_callback (callable, optional): Function to call with progress updates (0-100)

        Returns:
            str: Path to the generated audio file
        """
        try:
            # Split text into chunks
            chunks = self._split_text_into_chunks(text, chunk_size)

            # Create a temporary directory for chunk files
            temp_dir = tempfile.mkdtemp()
            temp_files = []

            # Process each chunk
            for i, chunk in enumerate(chunks):
                # Generate temporary filename
                temp_path = os.path.join(temp_dir, f"chunk_{i}.{output_format}")

                # Convert the text chunk to speech
                audio_path = self.synthesize_speech(
                    text=chunk,
                    voice=voice,
                    output_format=output_format,
                    output_path=temp_path
                )

                temp_files.append(audio_path)

                # Update progress (reserve 20% for final combining)
                if progress_callback:
                    progress = 10 + (i + 1) / len(chunks) * 70
                    progress_callback(progress)

            # Combine the audio files
            logger.info("Combining audio chunks...")

            # Combine audio files based on format
            if output_format == "wav":
                self._combine_wav_files(temp_files, output_path)
            else:
                # For other formats, we'd need to use external tools like ffmpeg
                # For now, just copy the first file as a placeholder
                import shutil
                shutil.copy(temp_files[0], output_path)
                logger.warning(f"Combining {output_format} files is not supported. Only the first segment was used.")

            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass
            try:
                os.rmdir(temp_dir)
            except:
                pass

            if progress_callback:
                progress_callback(100)  # Complete progress

            logger.info(f"Combined audio file generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate audio with chunks: {str(e)}")
            raise RuntimeError(f"Failed to generate audio: {str(e)}")

    def _combine_wav_files(self, input_files, output_file) -> str:
        """
        Combine multiple WAV files into a single file.

        Args:
            input_files (list): List of paths to the WAV files to combine
            output_file (str): Path to save the combined WAV file

        Returns:
            str: Path to the combined WAV file
        """
        try:
            # Open the first file to get parameters
            with wave.open(input_files[0], 'rb') as first_file:
                params = first_file.getparams()

            # Create output file with same parameters
            with wave.open(output_file, 'wb') as output:
                output.setparams(params)

                # Write data from each input file
                for input_file in input_files:
                    with wave.open(input_file, 'rb') as infile:
                        output.writeframes(infile.readframes(infile.getnframes()))

            return output_file
        except Exception as e:
            logger.error(f"Failed to combine WAV files: {str(e)}")
            raise RuntimeError(f"Failed to combine WAV files: {str(e)}")

    def _split_text_into_chunks(self, text, chunk_size) -> List[str]:
        """
        Split a text into chunks of approximately the given size,
        ensuring that chunks end at sentence boundaries.

        Args:
            text (str): The text to split
            chunk_size (int): Maximum size of each chunk

        Returns:
            list: List of text chunks
        """
        # Split the text into sentences
        sentences = []
        for sentence in text.replace("! ", "!.").replace("? ", "?.").split(". "):
            if sentence:
                sentences.append(sentence.strip() + ".")

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # If adding this sentence would exceed the chunk size,
            # add the current chunk to the list and start a new one
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            current_chunk += " " + sentence

        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks