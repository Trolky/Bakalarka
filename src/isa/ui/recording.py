# modules/recording.py - Module for recording lectures

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from datetime import datetime, timedelta
import threading
import time


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

        # No signal text
        self.preview_canvas.create_text(240, 135, text="Žádný video signál", fill="white", font=("Arial", 14))

        # Status display below preview
        status_frame = ttk.Frame(preview_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Připravceno")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="green")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Recording time
        time_frame = ttk.Frame(preview_frame)
        time_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(time_frame, text="Čas nahrávání:").pack(side=tk.LEFT)
        self.time_var = tk.StringVar(value="00:00:00")
        time_label = ttk.Label(time_frame, textvariable=self.time_var)
        time_label.pack(side=tk.LEFT, padx=5)

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
        source_combo = ttk.Combobox(source_frame,state="readonly", values=sources)
        source_combo.current(0)
        source_combo.pack(fill=tk.X, pady=(5, 0))

        # Audio source
        audio_frame = ttk.Frame(settings_frame)
        audio_frame.pack(fill=tk.X, pady=5)

        ttk.Label(audio_frame, text="Zdroj audia:").pack(anchor="w")
        audio_sources = ["Mikrofon"]
        audio_combo = ttk.Combobox(audio_frame,state="readonly", values=audio_sources)
        audio_combo.current(0)
        audio_combo.pack(fill=tk.X, pady=(5, 0))

        # Quality settings
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.pack(fill=tk.X, pady=5)

        ttk.Label(quality_frame, text="Kvalita nahrávky:").pack(anchor="w")
        qualities = ["1080p", "720p", "480p"]
        quality_combo = ttk.Combobox(quality_frame,state="readonly", values=qualities)
        quality_combo.current(0)
        quality_combo.pack(fill=tk.X, pady=(5, 0))

        # Output folder
        folder_frame = ttk.Frame(settings_frame)
        folder_frame.pack(fill=tk.X, pady=5)

        ttk.Label(folder_frame, text="Uložit do:").pack(anchor="w")

        path_frame = ttk.Frame(folder_frame)
        path_frame.pack(fill=tk.X, pady=(5, 0))

        self.folder_var = tk.StringVar()
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

    # TODO Complete
    def toggle_recording(self):
        """Start or stop recording."""


    def stop_recording(self):
        """Stop the recording process."""
        self.is_recording = False
        self.stop_thread = True
        self.record_btn.config(text="Začít nahrávat")
        self.pause_btn.config(state=tk.DISABLED)
        self.status_var.set("Připraveno")

        # Reset the video preview
        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(240, 135, text="No video signal", fill="white", font=("Arial", 14))

        # Show completion message
        filename = f"{self.title_entry.get()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        messagebox.showinfo("Recording Complete",
                            f"Recording saved to:\n{os.path.join(self.folder_var.get(), filename)}")


    def pause_recording(self):
        """Pause or resume recording."""
        if self.status_var.get() == "Nahrávání":
            self.status_label.config(foreground="red")
            self.status_var.set("Pozastaveno")
            self.pause_btn.config(text="Resume")
        else:
            self.status_var.set("Nahrávání")
            self.status_label.config(foreground="green")
            self.pause_btn.config(text="Pozastaveno")

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


    def preview_source(self):
        """Preview the selected video source."""
        # Simulate changing the preview
        self.preview_canvas.delete("all")

