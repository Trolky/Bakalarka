import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext


class DashboardFrame(ttk.Frame):
    """Dashboard module showing system overview and recent activities."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Create welcome header
        self.create_header()

        # Create main content area with usage instructions
        self.create_content()

        # Create footer with quick action buttons
        self.create_footer()

    def create_header(self):
        """Create the welcome header section."""
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        # Welcome title
        title = ttk.Label(header_frame, text="Vítejte v aplikaci Lecture Recording Automation",
                          font=("Arial", 18, "bold"))
        title.pack(anchor="w")

        # Subtitle
        subtitle = ttk.Label(header_frame,
                             text="Automatizovaný systém pro zpracování přednášek",
                             font=("Arial", 12))
        subtitle.pack(anchor="w", pady=(5, 0))

        # Separator
        separator = ttk.Separator(self, orient="horizontal")
        separator.grid(row=0, column=0, sticky="ew", padx=20, pady=(80, 0))

    def create_content(self):
        """Create the main content area with usage instructions."""
        content_frame = ttk.Frame(self)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Create notebook for tabbed interface
        notebook = ttk.Notebook(content_frame)
        notebook.grid(row=0, column=0, sticky="nsew")

        # Usage instructions tab
        usage_tab = ttk.Frame(notebook)
        notebook.add(usage_tab, text="Návod k použití")

        # About tab
        about_tab = ttk.Frame(notebook)
        notebook.add(about_tab, text="O aplikaci")

        # Fill the usage instructions tab
        self.create_usage_tab(usage_tab)

        # Fill the about tab
        self.create_about_tab(about_tab)

    def create_usage_tab(self, parent):
        """Create the usage instructions tab content."""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        # Create scrollable text area
        text_area = scrolledtext.ScrolledText(parent, wrap=tk.WORD, font=("Arial", 11))
        text_area.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        text_area.insert(tk.END, """
NÁVOD K POUŽITÍ

1. NAHRÁVÁNÍ ZE ZÁZNAMU:
   - Klikněte na tlačítko "Nahrávání ze záznamu" v levém menu
   - Vyberte video/audio soubor s přednáškou (podporované formáty: mp4, avi, mp3 atd.)
   - Nastavte parametry zpracování (kvalita transkripce, parafrázování)
   - Pokud je zaplé převod textu na řeč (TTS), je potřeba vybrat kam se uloží výstupní soubor
   - Spusťte zpracování tlačítkem "Zpracovat"
   - Po dokončení se uloží výstupní soubor kam jste ho nastavili a dále můžete stáhnout originální transkripci a parafrázovaný text

2. ŽIVÉ NAHRÁVÁNÍ:
   - Klikněte na tlačítko "Živé nahrávání" v levém menu
   - Zkontrolujte nastavení mikrofonu
   - Spusťte nahrávání tlačítkem "Začít nahrávat"
   - Po dokončení přednášky klikněte na "Ukončit nahrávání", ale ještě něž na to kliknete, chvilku počkejte než se přepíše poslední věta/úsek.
   - Aplikace provede transkripci, parafrázování a TTS
   - Výsledek si můžete stáhnout nebo uložit

TIPY:
- Pro nejlepší výsledky používejte kvalitní mikrofon
- Mluvte zřetelně a v přiměřeném tempu
- Při nahrávání ze záznamu používejte videa/audia s dobrou kvalitou zvuku
        """)
        text_area.config(state=tk.DISABLED)  # Make read-only

    def create_about_tab(self, parent):
        """Create the about tab content."""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        # Create scrollable text area
        text_area = scrolledtext.ScrolledText(parent, wrap=tk.WORD, font=("Arial", 11))
        text_area.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        text_area.insert(tk.END, """
O APLIKACI

Lecture Recording Automation System je nástroj pro automatizaci zpracování přednášek.

Hlavní funkce:
- Transkripce řeči na text pomocí STT (Speech-to-Text) technologie
- Inteligentní parafrázování obsahu
- Převod textu zpět na řeč pomocí TTS (Text-to-Speech) technologie
- Podpora pro zpracování existujících záznamů i živé nahrávání

Technologie:
- Aplikace využívá moderní AI modely pro zpracování přirozeného jazyka
- Podporuje různé výstupní formáty (mp4, avi, mp3 atd.)
- Optimalizováno pro akademické prostředí

Verze: 1.0.0
        """)
        text_area.config(state=tk.DISABLED)  # Make read-only

    def create_footer(self):
        """Create footer with quick action buttons."""
        footer_frame = ttk.Frame(self)
        footer_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))

        # Quick action buttons
        quick_actions_label = ttk.Label(footer_frame, text="Rychlé akce:", font=("Arial", 11, "bold"))
        quick_actions_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Button frame
        button_frame = ttk.Frame(footer_frame)
        button_frame.grid(row=1, column=0, sticky="w")

        # Create quick action buttons
        load_file_btn = ttk.Button(button_frame, text="Nahrát ze souboru",
                                   command=lambda: self.controller.show_frame("load_from_file"))
        load_file_btn.grid(row=0, column=0, padx=(0, 10))

        record_btn = ttk.Button(button_frame, text="Začít živé nahrávání",
                                command=lambda: self.controller.show_frame("recording"))
        record_btn.grid(row=0, column=1, padx=(0, 10))
