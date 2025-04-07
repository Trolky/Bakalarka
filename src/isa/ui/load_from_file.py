import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

from src.isa.stt.speech_to_text import SpeechToText
from src.isa.paraphrasing.paraphrasing import TextParaphraser
from src.isa.tts.text_to_speech import TextToSpeech


class LoadFromFileFrame(ttk.Frame):
    """Frame for loading and processing lecture recordings from files."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        # Initialize speech-to-text handler
        self.speech_to_text = SpeechToText()
        # Initialize paraphraser
        self.text_paraphraser = TextParaphraser()

        self.text_to_speech = TextToSpeech()
        self.audio_paths = []

        # Processing state variables
        self.is_processing = False
        self.processing_thread = None
        self.selected_file_path = None
        self.transcription_result = None
        self.paraphrased_result = None

        # Configure the frame for responsiveness
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Create scrollable frame
        self.create_scrollable_frame()

        # Main title
        title_frame = ttk.Frame(self.scrollable_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        title_label = ttk.Label(title_frame, text="Nahrávání ze záznamu", font=("Arial", 18, "bold"))
        title_label.pack(side=tk.LEFT)

        # Main content
        content_frame = ttk.Frame(self.scrollable_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # File selection area
        self.create_file_selection_area(content_frame)

        # Processing options
        self.create_processing_options(content_frame)

        # Output area
        self.create_output_area(content_frame)

    def create_scrollable_frame(self):
        """Create a scrollable frame to contain all content with optimized performance."""
        # Create a canvas with scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Add vertical scrollbar to canvas
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create a frame inside the canvas to hold the content
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Configure the scrollable frame to expand to the canvas width
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # Performance optimization: Set canvas attributes
        self.canvas.configure(
            # Reduce overdraw with proper scroll region
            scrollregion=(0, 0, 500, 1000),
            # Double buffering for smoother rendering
            confine=True,
            # Disable border highlight for better performance
            highlightthickness=0
        )

        # Bind mousewheel to scroll
        self.bind_mousewheel()

    def on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame with performance optimization."""
        # Update scroll region only when needed
        new_region = self.canvas.bbox("all")
        current_region = self.canvas.cget("scrollregion").split()

        # Only update if significantly different to reduce redraw operations
        if not current_region or abs(int(float(current_region[3])) - new_region[3]) > 20:
            self.canvas.configure(scrollregion=new_region)

    def on_canvas_configure(self, event):
        """When canvas is resized, resize the inner frame to match with performance optimization."""
        # Update the width of the frame to match the canvas
        canvas_width = event.width
        self.canvas.itemconfig(self.scrollable_frame_id, width=canvas_width)

    def bind_mousewheel(self):
        """Bind mousewheel events to the canvas for scrolling with improved performance."""

        def _on_mousewheel(event):
            # Determine scroll direction and amount
            if event.num == 4 or event.delta > 0:
                # Scroll up - use larger units for smoother scrolling
                self.canvas.yview_scroll(-3, "units")
            elif event.num == 5 or event.delta < 0:
                # Scroll down - use larger units for smoother scrolling
                self.canvas.yview_scroll(3, "units")

        # Bind for different platforms
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows and MacOS
        self.canvas.bind_all("<Button-4>", _on_mousewheel)  # Linux scroll up
        self.canvas.bind_all("<Button-5>", _on_mousewheel)  # Linux scroll down

    def unbind_mousewheel(self):
        """Unbind mousewheel events when frame is not visible."""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def create_file_selection_area(self, parent):
        """Create the file selection area."""
        file_frame = ttk.LabelFrame(parent, text="Vybrat soubor", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 15))

        # File path display and browse button
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X, pady=5)

        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(path_frame, textvariable=self.file_path_var, width=50)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_btn = ttk.Button(path_frame, text="Procházet...", command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # File info display
        info_frame = ttk.Frame(file_frame)
        info_frame.pack(fill=tk.X, pady=5)

        ttk.Label(info_frame, text="Informace o souboru:").pack(anchor="w")
        self.file_info_text = tk.Text(info_frame, height=3, width=50, state="disabled")
        self.file_info_text.pack(fill=tk.X, pady=(5, 0))

    def create_processing_options(self, parent):
        """Create the processing options area."""
        options_frame = ttk.LabelFrame(parent, text="Možnosti zpracování", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 15))

        # Create a notebook for tabbed options
        notebook = ttk.Notebook(options_frame)
        notebook.pack(fill=tk.X, pady=5)

        # Basic options tab
        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text="STT Základní")
        self.create_basic_options(basic_tab)

        # Advanced options tab
        advanced_tab = ttk.Frame(notebook)
        notebook.add(advanced_tab, text="STT Pokročilé")
        self.create_advanced_options(advanced_tab)

        # Paraphrasing options tab
        paraphrase_tab = ttk.Frame(notebook)
        notebook.add(paraphrase_tab, text="Parafrázování")
        self.create_paraphrasing_options(paraphrase_tab)

        tts_tab = ttk.Frame(notebook)
        notebook.add(tts_tab, text="TTS")
        self.create_tts_options(tts_tab)

        # Process button
        self.process_btn = ttk.Button(options_frame, text="Zpracovat soubor",
                                      command=self.process_file)
        self.process_btn.pack(fill=tk.X, pady=10)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(options_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)

        # Status label
        self.status_var = tk.StringVar(value="Připraveno")
        status_label = ttk.Label(options_frame, textvariable=self.status_var)
        status_label.pack(anchor="w", pady=5)

    def create_tts_options(self, parent):
        """Create text-to-speech options."""
        # Enable TTS option
        enable_frame = ttk.Frame(parent)
        enable_frame.pack(fill=tk.X, pady=5)
        self.enable_tts_var = tk.BooleanVar(value=True)
        enable_check = ttk.Checkbutton(
            enable_frame,
            text="Povolit převod textu na řeč",
            variable=self.enable_tts_var,
            command=self.toggle_tts_options
        )
        enable_check.pack(anchor="w", pady=2)

        # Voice selection
        voice_frame = ttk.Frame(parent)
        voice_frame.pack(fill=tk.X, pady=5)
        ttk.Label(voice_frame, text="Hlas:").pack(side=tk.LEFT)
        voices = [f"{k} ({v})" for k, v in self.text_to_speech.get_available_voices().items()]
        self.voice_combo = ttk.Combobox(voice_frame, state="readonly", values=voices)
        self.voice_combo.current(0)  # Default to first voice
        self.voice_combo.pack(side=tk.LEFT, padx=(5, 0))

        # Output format
        format_frame = ttk.Frame(parent)
        format_frame.pack(fill=tk.X, pady=5)
        ttk.Label(format_frame, text="Formát:").pack(side=tk.LEFT)
        formats = ["wav", "mp3"]
        self.format_combo = ttk.Combobox(format_frame, state="readonly", values=formats)
        self.format_combo.current(0)  # Default to wav
        self.format_combo.pack(side=tk.LEFT, padx=(5, 0))

        # Chunk size
        chunk_frame = ttk.Frame(parent)
        chunk_frame.pack(fill=tk.X, pady=5)
        ttk.Label(chunk_frame, text="Velikost části (znaky):").pack(side=tk.LEFT)
        self.chunk_size_var = tk.StringVar(value="4000")
        chunk_entry = ttk.Entry(chunk_frame, textvariable=self.chunk_size_var, width=10)
        chunk_entry.pack(side=tk.LEFT, padx=(5, 0))

        # Output directory options
        dir_frame = ttk.LabelFrame(parent, text="Umístění výstupu (povinné)", padding=5)
        dir_frame.pack(fill=tk.X, pady=5)

        # Output directory selection
        output_dir_frame = ttk.Frame(dir_frame)
        output_dir_frame.pack(fill=tk.X, pady=5)

        self.output_dir_var = tk.StringVar()
        self.output_dir_entry = ttk.Entry(output_dir_frame, textvariable=self.output_dir_var, width=40)
        self.output_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.browse_dir_btn = ttk.Button(
            output_dir_frame,
            text="Procházet...",
            command=self.browse_output_dir
        )
        self.browse_dir_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # File naming options
        naming_frame = ttk.LabelFrame(parent, text="Pojmenování souboru", padding=5)
        naming_frame.pack(fill=tk.X, pady=5)

        # File name
        prefix_frame = ttk.Frame(naming_frame)
        prefix_frame.pack(fill=tk.X, pady=2)
        ttk.Label(prefix_frame, text="Název souboru:").pack(side=tk.LEFT)
        self.file_prefix_var = tk.StringVar(value="")
        prefix_entry = ttk.Entry(prefix_frame, textvariable=self.file_prefix_var, width=20)
        prefix_entry.pack(side=tk.LEFT, padx=(5, 0))

        # Naming pattern explanation
        naming_info = ttk.Label(
            naming_frame,
            text="Pokud nezadáte název, bude použit název vstupního souboru.",
            wraplength=400,
            justify="left"
        )
        naming_info.pack(anchor="w", pady=5)


    def toggle_tts_options(self):
        """Enable or disable TTS options based on the TTS checkbox."""
        # This method is called when the TTS checkbox is toggled
        if self.enable_tts_var.get():
            # TTS is enabled, ensure output directory is set
            if not self.output_dir_var.get():
                # Set default output directory based on input file if available
                if self.selected_file_path:
                    input_filename = os.path.splitext(os.path.basename(self.selected_file_path))[0]
                    default_dir = os.path.join(os.path.dirname(self.selected_file_path), f"{input_filename}_audio")
                    self.output_dir_var.set(default_dir)

    def browse_output_dir(self):
        """Open a directory selection dialog."""
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir_var.set(dir_path)

    def create_basic_options(self, parent):
        """Create basic transcription options."""
        # Transcription model selection
        model_frame = ttk.Frame(parent)
        model_frame.pack(fill=tk.X, pady=5)

        ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT)
        models = self.speech_to_text.get_available_models()
        self.model_combo = ttk.Combobox(model_frame, state="readonly", values=models)
        self.model_combo.current(0)  # Default to first model (nova-2)
        self.model_combo.pack(side=tk.LEFT, padx=(5, 0))

        # Language selection
        language_frame = ttk.Frame(parent)
        language_frame.pack(fill=tk.X, pady=5)

        ttk.Label(language_frame, text="Jazyk:").pack(side=tk.LEFT)
        languages = [lang["name"] for lang in self.speech_to_text.get_available_languages()]
        language_codes = [lang["code"] for lang in self.speech_to_text.get_available_languages()]
        self.language_combo = ttk.Combobox(language_frame, state="readonly", values=languages)
        self.language_combo.current(0)  # Default to first language (Czech)
        self.language_combo.pack(side=tk.LEFT, padx=(5, 0))

        # Store language codes for later use
        self.language_codes = language_codes

        # Additional options
        options_grid = ttk.Frame(parent)
        options_grid.pack(fill=tk.X, pady=5)

        # Diarization option (speaker identification)
        self.diarize_var = tk.BooleanVar(value=True)
        diarize_check = ttk.Checkbutton(options_grid, text="Identifikace mluvčích", variable=self.diarize_var)
        diarize_check.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        # Smart formatting option
        self.smart_format_var = tk.BooleanVar(value=True)
        smart_format_check = ttk.Checkbutton(options_grid, text="Inteligentní formátování",
                                             variable=self.smart_format_var)
        smart_format_check.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        # Punctuation option
        self.punctuate_var = tk.BooleanVar(value=True)
        punctuate_check = ttk.Checkbutton(options_grid, text="Interpunkce", variable=self.punctuate_var)
        punctuate_check.grid(row=1, column=0, sticky="w", padx=5, pady=2)

        # Utterances option
        self.utterances_var = tk.BooleanVar(value=True)
        utterances_check = ttk.Checkbutton(options_grid, text="Rozdělení na věty", variable=self.utterances_var)
        utterances_check.grid(row=1, column=1, sticky="w", padx=5, pady=2)

    def create_advanced_options(self, parent):
        """Create advanced transcription options."""
        # Chunking options
        chunking_frame = ttk.LabelFrame(parent, text="Rozdělení souboru na části", padding=5)
        chunking_frame.pack(fill=tk.X, pady=5)

        # Force chunking option
        self.force_chunking_var = tk.BooleanVar(value=False)
        force_chunking_check = ttk.Checkbutton(
            chunking_frame,
            text="Vynutit rozdělení souboru na části",
            variable=self.force_chunking_var
        )
        force_chunking_check.pack(anchor="w", pady=2)

        # Chunking explanation
        chunking_info = ttk.Label(
            chunking_frame,
            text="Rozdělení velkých souborů na menší části může zlepšit přesnost přepisu, "
                 "ale může způsobit problémy s kontextem mezi částmi.",
            wraplength=400,
            justify="left"
        )
        chunking_info.pack(anchor="w", pady=5)

        # Chunk size threshold
        threshold_frame = ttk.Frame(chunking_frame)
        threshold_frame.pack(fill=tk.X, pady=2)

        ttk.Label(threshold_frame, text="Velikostní práh pro rozdělení (MB):").pack(side=tk.LEFT)
        self.chunk_threshold_var = tk.StringVar(value=str(self.speech_to_text.chunking_config["size_threshold"]))
        threshold_entry = ttk.Entry(threshold_frame, textvariable=self.chunk_threshold_var, width=10)
        threshold_entry.pack(side=tk.LEFT, padx=(5, 0))

        # Chunk duration
        duration_frame = ttk.Frame(chunking_frame)
        duration_frame.pack(fill=tk.X, pady=2)

        ttk.Label(duration_frame, text="Maximální délka části (minuty):").pack(side=tk.LEFT)
        self.chunk_duration_var = tk.StringVar(value=str(self.speech_to_text.chunking_config["max_chunk_duration"]))
        duration_entry = ttk.Entry(duration_frame, textvariable=self.chunk_duration_var, width=10)
        duration_entry.pack(side=tk.LEFT, padx=(5, 0))

        # Chunk overlap
        overlap_frame = ttk.Frame(chunking_frame)
        overlap_frame.pack(fill=tk.X, pady=2)

        ttk.Label(overlap_frame, text="Překryv mezi částmi (ms):").pack(side=tk.LEFT)
        self.chunk_overlap_var = tk.StringVar(value=str(self.speech_to_text.chunking_config["chunk_overlap_ms"]))
        overlap_entry = ttk.Entry(overlap_frame, textvariable=self.chunk_overlap_var, width=10)
        overlap_entry.pack(side=tk.LEFT, padx=(5, 0))

        # Reset to defaults button
        reset_btn = ttk.Button(chunking_frame, text="Obnovit výchozí hodnoty", command=self.reset_chunking_options)
        reset_btn.pack(anchor="e", pady=5)

    def create_paraphrasing_options(self, parent):
        """Create paraphrasing options."""
        # Enable paraphrasing option
        enable_frame = ttk.Frame(parent)
        enable_frame.pack(fill=tk.X, pady=5)

        self.enable_paraphrase_var = tk.BooleanVar(value=True)
        enable_check = ttk.Checkbutton(
            enable_frame,
            text="Povolit parafrázi přepisu",
            variable=self.enable_paraphrase_var
        )
        enable_check.pack(anchor="w", pady=2)

        # Paraphrasing explanation
        paraphrase_info = ttk.Label(
            parent,
            text="Parafráze přepisu může pomoci zlepšit čitelnost a srozumitelnost textu, "
                 "ale může změnit některé formulace oproti původnímu přepisu.",
            wraplength=400,
            justify="left"
        )
        paraphrase_info.pack(anchor="w", pady=5)

        # Style selection
        style_frame = ttk.Frame(parent)
        style_frame.pack(fill=tk.X, pady=5)

        ttk.Label(style_frame, text="Styl parafráze:").pack(side=tk.LEFT)
        styles = [style["name"] for style in self.text_paraphraser.get_available_styles()]
        style_codes = [style["code"] for style in self.text_paraphraser.get_available_styles()]
        self.style_combo = ttk.Combobox(style_frame, state="readonly", values=styles)
        self.style_combo.current(0)  # Default to first style (standard)
        self.style_combo.pack(side=tk.LEFT, padx=(5, 0))

        # Store style codes for later use
        self.style_codes = style_codes

        # Language selection for paraphrasing
        para_language_frame = ttk.Frame(parent)
        para_language_frame.pack(fill=tk.X, pady=5)

        ttk.Label(para_language_frame, text="Jazyk parafráze:").pack(side=tk.LEFT)
        para_languages = [lang["name"] for lang in self.text_paraphraser.get_available_languages()]
        para_language_codes = [lang["code"] for lang in self.text_paraphraser.get_available_languages()]
        self.para_language_combo = ttk.Combobox(para_language_frame, state="readonly", values=para_languages)
        self.para_language_combo.current(0)  # Default to first language (Czech)
        self.para_language_combo.pack(side=tk.LEFT, padx=(5, 0))

        # Store language codes for later use
        self.para_language_codes = para_language_codes


    def reset_chunking_options(self):
        """Reset chunking options to default values."""
        self.chunk_threshold_var.set(str(100))  # Default size threshold
        self.chunk_duration_var.set(str(30))  # Default duration
        self.chunk_overlap_var.set(str(2000))  # Default overlap
        self.force_chunking_var.set(False)  # Default force chunking

    def create_output_area(self, parent):
        """Create the output display area."""
        output_frame = ttk.LabelFrame(parent, text="Výstup", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Output type selection
        output_type_frame = ttk.Frame(output_frame)
        output_type_frame.pack(fill=tk.X, pady=5)

        self.output_type_var = tk.StringVar(value="transcription")
        ttk.Radiobutton(
            output_type_frame,
            text="Původní přepis",
            variable=self.output_type_var,
            value="transcription",
            command=self.switch_output_view
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.paraphrase_radio = ttk.Radiobutton(
            output_type_frame,
            text="Parafráze",
            variable=self.output_type_var,
            value="paraphrase",
            command=self.switch_output_view,
            state=tk.DISABLED
        )
        self.paraphrase_radio.pack(side=tk.LEFT)


        # Output preview
        preview_frame = ttk.Frame(output_frame)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.output_text = tk.Text(preview_frame, height=10, width=50, wrap=tk.WORD)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(preview_frame, command=self.output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.config(yscrollcommand=scrollbar.set)

        self.output_text.insert(tk.END, "Výstup zpracování se zobrazí zde...\n")
        self.output_text.config(state="disabled")

        # Download button
        button_frame = ttk.Frame(output_frame)
        button_frame.pack(fill=tk.X, pady=5)

        self.download_btn = ttk.Button(
            button_frame,
            text="Stáhnout přepis",
            command=self.download_output,
            state=tk.DISABLED
        )
        self.download_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.copy_btn = ttk.Button(
            button_frame,
            text="Kopírovat do schránky",
            command=self.copy_to_clipboard,
            state=tk.DISABLED
        )
        self.copy_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

    def browse_file(self):
        """Open a file selection dialog."""
        filetypes = [
            ("Audio/Video files", "*.mp3 *.mp4 *.wav *.avi *.mkv *.mov"),
            ("All files", "*.*")
        ]
        file_path = filedialog.askopenfilename(filetypes=filetypes)

        if file_path:
            self.file_path_var.set(file_path)
            self.selected_file_path = file_path
            self.update_file_info(file_path)

    def update_file_info(self, file_path):
        """Update the file information display."""
        try:
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_path)[1]

            info_text = f"Název: {file_name}\n"
            info_text += f"Typ: {file_ext}\n"
            info_text += f"Velikost: {file_size:.2f} MB"

            self.file_info_text.config(state="normal")
            self.file_info_text.delete(1.0, tk.END)
            self.file_info_text.insert(tk.END, info_text)
            self.file_info_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Chyba", f"Nelze načíst informace o souboru: {str(e)}")

    def process_file(self):
        """Process the selected file."""
        if not self.selected_file_path:
            messagebox.showwarning("Upozornění", "Nejprve vyberte soubor ke zpracování.")
            return

        if self.enable_tts_var.get() and not self.output_dir_var.get():
            messagebox.showerror("Chyba", "Pro generování audia je nutné zadat výstupní adresář.")
            return

        if self.is_processing:
            messagebox.showinfo("Informace", "Zpracování již probíhá.")
            return

        self.is_processing = True
        self.process_btn.config(state=tk.DISABLED)
        self.status_var.set("Probíhá převod řeči na text...")
        self.progress_var.set(0)

        # Clear output
        self.output_text.config(state="normal")
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "Zpracování souboru...\n")
        self.output_text.config(state="disabled")


        # Get selected options
        selected_model = self.model_combo.get()
        selected_language_index = self.language_combo.current()
        selected_language_code = self.language_codes[selected_language_index]

        # Configure transcription options
        options = {
            "model": selected_model,
            "language": selected_language_code,
            "diarize": self.diarize_var.get(),
            "smart_format": self.smart_format_var.get(),
            "punctuate": self.punctuate_var.get(),
            "utterances": self.utterances_var.get()
        }

        # Get chunking options
        force_chunking = self.force_chunking_var.get()

        # Update chunking configuration
        try:
            self.speech_to_text.chunking_config["size_threshold"] = float(self.chunk_threshold_var.get())
            self.speech_to_text.chunking_config["max_chunk_duration"] = float(self.chunk_duration_var.get())
            self.speech_to_text.chunking_config["chunk_overlap_ms"] = float(self.chunk_overlap_var.get())
        except ValueError:
            # If conversion fails, use default values
            self.reset_chunking_options()
            messagebox.showwarning("Upozornění", "Neplatné hodnoty pro rozdělení souboru. Použity výchozí hodnoty.")

        # Start transcription
        try:
            self.speech_to_text.transcribe_file(
                file_path=self.selected_file_path,
                callback=self.transcription_complete,
                progress_callback=self.update_progress,
                options=options,
                force_chunking=force_chunking
            )
        except Exception as e:
            self.is_processing = False
            self.process_btn.config(state=tk.NORMAL)
            self.status_var.set(f"Chyba: {str(e)}")
            messagebox.showerror("Chyba", f"Nelze zpracovat soubor: {str(e)}")

    def update_progress(self, progress):
        """Update the progress bar."""
        self.progress_var.set(progress * 100)

    def transcription_complete(self, text, processing_time):
        """Handle completed transcription."""
        self.is_processing = False
        self.process_btn.config(state=tk.NORMAL)

        if text.startswith("Error:"):
            # Handle error
            self.status_var.set(text)
            self.update_output_text(f"\n{text}\n")
            messagebox.showerror("Chyba", text)
        else:
            # Handle success
            self.transcription_result = text
            self.status_var.set(f"Zpracování dokončeno za {processing_time:.2f} sekund")
            self.update_output_text(text)

            # Enable download and copy buttons
            self.download_btn.config(state=tk.NORMAL)
            self.copy_btn.config(state=tk.NORMAL)

            # If auto-paraphrasing is enabled, start paraphrasing
            if self.enable_paraphrase_var.get():
                self.paraphrase_transcription()

    def generate_audio(self):
        """Generate audio from the paraphrased text only."""
        # Only use paraphrased text for TTS
        if not self.paraphrased_result:
            messagebox.showwarning("Upozornění", "Nejsou k dispozici žádné výsledky parafráze pro generování audia.")
            return

        # Check if output directory is specified
        if not self.output_dir_var.get():
            messagebox.showerror("Chyba", "Pro generování audia je nutné zadat výstupní adresář.")
            return

        text = self.paraphrased_result

        # Get selected voice
        voice_selection = self.voice_combo.get()
        voice = voice_selection.split(" ")[0]  # Extract voice key from combo box

        # Get output format
        output_format = self.format_combo.get()

        # Get chunk size
        try:
            chunk_size = int(self.chunk_size_var.get())
        except ValueError:
            chunk_size = 4000
            self.chunk_size_var.set("4000")

        # Get output directory
        output_dir = self.output_dir_var.get()

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Get file name
        file_name = self.file_prefix_var.get()
        if not file_name:
            # Use input filename if no custom name provided
            file_name = os.path.splitext(os.path.basename(self.selected_file_path))[0]

        # Create full output path
        output_path = os.path.join(output_dir, f"{file_name}.{output_format}")

        self.status_var.set("Probíhá generování audia z parafráze...")

        try:
            # Use the new method to generate a single audio file
            audio_path = self.text_to_speech.generate_single_audio_file(
                text=text,
                voice=voice,
                output_format=output_format,
                output_path=output_path,
                chunk_size=chunk_size,
                progress_callback=lambda p: self.progress_var.set(p)
            )

            self.audio_paths = [audio_path]  # Store the path for potential download

            self.status_var.set(f"Audio vygenerováno: {audio_path}")
            messagebox.showinfo("Úspěch", f"Audio soubor byl vygenerován:\n{audio_path}")
        except Exception as e:
            self.status_var.set(f"Chyba generování audia: {str(e)}")
            messagebox.showerror("Chyba", f"Nelze vygenerovat audio: {str(e)}")

    def paraphrase_transcription(self):
        """Paraphrase the transcription result."""
        if not self.transcription_result:
            messagebox.showwarning("Upozornění", "Nejsou k dispozici žádné výsledky k parafrázi.")
            return

        if self.is_processing:
            messagebox.showinfo("Informace", "Zpracování již probíhá.")
            return

        self.is_processing = True
        self.status_var.set("Probíhá parafrázování...")
        self.progress_var.set(0)

        # Get selected paraphrasing options
        selected_style_index = self.style_combo.current()
        selected_style_code = self.style_codes[selected_style_index]

        selected_language_index = self.para_language_combo.current()
        selected_language_code = self.para_language_codes[selected_language_index]

        # Configure paraphrasing options
        options = {
            "style": selected_style_code,
            "language": selected_language_code
        }

        # Start paraphrasing
        try:
            self.text_paraphraser.paraphrase_text(
                text=self.transcription_result,
                callback=self.paraphrasing_complete,
                progress_callback=self.update_progress,
                options=options
            )
        except Exception as e:
            self.is_processing = False
            self.status_var.set(f"Chyba parafráze: {str(e)}")
            messagebox.showerror("Chyba", f"Nelze parafrázi provést: {str(e)}")

    def paraphrasing_complete(self, text, processing_time):
        """Handle completed paraphrasing."""
        self.is_processing = False

        if text.startswith("Error:"):
            # Handle error
            self.status_var.set(text)
            messagebox.showerror("Chyba", text)
        else:
            # Handle success
            self.paraphrased_result = text
            self.status_var.set(f"Parafráze dokončena za {processing_time:.2f} sekund")

            # Enable paraphrase radio button
            self.paraphrase_radio.config(state=tk.NORMAL)

            # Switch to paraphrase view
            self.output_type_var.set("paraphrase")
            self.switch_output_view()

            # Now that paraphrasing is complete, generate audio if TTS is enabled
            if self.enable_tts_var.get():
                self.generate_audio()

    def switch_output_view(self):
        """Switch between original transcription and paraphrased view."""
        output_type = self.output_type_var.get()

        if output_type == "transcription" and self.transcription_result:
            self.update_output_text(self.transcription_result)
        elif output_type == "paraphrase" and self.paraphrased_result:
            self.update_output_text(self.paraphrased_result)

    def update_output_text(self, text):
        """Update the output text area."""
        self.output_text.config(state="normal")
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, text)
        self.output_text.config(state="disabled")
        self.output_text.see(tk.END)

    def download_output(self):
        """Save the output to a file."""
        output_type = self.output_type_var.get()

        if output_type == "transcription" and not self.transcription_result:
            messagebox.showwarning("Upozornění", "Nejsou k dispozici žádné výsledky ke stažení.")
            return
        elif output_type == "paraphrase" and not self.paraphrased_result:
            messagebox.showwarning("Upozornění", "Nejsou k dispozici žádné výsledky parafráze ke stažení.")
            return

        # Ask for save location
        file_types = [("Text files", "*.txt"), ("All files", "*.*")]
        suffix = "_transcript" if output_type == "transcription" else "_paraphrased"
        default_name = os.path.splitext(os.path.basename(self.selected_file_path))[0] + suffix + ".txt"

        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=file_types,
            initialfile=default_name
        )

        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    if output_type == "transcription":
                        f.write(self.transcription_result)
                    else:
                        f.write(self.paraphrased_result)

                self.status_var.set("Soubor uložen")
                messagebox.showinfo("Úspěch", f"Soubor byl úspěšně uložen do:\n{save_path}")
            except Exception as e:
                self.status_var.set(f"Chyba při ukládání: {str(e)}")
                messagebox.showerror("Chyba", f"Nelze uložit soubor: {str(e)}")

        if self.audio_paths:
            # Create a zip file with all audio files
            import zipfile
            zip_path = os.path.join(os.path.dirname(save_path),
                                    f"{os.path.splitext(os.path.basename(save_path))[0]}_audio.zip")

            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for audio_path in self.audio_paths:
                    zipf.write(audio_path, os.path.basename(audio_path))

            messagebox.showinfo("Úspěch", f"Audio soubory byly zabaleny do:\n{zip_path}")

    def copy_to_clipboard(self):
        """Copy the output to clipboard."""
        output_type = self.output_type_var.get()

        if output_type == "transcription" and not self.transcription_result:
            messagebox.showwarning("Upozornění", "Nejsou k dispozici žádné výsledky ke kopírování.")
            return
        elif output_type == "paraphrase" and not self.paraphrased_result:
            messagebox.showwarning("Upozornění", "Nejsou k dispozici žádné výsledky parafráze ke kopírování.")
            return

        self.clipboard_clear()

        if output_type == "transcription":
            self.clipboard_append(self.transcription_result)
            self.status_var.set("Přepis zkopírován do schránky")
        else:
            self.clipboard_append(self.paraphrased_result)
            self.status_var.set("Parafráze zkopírována do schránky")
