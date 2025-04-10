import os
import time
import threading
from typing import Optional, Callable, Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI


class TextParaphraser:
    """
    Handles text paraphrasing using OpenAI's GPT-4o model.
    Supports both synchronous and asynchronous paraphrasing.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the TextParaphraser handler.

        Args:
            api_key: OpenAI API key. If None, will try to load from environment variables.
        """
        # Load environment variables if API key not provided
        if api_key is None:
            load_dotenv()
            api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Provide it directly or set OPENAI_API_KEY environment variable.")

        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)

        # Default paraphrasing options
        self.default_options = {
            "style": "standard",  # Paraphrasing style
            "formality": "neutral",  # Formality level
            "max_length": 4000,  # Maximum text length to process at once (for GPT-4o context)
            "language": "cs"  # Default language
        }

        # For tracking paraphrasing progress
        self.is_paraphrasing = False
        self.current_job = None
        self.paraphrasing_thread = None

    def paraphrase_text(self, text: str, callback: Callable[[str, float], None] = None,
                        progress_callback: Callable[[float], None] = None,
                        options: Optional[Dict[str, Any]] = None) -> None:
        """
        Paraphrase text asynchronously.

        Args:
            text: Text to paraphrase
            callback: Function to call with paraphrased result and processing time
            progress_callback: Function to call with progress updates (0.0 to 1.0)
            options: Custom paraphrasing options to override defaults
        """
        if self.is_paraphrasing:
            raise RuntimeError("A paraphrasing job is already in progress")

        self.is_paraphrasing = True
        self.current_job = text[:50] + "..." if len(text) > 50 else text

        # Start paraphrasing in a separate thread
        self.paraphrasing_thread = threading.Thread(
            target=self._paraphrase_text_task,
            args=(text, callback, progress_callback, options)
        )
        self.paraphrasing_thread.daemon = True
        self.paraphrasing_thread.start()

    def _paraphrase_text_task(self, text: str, callback: Callable[[str, float], None],
                              progress_callback: Callable[[float], None],
                              options: Optional[Dict[str, Any]]) -> None:
        """
        Internal method to handle text paraphrasing in a separate thread.
        """
        try:
            # Update progress for processing start
            if progress_callback:
                progress_callback(0.1)

            # Check if text is empty
            if not text or text.strip() == "":
                if callback:
                    callback("No text to paraphrase", 0)
                return

            # Process text
            start_time = time.time()

            # For long texts, split into chunks
            max_length = self.default_options["max_length"]
            if options and "max_length" in options:
                max_length = options["max_length"]

            if len(text) > max_length:
                result = self._process_in_chunks(text, max_length, progress_callback, options)
            else:
                result = self._process_single_text(text, options)
                if progress_callback:
                    progress_callback(0.9)  # Almost done

            # Calculate processing time
            processing_time = time.time() - start_time

            # Final progress update
            if progress_callback:
                progress_callback(1.0)

            # Return result via callback
            if callback:
                callback(result, processing_time)

        except Exception as e:
            # Handle errors
            if callback:
                callback(f"Error: {str(e)}", 0)
        finally:
            # Reset state
            self.is_paraphrasing = False
            self.current_job = None

    def _process_single_text(self, text: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a single text segment using OpenAI's GPT-4o.

        Args:
            text: Text to paraphrase
            options: Custom options to override defaults

        Returns:
            Paraphrased text
        """
        # Combine default options with custom options
        merged_options = self.default_options.copy()
        if options:
            merged_options.update(options)

        try:
            # Construct the prompt based on style and language
            style_instruction = self._get_style_instruction(merged_options["style"])
            language_code = merged_options["language"]
            language_name = next((lang["name"] for lang in self.get_available_languages()
                                  if lang["code"] == language_code), "Čeština")

            prompt = f"""Paraphrase the following text in {language_name}. {style_instruction}
            Original text:
            {text}
            Paraphrased version:"""
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system",
                     "content": f"You are an expert paraphrasing assistant. Your task is to paraphrase text in {language_name} while maintaining the original meaning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )

            # Extract the paraphrased text from the response
            paraphrased_text = response.choices[0].message.content.strip()
            return paraphrased_text

        except Exception as e:
            raise RuntimeError(f"Failed to paraphrase text: {str(e)}")

    def _get_style_instruction(self, style: str) -> str:
        """Get specific instructions based on the paraphrasing style."""
        style_instructions = {
            "standard": "Maintain a balanced tone and similar complexity to the original.",
            "formal": "Use formal language and academic tone.",
            "simple": "Simplify the language and make it easier to understand.",
            "creative": "Use more creative and expressive language.",
            "academic": "Use academic terminology and formal structure."
        }
        return style_instructions.get(style, style_instructions["standard"])

    def _process_in_chunks(self, text: str, chunk_size: int, progress_callback: Callable[[float], None],
                           options: Optional[Dict[str, Any]]) -> str:
        """
        Process a long text by splitting it into chunks.

        Args:
            text: Text to paraphrase
            chunk_size: Maximum size of each chunk
            progress_callback: Function to call with progress updates
            options: Custom options to override defaults

        Returns:
            Paraphrased text with all chunks combined
        """
        # Split text into sentences (simple split by period)
        sentences = text.split(". ")

        # Group sentences into chunks
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 2 <= chunk_size:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk + ".")
                current_chunk = sentence

        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(current_chunk + ".")

        # Process each chunk
        results = []
        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            if not self.is_paraphrasing:
                break

            # Update progress
            if progress_callback:
                # Reserve 10% for final processing
                progress_callback(0.1 + (i / total_chunks) * 0.8)

            # Process chunk
            paraphrased_chunk = self._process_single_text(chunk, options)
            results.append(paraphrased_chunk)

        # Combine results
        return " ".join(results)

    def cancel_paraphrasing(self) -> None:
        """Cancel the current paraphrasing job if one is running."""
        if self.is_paraphrasing:
            self.is_paraphrasing = False
            # Thread will terminate on next iteration

    def get_available_styles(self) -> List[Dict[str, str]]:
        """
        Get a list of available paraphrasing styles.

        Returns:
            List of style dictionaries with code and name
        """
        return [
            {"code": "standard", "name": "Standardní"},
            {"code": "formal", "name": "Formální"},
            {"code": "simple", "name": "Zjednodušený"},
            {"code": "creative", "name": "Kreativní"},
            {"code": "academic", "name": "Akademický"}
        ]

    def get_available_languages(self) -> List[Dict[str, str]]:
        """
        Get a list of available languages for paraphrasing.

        Returns:
            List of language dictionaries with code and name
        """
        return [
            {"code": "cs", "name": "Čeština"},
            {"code": "en", "name": "Angličtina"},
        ]
