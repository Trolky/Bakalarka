import tkinter as tk
from tkinter import ttk



class DashboardFrame(ttk.Frame):
    """Dashboard module showing system overview and recent activities."""

    def __init__(self, parent, controller):
        super().__init__(parent)

