import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

# Import application modules
from src.isa.ui.recording import RecordingFrame
from src.isa.ui.dashboard import DashboardFrame
from src.isa.ui.load_from_file import LoadFromFileFrame


class LectureAutomationApp(tk.Tk):
    """Main application class for Lecture Recording Automation System."""

    def __init__(self):
        super().__init__()

        # Configure the main window
        self.title("Lecture Recording Automation System")
        self.geometry("1200x700")
        self.minsize(800, 600)

        # Set theme
        script_dir = os.path.dirname(os.path.abspath(__file__))
        theme_path = os.path.join(script_dir, "themes/azure.tcl")
        self.tk.call("source", theme_path)
        self.tk.call("set_theme", "dark")


        # Create the main container
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create the sidebar for navigation
        self.setup_sidebar()

        # Create the content area
        self.content = ttk.Frame(self.main_container)
        self.content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Initialize frames dictionary
        self.frames = {}

        # Create all frames
        self.create_frames()

        # Show dashboard by default
        self.show_frame("dashboard")

        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_sidebar(self):
        """Create the navigation sidebar."""

        # Create a frame for the sidebar
        sidebar = ttk.Frame(self.main_container, width=200, style="Sidebar.TFrame")
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=0)
        sidebar.pack_propagate(False)  # Force the set width

        # Application title/logo area
        logo_frame = ttk.Frame(sidebar)
        logo_frame.pack(fill=tk.X, pady=(0, 20))

        title = ttk.Label(logo_frame, text="LectureAuto", font=("Arial", 16, "bold"))
        title.pack(pady=10)

        # Navigation buttons
        nav_buttons = [
            ("Dashboard", "dashboard", "Home"),
            ("Nahrávání ze záznamu", "load_from_file", "Nahrávání ze záznamu"),
            ("Živé nahrávání", "recording", "Živé nahrávání"),
            ("Nastavení", "settings", "Nastavení")
        ]

        for text, frame_id, tooltip in nav_buttons:
            btn = ttk.Button(sidebar, text=text, command=lambda f=frame_id: self.show_frame(f), width=18)
            btn.pack(pady=5, padx=10, fill=tk.X)

        # Version info at bottom of sidebar
        version_label = ttk.Label(sidebar, text="Version 1.0.0", font=("Arial", 8))
        version_label.pack(side=tk.BOTTOM, pady=10)

    def create_frames(self):
        """Create all application frames."""

        # Create each frame and add to the dictionary
        self.frames["dashboard"] = DashboardFrame(self.content, self)
        self.frames["recording"] = RecordingFrame(self.content, self)
        self.frames["load_from_file"] = LoadFromFileFrame(self.content, self)
        # self.frames["settings"] = SettingsFrame(self.content, self)

        # Place all frames in the same position
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, frame_id):
        """Raise the specified frame to the top."""
        frame = self.frames.get(frame_id)
        if frame:
            frame.tkraise()

    def on_close(self):
        """Handle application close event."""
        if messagebox.askokcancel("Ukončit", "Opravdu chcete odejít?"):
            # Save any configuration if needed
            # self.config_manager.save_config()
            self.destroy()
