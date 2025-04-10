import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from datetime import datetime
import threading
import time
from dotenv import load_dotenv
from src.isa.stt.speech_to_text import LiveTranscription
from src.isa.paraphrasing.paraphrasing import TextParaphraser
from src.isa.tts.text_to_speech import TextToSpeech

# Load environment variables
load_dotenv()


class RecordingFrame(ttk.Frame):
    """Frame for managing lecture recording settings and controls."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Recording state variables
        self.is_recording = False
        self.recording_time = 0
        self.recording_thread = None
        self.stop_thread = False

        # Transcription instance
        self.transcription = None

        self.text_paraphraser = TextParaphraser()
        self.text_to_speech = TextToSpeech()

        # Main title
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, pady=(0, 15))

        title_label = ttk.Label(title_frame, text="Nahrávání", font=("Arial", 18, "bold"))
        title_label.pack(side=tk.LEFT)

        # Main content with video preview and settings
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Split into left (preview) and right (controls) sides
        left_side = ttk.Frame(content_frame)
        left_side.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right_side = ttk.Frame(content_frame)
        right_side.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0), pady=10)

        # Video preview area
        self.create_preview_area(left_side)

        # Transcription area
        self.create_transcription_area(left_side)

        # Recording settings
        self.create_recording_settings(right_side)

        # Recording controls
        self.create_recording_controls(right_side)

    def create_preview_area(self, parent):
        """Create the video preview area."""
        preview_frame = ttk.LabelFrame(parent, text="Náhled videa", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Canvas for video preview (simulated)
        self.preview_canvas = tk.Canvas(preview_frame, bg="black", width=480, height=270)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Status display below preview
        status_frame = ttk.Frame(preview_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Připraveno")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="green")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Recording time
        time_frame = ttk.Frame(preview_frame)
        time_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(time_frame, text="Čas nahrávání:").pack(side=tk.LEFT)
        self.time_var = tk.StringVar(value="00:00:00")
        time_label = ttk.Label(time_frame, textvariable=self.time_var)
        time_label.pack(side=tk.LEFT, padx=5)

    def create_transcription_area(self, parent):
        """Create the live transcription area."""
        transcription_frame = ttk.LabelFrame(parent, text="Živý přepis", padding=10)
        transcription_frame.pack(fill=tk.BOTH, expand=True)

        # Create a frame to hold the text widget and scrollbar
        text_container = ttk.Frame(transcription_frame)
        text_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configure the container to allow the text widget to expand
        text_container.columnconfigure(0, weight=1)
        text_container.rowconfigure(0, weight=1)

        # Create the text widget and scrollbar
        self.transcription_text = tk.Text(text_container, wrap=tk.WORD,
                                          bg="#f0f0f0", state=tk.NORMAL)
        scrollbar = ttk.Scrollbar(text_container, command=self.transcription_text.yview)

        # Grid layout works better than pack for this case
        self.transcription_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Connect the scrollbar to the text widget
        self.transcription_text.config(yscrollcommand=scrollbar.set)

        # Configure text tags for different types of transcription
        self.transcription_text.tag_configure("interim", foreground="gray")
        self.transcription_text.tag_configure("final", foreground="black")
        self.transcription_text.tag_configure("complete", foreground="blue")

        # Transcription controls
        controls_frame = ttk.Frame(transcription_frame)
        controls_frame.pack(fill=tk.X, pady=(5, 0))

        # Enable transcription checkbox
        self.transcription_enabled = tk.BooleanVar(value=True)
        transcription_check = ttk.Checkbutton(controls_frame, text="Povolit přepis",
                                              variable=self.transcription_enabled)
        transcription_check.pack(side=tk.LEFT)

        # Clear button
        clear_btn = ttk.Button(controls_frame, text="Vymazat", command=self.clear_transcription)
        clear_btn.pack(side=tk.RIGHT)

    def create_recording_settings(self, parent):
        """Create the recording settings panel."""
        settings_frame = ttk.LabelFrame(parent, text="Nastavení nahrávání", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 15))

        # Lecture title
        title_frame = ttk.Frame(settings_frame)
        title_frame.pack(fill=tk.X, pady=5)

        ttk.Label(title_frame, text="Titulek:").pack(anchor="w")
        self.title_entry = ttk.Entry(title_frame, width=25)
        self.title_entry.pack(fill=tk.X, pady=(5, 0))

        name_frame = ttk.Frame(settings_frame)
        name_frame.pack(fill=tk.X, pady=5)

        ttk.Label(title_frame, text="Jméno autora:").pack(anchor="w")
        self.name_frame = ttk.Entry(title_frame, width=25)
        self.name_frame.pack(fill=tk.X, pady=(5, 0))

        # Input source selection
        source_frame = ttk.Frame(settings_frame)
        source_frame.pack(fill=tk.X, pady=5)

        ttk.Label(source_frame, text="Zdroj videa:").pack(anchor="w")
        sources = ["Žádný", "Web kamera", "Nahrávání obrazovky"]
        self.source_combo = ttk.Combobox(source_frame, state="readonly", values=sources)
        self.source_combo.current(0)
        self.source_combo.pack(fill=tk.X, pady=(5, 0))

        # Language selection (replacing audio source)
        language_frame = ttk.Frame(settings_frame)
        language_frame.pack(fill=tk.X, pady=5)

        ttk.Label(language_frame, text="Jazyk nahrávky:").pack(anchor="w")

        # Available languages
        languages = [
            {"code": "cs", "name": "Čeština"},
            {"code": "en", "name": "Angličtina"},
        ]

        language_values = [f"{lang['name']} ({lang['code']})" for lang in languages]
        self.recording_language_var = tk.StringVar()
        self.language_combo = ttk.Combobox(language_frame, values=language_values, state="readonly")
        self.language_combo.current(0)  # Default to Czech
        self.language_combo.pack(fill=tk.X, pady=(5, 0))

        # Quality settings
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.pack(fill=tk.X, pady=5)

        ttk.Label(quality_frame, text="Kvalita nahrávky:").pack(anchor="w")
        qualities = ["1080p", "720p", "480p"]
        self.quality_combo = ttk.Combobox(quality_frame, state="readonly", values=qualities)
        self.quality_combo.current(0)
        self.quality_combo.pack(fill=tk.X, pady=(5, 0))

        # Output folder
        folder_frame = ttk.Frame(settings_frame)
        folder_frame.pack(fill=tk.X, pady=5)

        ttk.Label(folder_frame, text="Uložit do:").pack(anchor="w")

        path_frame = ttk.Frame(folder_frame)
        path_frame.pack(fill=tk.X, pady=(5, 0))

        self.folder_var = tk.StringVar(value=os.path.expanduser("~/Documents"))
        folder_entry = ttk.Entry(path_frame, textvariable=self.folder_var)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_btn = ttk.Button(path_frame, text="...", width=3, command=self.browse_output_folder)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))

    def create_recording_controls(self, parent):
        """Create recording control buttons."""
        controls_frame = ttk.LabelFrame(parent, text="Ovládací prvky", padding=10)
        controls_frame.pack(fill=tk.X)

        # Record button
        self.record_btn = ttk.Button(controls_frame, text="Začít nahrávat",
                                     command=self.toggle_recording)
        self.record_btn.pack(fill=tk.X, pady=5)

        # Pause button
        self.pause_btn = ttk.Button(controls_frame, text="Pozastavit", state=tk.DISABLED,
                                    command=self.pause_recording)
        self.pause_btn.pack(fill=tk.X, pady=5)

    def browse_output_folder(self):
        """Open a folder selection dialog."""
        folder = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)

    def toggle_recording(self):
        """Start or stop recording."""
        if not self.is_recording:
            # Check if title is provided
            if not self.title_entry.get().strip():
                messagebox.showwarning("Chybějící informace", "Prosím zadejte titulek nahrávky.")
                return

            # Check if output folder exists
            if not os.path.exists(self.folder_var.get()):
                messagebox.showwarning("Neplatná cesta", "Výstupní složka neexistuje.")
                return

            # Start recording
            self.is_recording = True
            self.stop_thread = False
            self.record_btn.config(text="Zastavit nahrávání")
            self.pause_btn.config(state=tk.NORMAL)
            self.status_var.set("Nahrávání")
            self.status_label.config(foreground="green")

            # Start recording time thread
            self.recording_thread = threading.Thread(target=self.update_recording_time)
            self.recording_thread.daemon = True
            self.recording_thread.start()

            # Start transcription if enabled
            if self.transcription_enabled.get():
                self.start_transcription()

        else:
            # Stop recording
            self.stop_recording()

    def stop_recording(self):
        """Stop the recording process."""
        self.is_recording = False
        self.stop_thread = True
        self.record_btn.config(text="Začít nahrávat")
        self.pause_btn.config(state=tk.DISABLED)
        self.status_var.set("Připraveno")

        # Stop transcription
        self.stop_transcription()

        # Reset the video preview
        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(240, 135, text="Žádný video signál", fill="white", font=("Arial", 14))

        # Get transcription text
        transcription_text = self.get_transcription_text()

        if transcription_text:

            # Process the transcription (paraphrase and TTS)
            self.process_transcription(transcription_text)

    def process_transcription(self, text):
        """Process the transcription by paraphrasing and converting to speech."""
        if not text or text.strip() == "":
            messagebox.showinfo("Informace", "Žádný text k zpracování.")
            return

        try:
            # Show processing dialog
            progress_window = tk.Toplevel(self)
            progress_window.title("Zpracování přepisu")
            progress_window.geometry("300x150")
            progress_window.transient(self)
            progress_window.grab_set()

            # Center the window
            progress_window.update_idletasks()
            width = progress_window.winfo_width()
            height = progress_window.winfo_height()
            x = (progress_window.winfo_screenwidth() // 2) - (width // 2)
            y = (progress_window.winfo_screenheight() // 2) - (height // 2)
            progress_window.geometry(f"{width}x{height}+{x}+{y}")

            # Progress message
            message_label = ttk.Label(progress_window, text="Probíhá parafráze textu...", font=("Arial", 10))
            message_label.pack(pady=10)

            # Progress bar
            progress = ttk.Progressbar(progress_window, orient="horizontal", length=250, mode="determinate")
            progress.pack(pady=10, padx=20)

            # Get selected language code from the language combo
            selected_language = self.language_combo.get()
            language_code = "cs"  # Default to Czech

            # Extract language code from selection (format: "Language Name (code)")
            if "(" in selected_language and ")" in selected_language:
                language_code = selected_language.split("(")[1].split(")")[0]

            # Store necessary data in instance variables for the callback
            self.progress_window = progress_window
            self.progress_bar = progress
            self.message_label = message_label
            self.language_code = language_code

            # Start paraphrasing in a separate thread
            threading.Thread(
                target=lambda: self.text_paraphraser.paraphrase_text(
                    text=text,
                    callback=self.on_paraphrase_complete,
                    progress_callback=lambda p: self.update_progress(progress_window, progress, p),
                    options={"language": language_code}
                ),
                daemon=True
            ).start()

        except Exception as e:
            messagebox.showerror("Chyba při zpracování", f"Nepodařilo se zpracovat přepis: {str(e)}")

    def on_paraphrase_complete(self, paraphrased_text, processing_time):
        """Handle completion of paraphrasing and start text-to-speech conversion."""
        try:
            # Update progress window
            self.message_label.config(text="Převod textu na řeč...")
            self.update_progress(self.progress_window, self.progress_bar, 0.5)

            # Determine voice based on language
            voice = "czech_male" if self.language_code == "cs" else "english_male"

            # Generate output path for audio file
            audio_filename = f"{self.title_entry.get()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_speech.wav"
            audio_filepath = os.path.join(self.folder_var.get(), audio_filename)

            # Convert to speech
            self.text_to_speech.generate_single_audio_file(
                text=paraphrased_text,
                voice=voice,
                output_format="wav",
                output_path=audio_filepath,
                progress_callback=lambda p: self.update_progress(self.progress_window, self.progress_bar, 0.5 + p / 200)
            )

            # Close progress window
            self.progress_window.destroy()

            # Show success message
            messagebox.showinfo("Zpracování dokončeno",
                                f"Přepis byl úspěšně zpracován.\n\n"
                                f"Audio: {audio_filepath}")

        except Exception as e:
            if hasattr(self, 'progress_window') and self.progress_window:
                self.progress_window.destroy()
            messagebox.showerror("Chyba při převodu na řeč", f"Nepodařilo se převést text na řeč: {str(e)}")

    def update_progress(self, window, widget, value):
        """Update progress bar in the progress window."""
        widget["value"] = value * 100
        window.update()

    def pause_recording(self):
        """Pause or resume recording."""
        if self.status_var.get() == "Nahrávání":
            self.status_label.config(foreground="red")
            self.status_var.set("Pozastaveno")
            self.pause_btn.config(text="Pokračovat")

            # Pause transcription
            if self.transcription and self.transcription.is_active():
                self.transcription.pause()
        else:
            self.status_var.set("Nahrávání")
            self.status_label.config(foreground="green")
            self.pause_btn.config(text="Pozastavit")

            # Resume transcription
            if self.transcription and self.transcription.is_active():
                self.transcription.resume()

    def update_recording_time(self):
        """Update the recording time display."""
        while not self.stop_thread:
            if self.status_var.get() == "Nahrávání":
                self.recording_time += 1
                hours = self.recording_time // 3600
                minutes = (self.recording_time % 3600) // 60
                seconds = self.recording_time % 60

                self.time_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            time.sleep(1)

    def start_transcription(self):
        """Start the live transcription process."""
        try:
            # Get selected language code
            selected_language = self.language_combo.get()
            language_code = "cs"  # Default to Czech

            # Extract language code from selection (format: "Language Name (code)")
            if "(" in selected_language and ")" in selected_language:
                language_code = selected_language.split("(")[1].split(")")[0]

            # Configure text tags for different types of transcription
            self.transcription_text.tag_configure("interim", foreground="gray")
            self.transcription_text.tag_configure("final", foreground="black")
            self.transcription_text.tag_configure("complete", foreground="blue")

            # Initialize the LiveTranscription instance if needed
            if not self.transcription:
                self.transcription = LiveTranscription(text_widget=self.transcription_text)

            # Start transcription
            success = self.transcription.start(language_code=language_code)

            if not success:
                messagebox.showerror("Chyba", "Nepodařilo se spustit přepis.")

        except Exception as e:
            messagebox.showerror("Chyba přepisu", f"Nepodařilo se spustit přepis: {str(e)}")

    def stop_transcription(self):
        """Stop the live transcription process."""
        if self.transcription and self.transcription.is_active():
            self.transcription.stop()

    def clear_transcription(self):
        """Clear the transcription text area."""
        if self.transcription:
            self.transcription.clear_text_widget()
        else:
            self.transcription_text.delete(1.0, tk.END)

            # Configure text tags for different types of transcription
            self.transcription_text.tag_configure("interim", foreground="gray")
            self.transcription_text.tag_configure("final", foreground="black")
            self.transcription_text.tag_configure("complete", foreground="blue")

    def get_transcription_text(self):
        """Get the current transcription text."""
        if self.transcription_text:
            return self.transcription_text.get(1.0, tk.END).strip()
        return ""

    def save_transcription(self, text):
        """Save the transcription to a file."""
        if not text:
            return

        try:
            filename = f"{self.title_entry.get()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_transcript.txt"
            filepath = os.path.join(self.folder_var.get(), filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)

            messagebox.showinfo("Přepis uložen", f"Přepis uložen do:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodařilo se uložit přepis: {str(e)}")
