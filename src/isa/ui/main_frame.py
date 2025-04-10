
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
        self.resizable(False, False)  # Make window not resizable

        # Set theme
        script_dir = os.path.dirname(os.path.abspath(__file__))
        theme_path = os.path.join(script_dir, "themes/azure.tcl")
        self.tk.call("source", theme_path)
        self.tk.call("set_theme", "dark")

        # Configure grid for responsiveness
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create the main container
        self.main_container = ttk.Frame(self)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Configure main container grid
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Create the sidebar for navigation
        self.setup_sidebar()

        # Create the content area
        self.content = ttk.Frame(self.main_container)
        self.content.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # Configure content grid
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

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
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)  # Force the set width

        # Configure sidebar grid
        sidebar.grid_columnconfigure(0, weight=1)

        # Application title/logo area
        logo_frame = ttk.Frame(sidebar)
        logo_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        title = ttk.Label(logo_frame, text="LectureAuto", font=("Arial", 16, "bold"))
        title.pack(pady=10)

        # Navigation buttons
        nav_buttons = [
            ("Dashboard", "dashboard", "Home"),
            ("Nahrávání ze záznamu", "load_from_file", "Nahrávání ze záznamu"),
            ("Živé nahrávání", "recording", "Živé nahrávání"),
            ("Nastavení", "settings", "Nastavení")
        ]

        for i, (text, frame_id, tooltip) in enumerate(nav_buttons):
            btn = ttk.Button(sidebar, text=text, command=lambda f=frame_id: self.show_frame(f), width=18)
            btn.grid(row=i + 1, column=0, pady=5, padx=10, sticky="ew")

        # Version info at bottom of sidebar
        version_label = ttk.Label(sidebar, text="Verze 1.0.0", font=("Arial", 8))
        version_label.grid(row=99, column=0, pady=10, sticky="s")  # High row number to push to bottom

    def create_frames(self):
        """Create all application frames."""
        self.frames["dashboard"] = DashboardFrame(self.content, self)
        self.frames["recording"] = RecordingFrame(self.content, self)
        self.frames["load_from_file"] = LoadFromFileFrame(self.content, self)
        # self.frames["settings"] = SettingsFrame(self.content, self)

        # Place all frames in the same position
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

            # Make sure each frame is also responsive
            if hasattr(frame, 'grid_columnconfigure'):
                frame.grid_columnconfigure(0, weight=1)
            if hasattr(frame, 'grid_rowconfigure'):
                frame.grid_rowconfigure(0, weight=1)

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
