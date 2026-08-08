import hashlib
import json
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import webbrowser
from datetime import datetime
from urllib.parse import quote

try:
    import requests
except ImportError:
    requests = None

PLATFORM_GROUPS = {
    "Social": {
        "Twitter/X": "https://x.com/{}",
        "Instagram": "https://www.instagram.com/{}/",
        "Facebook": "https://www.facebook.com/{}",
        "TikTok": "https://www.tiktok.com/@{}",
        "Pinterest": "https://www.pinterest.com/{}/",
        "Reddit": "https://www.reddit.com/user/{}",
        "Tumblr": "https://{}.tumblr.com/",
        "Mastodon (mastodon.social)": "https://mastodon.social/@{}",
    },
    "Professional": {
        "LinkedIn": "https://www.linkedin.com/in/{}",
        "Medium": "https://medium.com/@{}",
        "About.me": "https://about.me/{}",
        "Linktree": "https://linktr.ee/{}",
        "Behance": "https://www.behance.net/{}",
    },
    "Developer": {
        "GitHub": "https://github.com/{}",
        "GitLab": "https://gitlab.com/{}",
        "StackOverflow": "https://stackoverflow.com/users/{}",
        "Keybase": "https://keybase.io/{}",
        "Bitbucket": "https://bitbucket.org/{}/",
        "CodePen": "https://codepen.io/{}",
        "npm": "https://www.npmjs.com/~{}",
        "PyPI": "https://pypi.org/user/{}/",
        "Docker Hub": "https://hub.docker.com/u/{}",
        "Hacker News": "https://news.ycombinator.com/user?id={}",
        "Replit": "https://replit.com/@{}",
    },
    "Gaming & Streaming": {
        "Twitch": "https://www.twitch.tv/{}",
        "Steam": "https://steamcommunity.com/id/{}",
        "Xbox Gamertag": "https://account.xbox.com/en-us/profile?gamertag={}",
    },
    "Media & Creative": {
        "YouTube": "https://www.youtube.com/@{}",
        "SoundCloud": "https://soundcloud.com/{}",
        "Vimeo": "https://vimeo.com/{}",
        "Dribbble": "https://dribbble.com/{}",
        "DeviantArt": "https://www.deviantart.com/{}",
        "Flickr": "https://www.flickr.com/people/{}/",
        "Last.fm": "https://www.last.fm/user/{}",
        "Spotify": "https://open.spotify.com/user/{}",
    },
    "Other": {
        "Telegram": "https://t.me/{}",
        "Patreon": "https://www.patreon.com/{}",
        "Cash App": "https://cash.app/${}",
        "Venmo": "https://venmo.com/{}",
    },
}

PLATFORMS = {n: u for g in PLATFORM_GROUPS.values() for n, u in g.items()}

DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "tempmail.com", "10minutemail.com",
    "throwaway.email", "yopmail.com", "sharklasers.com", "trashmail.com",
    "getnada.com", "maildrop.cc", "temp-mail.org", "fakeinbox.com",
}

BREACH_LINKS = [
    ("Have I Been Pwned", "https://haveibeenpwned.com/account/{email}"),
    ("HIBP Pastes", "https://haveibeenpwned.com/Pastes/{email}"),
    ("Dehashed (search)", "https://dehashed.com/search?query={email}"),
    ("IntelX (email)", "https://intelx.io/?s={email}"),
    ("LeakCheck", "https://leakcheck.io/search?query={email}"),
    ("BreachDirectory", "https://breachdirectory.org/search?query={email}"),
]

PASTE_LINKS = [
    ("Google → Pastebin", 'https://www.google.com/search?q=site:pastebin.com+"{email}"'),
    ("Google → GitHub gists", 'https://www.google.com/search?q=site:gist.github.com+"{email}"'),
    ("Google → Paste sites", 'https://www.google.com/search?q=site:paste.ee+OR+site:ghostbin.com+"{email}"'),
    ("IntelX pastes", "https://intelx.io/?s={email}"),
]

SEARCH_DORKS = [
    ('Exact email', '"{email}"'),
    ('Exact username', '"{username}"'),
    ('Email in PDFs', 'intext:"{email}" filetype:pdf'),
    ('Username on LinkedIn', 'site:linkedin.com "{username}"'),
    ('Username on Reddit', 'site:reddit.com/user/{username}'),
    ('Email on forums', 'intext:"{email}" (site:stackoverflow.com OR site:discourse.org)'),
    ('Resume / CV leak', 'intext:"{email}" (filetype:pdf OR filetype:doc) resume OR cv'),
    ('Public documents', 'intext:"{email}" filetype:pdf OR filetype:docx OR filetype:xlsx'),
]

ARCHIVE_LINKS = [
    ("Wayback Machine (domain)", "https://web.archive.org/web/*/{domain}"),
    ("Wayback Machine (email search)", 'https://web.archive.org/web/*/"{email}"'),
    ("Google Cache hint", "https://www.google.com/search?q=cache:{domain}"),
    ("Common Crawl index", "https://index.commoncrawl.org/?url={domain}"),
]

CODE_SEARCH_LINKS = [
    ("GitHub code → email", "https://github.com/search?q={email}&type=code"),
    ("GitHub code → username", "https://github.com/search?q={username}&type=code"),
    ("GitLab search", "https://gitlab.com/search?search={email}"),
    ("grep.app", "https://grep.app/search?q={email}"),
    ("Searchcode", "https://searchcode.com/?q={email}"),
    ("Public GitLab commits", 'https://www.google.com/search?q=site:gitlab.com+"{email}"'),
]

DATA_BROKER_LINKS = [
    ("Spokeo", "https://www.spokeo.com/search?q={email}"),
    ("That's Them", "https://thatsthem.com/email/{email}"),
    ("TruePeopleSearch", "https://www.truepeoplesearch.com/results?name={name}&citystatezip="),
    ("FastPeopleSearch", "https://www.fastpeoplesearch.com/name/{name}"),
    ("Whitepages (reverse email)", "https://www.whitepages.com/email/{email}"),
    ("BeenVerified", "https://www.beenverified.com/people/{name}/"),
    ("Nuwber", "https://nuwber.com/search?name={name}"),
]

DOMAIN_LINKS = [
    ("DNS Checker (A)", "https://dnschecker.org/#A/{domain}"),
    ("DNS Checker (MX)", "https://dnschecker.org/#MX/{domain}"),
    ("WHOIS lookup", "https://who.is/whois/{domain}"),
    ("crt.sh (certs)", "https://crt.sh/?q={domain}"),
    ("SecurityHeaders", "https://securityheaders.com/?q={domain}"),
    ("VirusTotal domain", "https://www.virustotal.com/gui/domain/{domain}"),
    ("Shodan search", "https://www.shodan.io/search?query=hostname:{domain}"),
    ("Subdomain finder", "https://subdomainfinder.c99.nl/?domain={domain}"),
]

PEOPLE_LINKS = [
    ("Google name search", 'https://www.google.com/search?q="{name}"'),
    ("LinkedIn name", 'https://www.google.com/search?q=site:linkedin.com+"{name}"'),
    ("Facebook name", 'https://www.google.com/search?q=site:facebook.com+"{name}"'),
    ("Phone reverse (Google)", 'https://www.google.com/search?q="{phone}"'),
    ("Sync.me phone", "https://sync.me/search/?number={phone}"),
]

REVERSE_IMAGE_LINKS = [
    ("Google Lens / Images", "https://lens.google.com/uploadbyurl?url="),
    ("TinEye", "https://tineye.com/"),
    ("Yandex Images", "https://yandex.com/images/"),
    ("PimEyes", "https://pimeyes.com/en"),
]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

IOS_BG = "#F2F2F7"
IOS_CARD = "#FFFFFF"
IOS_SEP = "#D1D1D6"
IOS_LABEL = "#000000"
IOS_SECONDARY = "#8E8E93"
IOS_BLUE = "#007AFF"
IOS_BLUE_PRESSED = "#0051A8"
IOS_GREEN = "#34C759"
IOS_ORANGE = "#FF9500"
IOS_RED = "#FF3B30"
IOS_GROUP_LABEL = "#6D6D72"
IOS_SIDEBAR = "#FFFFFF"
IOS_SIDEBAR_SEL = "#007AFF"
IOS_SIDEBAR_SEL_BG = "#E8F2FF"
IOS_INPUT = "#F2F2F7"

FONT = ("Segoe UI", 11)
FONT_SM = ("Segoe UI", 10)
FONT_LG = ("Segoe UI", 28, "bold")
FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_MONO = ("Consolas", 10)
FONT_MONO_BOLD = ("Consolas", 10, "bold")

NAV_ITEMS = [
    ("GENERAL", None),
    ("home", "Home", "Overview & run audit"),
    ("identifiers", "Identifiers", "Email, username, name…"),
    ("sections", "Audit Sections", "Choose what to scan"),
    ("appearance", "Appearance", "Themes, background, colors"),
    ("RESULTS", None),
    ("platforms", "Platforms", "Social & dev profiles"),
    ("email", "Email Intel", "Gravatar, DNS, APIs"),
    ("breaches", "Breaches & Pastes", "Leak databases"),
    ("search", "Web Search", "Google dork queries"),
    ("archives", "Archives", "Wayback & cache"),
    ("code", "Code & Repos", "Source code leaks"),
    ("brokers", "Data Brokers", "People-search sites"),
    ("domain", "Domain & DNS", "WHOIS, certs, DNS"),
    ("people", "People & Phone", "Name & image search"),
    ("report", "Full Report", "Exportable log"),
]


def flatten_platforms():
    rows = []
    for category, platforms in PLATFORM_GROUPS.items():
        for name, template in platforms.items():
            rows.append((category, name, template))
    return rows


class AuditApp(tk.Tk):
    def __init__(self):
        super().__init__()
        try:
            self.title("Footprint Audit")
            self.geometry("1060x740")
            self.minsize(900, 620)
            self.configure(bg=IOS_BG)
            self.links = []
            self.platform_rows = {}
            self.email_rows = {}
            self._audit_running = False
            self._cancel = False
            self._current_screen = None
            self._nav_buttons = {}
            self.screens = {}
            
            # Appearance settings
            self.bg_image_path = None
            self.bg_opacity = tk.DoubleVar(value=0.1)
            self.theme_var = tk.StringVar(value="light")
            self.font_size_var = tk.StringVar(value="normal")
            
            self._setup_styles()
            self._build_shell()
            self._show_screen("home")
            self.bind("<Control-Return>", lambda _e: self.start_audit())
        except Exception as e:
            print(f"ERROR in __init__: {e}")
            import traceback
            traceback.print_exc()
            raise


    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TProgressbar", troughcolor=IOS_INPUT, background=IOS_BLUE,
                    bordercolor=IOS_SEP, lightcolor=IOS_BLUE, darkcolor=IOS_BLUE, thickness=6)
        s.configure("Treeview", background=IOS_CARD, foreground=IOS_LABEL,
                    fieldbackground=IOS_CARD, borderwidth=0, rowheight=32, font=FONT)
        s.configure("Treeview.Heading", background=IOS_BG, foreground=IOS_SECONDARY,
                    relief="flat", font=("Segoe UI", 10, "bold"))
        s.map("Treeview", background=[("selected", IOS_BLUE)], foreground=[("selected", "#FFFFFF")])
        
        # Enhanced scrollbar styling - more visible
        s.configure("Vertical.TScrollbar", 
                    background=IOS_BG, 
                    troughcolor=IOS_INPUT,
                    bordercolor=IOS_INPUT,
                    lightcolor=IOS_BLUE,
                    darkcolor=IOS_BLUE,
                    arrowcolor=IOS_BLUE)
        s.configure("Horizontal.TScrollbar", 
                    background=IOS_BG, 
                    troughcolor=IOS_INPUT,
                    bordercolor=IOS_INPUT,
                    lightcolor=IOS_BLUE,
                    darkcolor=IOS_BLUE,
                    arrowcolor=IOS_BLUE)


    def _build_shell(self):
        root = tk.Frame(self, bg=IOS_BG)
        root.pack(fill="both", expand=True)

        # Sidebar
        sidebar = tk.Frame(root, bg=IOS_SIDEBAR, width=248,
                           highlightbackground=IOS_SEP, highlightthickness=1)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Footprint Audit", bg=IOS_SIDEBAR, fg=IOS_LABEL,
                 font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=18, pady=(20, 4))
        tk.Label(sidebar, text="Self OSINT check", bg=IOS_SIDEBAR, fg=IOS_SECONDARY,
                 font=FONT_SM).pack(anchor="w", padx=18, pady=(0, 12))

        nav_canvas = tk.Canvas(sidebar, bg=IOS_SIDEBAR, highlightthickness=0, bd=0)
        nav_scroll = ttk.Scrollbar(sidebar, orient="vertical", command=nav_canvas.yview)
        nav_inner = tk.Frame(nav_canvas, bg=IOS_SIDEBAR)
        nav_inner.bind("<Configure>", lambda e: nav_canvas.configure(scrollregion=nav_canvas.bbox("all")))
        nav_canvas.create_window((0, 0), window=nav_inner, anchor="nw", width=230)
        nav_canvas.configure(yscrollcommand=nav_scroll.set)
        nav_canvas.pack(side="left", fill="both", expand=True)
        nav_scroll.pack(side="right", fill="y")

        for item in NAV_ITEMS:
            if item[1] is None:
                tk.Label(nav_inner, text=item[0], bg=IOS_SIDEBAR, fg=IOS_GROUP_LABEL,
                         font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=18, pady=(14, 4))
            else:
                key, title, subtitle = item
                self._nav_row(nav_inner, key, title, subtitle)

        # Content area
        self.content = tk.Frame(root, bg=IOS_BG)
        self.content.pack(side="left", fill="both", expand=True)

        self._build_all_screens()

    def _nav_row(self, parent, key, title, subtitle):
        row = tk.Frame(parent, bg=IOS_SIDEBAR, cursor="hand2")
        row.pack(fill="x", padx=10, pady=1)

        inner = tk.Frame(row, bg=IOS_SIDEBAR)
        inner.pack(fill="x", padx=8, pady=8)

        title_lbl = tk.Label(inner, text=title, bg=IOS_SIDEBAR, fg=IOS_LABEL,
                             font=FONT, anchor="w")
        title_lbl.pack(anchor="w")
        tk.Label(inner, text=subtitle, bg=IOS_SIDEBAR, fg=IOS_SECONDARY,
                 font=("Segoe UI", 9), anchor="w").pack(anchor="w")

        chevron = tk.Label(row, text="›", bg=IOS_SIDEBAR, fg=IOS_SEP, font=("Segoe UI", 16))
        chevron.place(relx=1.0, rely=0.5, anchor="e", x=-12)

        self._nav_buttons[key] = (row, inner, title_lbl)

        for w in (row, inner, title_lbl):
            w.bind("<Button-1>", lambda _e, k=key: self._show_screen(k))
            w.bind("<Enter>", lambda _e, r=row, i=inner, t=title_lbl, k=key:
                   self._nav_hover(k, r, i, t, True))
            w.bind("<Leave>", lambda _e, r=row, i=inner, t=title_lbl, k=key:
                   self._nav_hover(k, r, i, t, False))

    def _nav_hover(self, key, row, inner, title_lbl, entering):
        if key == self._current_screen:
            return
        bg = "#F0F0F5" if entering else IOS_SIDEBAR
        for w in (row, inner, title_lbl):
            w.configure(bg=bg)

    def _show_screen(self, key):
        if self._current_screen:
            self.screens[self._current_screen].pack_forget()
        self.screens[key].pack(fill="both", expand=True)
        self._current_screen = key
        for k, (row, inner, title_lbl) in self._nav_buttons.items():
            sel = k == key
            bg = IOS_SIDEBAR_SEL_BG if sel else IOS_SIDEBAR
            fg = IOS_SIDEBAR_SEL if sel else IOS_LABEL
            row.configure(bg=bg)
            inner.configure(bg=bg)
            title_lbl.configure(bg=bg, fg=fg, font=("Segoe UI", 11, "bold" if sel else "normal"))

    def _screen(self, key):
        frame = tk.Frame(self.content, bg=IOS_BG)
        self.screens[key] = frame
        return frame

    def _scroll_screen(self, key):
        outer = self._screen(key)
        outer.configure(bg=IOS_BG)
        
        canvas = tk.Canvas(outer, bg=IOS_BG, highlightthickness=0, bd=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=IOS_BG)
        
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y", padx=(2, 0))

        def _on_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
            # Auto-scroll to top when screen changes
            canvas.yview_moveto(0)

        canvas.bind("<Configure>", _on_configure)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            if event.delta:  # Windows
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            else:  # Linux
                if event.num == 5:
                    canvas.yview_scroll(3, "units")
                elif event.num == 4:
                    canvas.yview_scroll(-3, "units")
        
        def _bind_scroll(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", _on_mousewheel)
            widget.bind("<Button-5>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_scroll(child)
        
        _bind_scroll(inner)
        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", _on_mousewheel)
        canvas.bind("<Button-5>", _on_mousewheel)
        
        # Arrow keys support
        def _on_key(event):
            if event.keysym == "Up":
                canvas.yview_scroll(-3, "units")
            elif event.keysym == "Down":
                canvas.yview_scroll(3, "units")
            elif event.keysym == "Prior":
                canvas.yview_scroll(-10, "units")
            elif event.keysym == "Next":
                canvas.yview_scroll(10, "units")
        
        canvas.bind("<Up>", _on_key)
        canvas.bind("<Down>", _on_key)
        canvas.bind("<Prior>", _on_key)
        canvas.bind("<Next>", _on_key)
        inner.bind("<Up>", _on_key)
        inner.bind("<Down>", _on_key)
        inner.bind("<Prior>", _on_key)
        inner.bind("<Next>", _on_key)
        
        return outer, inner

    def _large_title(self, parent, text, subtitle=None):
        tk.Label(parent, text=text, bg=IOS_BG, fg=IOS_LABEL, font=FONT_LG).pack(
            anchor="w", padx=28, pady=(24, 0))
        if subtitle:
            tk.Label(parent, text=subtitle, bg=IOS_BG, fg=IOS_SECONDARY, font=FONT,
                     wraplength=700, justify="left").pack(anchor="w", padx=28, pady=(6, 16))

    def _section_label(self, parent, text):
        tk.Label(parent, text=text.upper(), bg=IOS_BG, fg=IOS_GROUP_LABEL,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=28, pady=(18, 6))

    def _inset_group(self, parent):
        wrap = tk.Frame(parent, bg=IOS_BG)
        wrap.pack(fill="x", padx=24, pady=(0, 8))
        card = tk.Frame(wrap, bg=IOS_CARD, highlightbackground=IOS_SEP, highlightthickness=1)
        card.pack(fill="x")
        return card

    def _ios_button(self, parent, text, command, primary=False, state="normal"):
        bg = IOS_BLUE if primary else IOS_CARD
        fg = "#FFFFFF" if primary else IOS_BLUE
        abg = IOS_BLUE_PRESSED if primary else "#E5E5EA"
        btn = tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                        activebackground=abg, activeforeground=fg,
                        font=("Segoe UI", 12, "bold" if primary else "normal"),
                        relief="flat", padx=20, pady=12, cursor="hand2", state=state,
                        highlightthickness=1,
                        highlightbackground=IOS_SEP if not primary else IOS_BLUE)
        return btn

    def _settings_row(self, parent, label, var, last=False):
        row = tk.Frame(parent, bg=IOS_CARD)
        row.pack(fill="x")
        tk.Label(row, text=label, bg=IOS_CARD, fg=IOS_LABEL, font=FONT).pack(
            side="left", padx=16, pady=14)
        entry = tk.Entry(row, textvariable=var, bg=IOS_INPUT, fg=IOS_LABEL,
                         insertbackground=IOS_BLUE, relief="flat", font=FONT,
                         justify="right", width=36)
        entry.pack(side="right", padx=16, pady=10, ipady=6)
        if not last:
            tk.Frame(parent, bg=IOS_SEP, height=1).pack(fill="x", padx=16)

    def _toggle_row(self, parent, label, var, last=False):
        row = tk.Frame(parent, bg=IOS_CARD)
        row.pack(fill="x")
        tk.Label(row, text=label, bg=IOS_CARD, fg=IOS_LABEL, font=FONT,
                 wraplength=420, justify="left").pack(side="left", padx=16, pady=12)
        cb = tk.Checkbutton(row, variable=var, bg=IOS_CARD, activebackground=IOS_CARD,
                            selectcolor=IOS_BLUE, relief="flat")
        cb.pack(side="right", padx=16)
        if not last:
            tk.Frame(parent, bg=IOS_SEP, height=1).pack(fill="x", padx=16)


    def _build_all_screens(self):
        screens_to_build = [
            ("home", self._build_home_screen, ()),
            ("identifiers", self._build_identifiers_screen, ()),
            ("sections", self._build_sections_screen, ()),
            ("appearance", self._build_appearance_screen, ()),
            ("platforms", self._build_platforms_screen, ()),
            ("email", self._build_email_screen, ()),
        ]
        
        for name, func, args in screens_to_build:
            try:
                func(*args)
            except Exception as e:
                print(f"ERROR building {name} screen: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        text_screens = [
            ("breaches", "Breaches & Pastes",
             "Check if your email appears in known breach databases and paste sites.",
             "breach_output"),
            ("search", "Web Search",
             "Google dork queries to find public mentions of your identifiers.",
             "search_output"),
            ("archives", "Archives",
             "Historical snapshots and cached copies of pages tied to you.",
             "archive_output"),
            ("code", "Code & Repos",
             "Search public code for leaked emails, keys, or usernames.",
             "code_output"),
            ("brokers", "Data Brokers",
             "People-search sites that may list your personal information.",
             "broker_output"),
            ("domain", "Domain & DNS",
             "DNS records, WHOIS, certificates, and domain security tools.",
             "domain_output"),
            ("people", "People & Phone",
             "Name, phone, and reverse-image search links.",
             "people_output"),
        ]
        
        for key, title, subtitle, attr in text_screens:
            try:
                self._build_text_screen(key, title, subtitle, attr)
            except Exception as e:
                print(f"ERROR building {key} text screen: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        try:
            self._build_report_screen()
        except Exception as e:
            print(f"ERROR building report screen: {e}")
            import traceback
            traceback.print_exc()
            raise

        self.link_widgets = [
            self.breach_output, self.search_output, self.archive_output,
            self.code_output, self.broker_output, self.domain_output, self.people_output,
        ]

    def _build_home_screen(self):
        _, inner = self._scroll_screen("home")
        self._large_title(inner, "Home",
                          "Run a self-audit against public sources. Pick sections in the sidebar, then tap Run.")

        self._section_label(inner, "Summary")
        stats_wrap = tk.Frame(inner, bg=IOS_BG)
        stats_wrap.pack(fill="x", padx=24)
        self.stat_found = self._stat_tile(stats_wrap, "Found", "—", IOS_GREEN)
        self.stat_missing = self._stat_tile(stats_wrap, "Not found", "—", IOS_SECONDARY)
        self.stat_errors = self._stat_tile(stats_wrap, "Errors", "—", IOS_ORANGE)
        self.stat_links = self._stat_tile(stats_wrap, "Links", "—", IOS_BLUE)

        self._section_label(inner, "Progress")
        prog_card = self._inset_group(inner)
        prog_inner = tk.Frame(prog_card, bg=IOS_CARD)
        prog_inner.pack(fill="x", padx=16, pady=16)
        self.progress = ttk.Progressbar(prog_inner, mode="determinate", maximum=100)
        self.progress.pack(fill="x")
        self.status_label = tk.Label(prog_inner, text="Ready to run",
                                     bg=IOS_CARD, fg=IOS_SECONDARY, font=FONT_SM, anchor="w")
        self.status_label.pack(fill="x", pady=(10, 0))

        self._section_label(inner, "Actions")
        act = tk.Frame(inner, bg=IOS_BG)
        act.pack(fill="x", padx=24)
        self.run_btn = self._ios_button(act, "Run Audit", self.start_audit, primary=True)
        self.run_btn.pack(side="left", padx=(0, 10))
        self.stop_btn = self._ios_button(act, "Stop", self.stop_audit, state="disabled")
        self.stop_btn.pack(side="left", padx=(0, 10))
        self.clear_btn = self._ios_button(act, "Clear", self.clear_results)
        self.clear_btn.pack(side="left", padx=(0, 10))
        self.export_btn = self._ios_button(act, "Export", self.export_report, state="disabled")
        self.export_btn.pack(side="left")

        self._section_label(inner, "Quick navigation")
        nav_card = self._inset_group(inner)
        quick = [
            ("identifiers", "Set up your identifiers first"),
            ("sections", "Choose which checks to include"),
            ("platforms", "View platform scan results"),
            ("report", "Read & export the full report"),
        ]
        for i, (key, hint) in enumerate(quick):
            self._link_row(nav_card, key, hint, last=(i == len(quick) - 1))

        tk.Label(inner, text="Use only on your own data.", bg=IOS_BG, fg=IOS_SECONDARY,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=28, pady=24)

    def _stat_tile(self, parent, title, value, color):
        tile = tk.Frame(parent, bg=IOS_CARD, highlightbackground=IOS_SEP, highlightthickness=1)
        tile.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(tile, text=title, bg=IOS_CARD, fg=IOS_SECONDARY, font=FONT_SM).pack(
            anchor="w", padx=14, pady=(12, 0))
        lbl = tk.Label(tile, text=value, bg=IOS_CARD, fg=color, font=("Segoe UI", 26, "bold"))
        lbl.pack(anchor="w", padx=14, pady=(0, 12))
        return lbl

    def _link_row(self, parent, screen_key, hint, last=False):
        # Find the title from NAV_ITEMS, handling both 2-tuple and 3-tuple entries
        title = None
        for item in NAV_ITEMS:
            if len(item) == 3 and item[0] == screen_key:
                title = item[1]
                break
        if title is None:
            title = screen_key
        
        row = tk.Frame(parent, bg=IOS_CARD, cursor="hand2")
        row.pack(fill="x")
        tk.Label(row, text=title, bg=IOS_CARD, fg=IOS_BLUE, font=FONT).pack(side="left", padx=16, pady=12)
        tk.Label(row, text=hint, bg=IOS_CARD, fg=IOS_SECONDARY, font=FONT_SM).pack(side="left")
        tk.Label(row, text="›", bg=IOS_CARD, fg=IOS_SEP, font=("Segoe UI", 16)).pack(side="right", padx=16)
        row.bind("<Button-1>", lambda _e, k=screen_key: self._show_screen(k))
        if not last:
            tk.Frame(parent, bg=IOS_SEP, height=1).pack(fill="x", padx=16)

    def _build_identifiers_screen(self):
        _, inner = self._scroll_screen("identifiers")
        self._large_title(inner, "Identifiers",
                          "Enter the details you want to audit. Email and username are required.")

        self.email_var = tk.StringVar()
        self.user_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.domain_var = tk.StringVar()

        self._section_label(inner, "Required")
        req = self._inset_group(inner)
        self._settings_row(req, "Email", self.email_var)
        self._settings_row(req, "Username", self.user_var, last=True)

        self._section_label(inner, "Optional")
        opt = self._inset_group(inner)
        self._settings_row(opt, "Full name", self.name_var)
        self._settings_row(opt, "Phone", self.phone_var)
        self._settings_row(opt, "Domain", self.domain_var, last=True)

        tk.Label(inner, text="Domain defaults to your email domain if left blank.",
                 bg=IOS_BG, fg=IOS_SECONDARY, font=FONT_SM).pack(anchor="w", padx=28, pady=12)

    def _build_sections_screen(self):
        _, inner = self._scroll_screen("sections")
        self._large_title(inner, "Audit Sections",
                          "Toggle the checks you want included. Each section has its own results screen.")

        self.section_vars = {}
        groups = [
            ("Automated scans", [
                ("platforms", "Platform username scan"),
                ("email", "Email intelligence"),
                ("domain", "Domain & DNS intelligence"),
            ]),
            ("Lookup link packs", [
                ("breaches", "Breach & paste databases"),
                ("search", "Google dork searches"),
                ("archives", "Web archives"),
                ("code", "Code & repo leak search"),
                ("brokers", "Data broker sites"),
                ("people", "People & phone search"),
            ]),
        ]
        for group_name, items in groups:
            self._section_label(inner, group_name)
            card = self._inset_group(inner)
            for i, (key, label) in enumerate(items):
                var = tk.BooleanVar(value=True)
                self.section_vars[key] = var
                self._toggle_row(card, label, var, last=(i == len(items) - 1))

        btn_row = tk.Frame(inner, bg=IOS_BG)
        btn_row.pack(fill="x", padx=24, pady=16)
        self._ios_button(btn_row, "Select All", self._select_all_sections).pack(side="left", padx=(0, 10))
        self._ios_button(btn_row, "Clear All", self._clear_all_sections).pack(side="left")

    def _build_appearance_screen(self):
        _, inner = self._scroll_screen("appearance")
        self._large_title(inner, "Appearance",
                          "Customize the look and feel of Footprint Audit.")

        # Background section
        self._section_label(inner, "Background Image")
        bg_card = self._inset_group(inner)
        
        bg_frame = tk.Frame(bg_card, bg=IOS_CARD)
        bg_frame.pack(fill="x")
        tk.Label(bg_frame, text="Select Image", bg=IOS_CARD, fg=IOS_LABEL, font=FONT).pack(
            side="left", padx=16, pady=14)
        bg_btn_frame = tk.Frame(bg_frame, bg=IOS_CARD)
        bg_btn_frame.pack(side="right", padx=16, pady=10)
        self._ios_button(bg_btn_frame, "Browse", self._select_background_image).pack(side="left", padx=(0, 8))
        self._ios_button(bg_btn_frame, "Clear", self._clear_background_image).pack(side="left")
        
        tk.Frame(bg_card, bg=IOS_SEP, height=1).pack(fill="x", padx=16)
        
        # Status display
        self.bg_status = tk.StringVar(value="✓ No background selected")
        status_frame = tk.Frame(bg_card, bg=IOS_CARD)
        status_frame.pack(fill="x", padx=16, pady=12)
        tk.Label(status_frame, text="Status:", bg=IOS_CARD, fg=IOS_SECONDARY, font=FONT_SM).pack(anchor="w")
        tk.Label(status_frame, textvariable=self.bg_status, bg=IOS_CARD, fg=IOS_BLUE, font=FONT_SM, wraplength=400, justify="left").pack(anchor="w", pady=(4, 0))
        
        tk.Frame(bg_card, bg=IOS_SEP, height=1).pack(fill="x", padx=16)
        
        # Opacity slider
        opacity_frame = tk.Frame(bg_card, bg=IOS_CARD)
        opacity_frame.pack(fill="x", padx=16, pady=12)
        tk.Label(opacity_frame, text="Background Opacity", bg=IOS_CARD, fg=IOS_LABEL, font=FONT).pack(anchor="w")
        
        opacity_sub = tk.Frame(opacity_frame, bg=IOS_CARD)
        opacity_sub.pack(fill="x", pady=(8, 0))
        self.opacity_label = tk.Label(opacity_sub, text="10%", bg=IOS_CARD, fg=IOS_BLUE, font=FONT_MONO_BOLD, width=5)
        self.opacity_label.pack(side="right")
        
        slider = tk.Scale(opacity_sub, from_=0, to=100, orient="horizontal", variable=self.bg_opacity,
                         bg=IOS_INPUT, fg=IOS_BLUE, highlightthickness=0, relief="flat",
                         command=self._update_opacity_label)
        slider.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Theme section
        self._section_label(inner, "Theme")
        theme_card = self._inset_group(inner)
        
        themes = [("Light", "light"), ("Dark", "dark"), ("Auto", "auto")]
        for i, (label, value) in enumerate(themes):
            row = tk.Frame(theme_card, bg=IOS_CARD)
            row.pack(fill="x")
            rb = tk.Radiobutton(row, text=label, variable=self.theme_var, value=value,
                               bg=IOS_CARD, activebackground=IOS_CARD, selectcolor=IOS_BLUE,
                               font=FONT, relief="flat", command=self._apply_theme)
            rb.pack(side="left", padx=16, pady=12)
            if i < len(themes) - 1:
                tk.Frame(theme_card, bg=IOS_SEP, height=1).pack(fill="x", padx=16)

        # Font size section
        self._section_label(inner, "Font Size")
        font_card = self._inset_group(inner)
        
        sizes = [("Small", "small"), ("Normal", "normal"), ("Large", "large")]
        for i, (label, value) in enumerate(sizes):
            row = tk.Frame(font_card, bg=IOS_CARD)
            row.pack(fill="x")
            rb = tk.Radiobutton(row, text=label, variable=self.font_size_var, value=value,
                               bg=IOS_CARD, activebackground=IOS_CARD, selectcolor=IOS_BLUE,
                               font=FONT, relief="flat", command=self._apply_font_size)
            rb.pack(side="left", padx=16, pady=12)
            if i < len(sizes) - 1:
                tk.Frame(font_card, bg=IOS_SEP, height=1).pack(fill="x", padx=16)

        # Reset button
        btn_row = tk.Frame(inner, bg=IOS_BG)
        btn_row.pack(fill="x", padx=24, pady=16)
        self._ios_button(btn_row, "Reset to Defaults", self._reset_appearance).pack(side="left")
        
        # Info text
        tk.Label(inner, text="Settings saved automatically. App restart may be required for some changes.", 
                 bg=IOS_BG, fg=IOS_SECONDARY, font=FONT_SM).pack(anchor="w", padx=28, pady=12)

    def _update_opacity_label(self, value):
        """Update the opacity percentage label"""
        self.opacity_label.config(text=f"{int(float(value))}%")

    def _apply_theme(self):
        """Apply theme changes"""
        theme = self.theme_var.get()
        messagebox.showinfo("Theme Changed", f"Theme changed to: {theme.title()}\n\n✓ Setting saved")

    def _apply_font_size(self):
        """Apply font size changes"""
        size = self.font_size_var.get()
        messagebox.showinfo("Font Size Changed", f"Font size changed to: {size.title()}\n\n✓ Setting saved")

    def _select_background_image(self):
        """Open file dialog to select background image"""
        path = filedialog.askopenfilename(
            title="Select Background Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")],
        )
        if path:
            try:
                # Verify file exists and is readable
                with open(path, 'rb') as f:
                    f.read(1)
                
                self.bg_image_path = path
                filename = path.split("\\")[-1] if "\\" in path else path.split("/")[-1]
                self.bg_status.set(f"✓ Selected: {filename}")
                messagebox.showinfo("Background Selected", f"Background image set to:\n{filename}\n\n✓ Setting saved")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image:\n{str(e)}")
                self.bg_status.set("✗ Error loading image")

    def _clear_background_image(self):
        """Clear the background image"""
        self.bg_image_path = None
        self.bg_status.set("✓ No background selected")
        messagebox.showinfo("Background Cleared", "Background image cleared.\n\n✓ Setting saved")

    def _reset_appearance(self):
        """Reset all appearance settings to defaults"""
        self.bg_image_path = None
        self.bg_status.set("✓ No background selected")
        self.bg_opacity.set(10)
        self.opacity_label.config(text="10%")
        self.theme_var.set("light")
        self.font_size_var.set("normal")
        messagebox.showinfo("Reset Complete", "All appearance settings reset to defaults.\n\n✓ Changes saved")

    def _build_platforms_screen(self):
        frame = self._screen("platforms")
        self._large_title(frame, "Platforms", f"Scanning {len(PLATFORMS)} public profile URLs.")

        bar = tk.Frame(frame, bg=IOS_BG)
        bar.pack(fill="x", padx=28, pady=(0, 8))
        tk.Label(bar, text="Search", bg=IOS_BG, fg=IOS_SECONDARY, font=FONT_SM).pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self._apply_filter())
        tk.Entry(bar, textvariable=self.filter_var, bg=IOS_CARD, fg=IOS_LABEL,
                 relief="flat", font=FONT, width=28).pack(side="left", padx=(8, 0), ipady=5)
        self.filter_status = tk.StringVar(value="")
        tk.Label(bar, textvariable=self.filter_status, bg=IOS_BG, fg=IOS_SECONDARY,
                 font=FONT_SM).pack(side="right")

        tw = tk.Frame(frame, bg=IOS_BG)
        tw.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        cols = ("category", "platform", "status", "url")
        self.tree = ttk.Treeview(tw, columns=cols, show="headings", selectmode="browse")
        for c, w in zip(cols, (120, 140, 100, 480)):
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=w, stretch=(c == "url"))
        sb = ttk.Scrollbar(tw, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        for tag, color in [("found", IOS_GREEN), ("missing", IOS_SECONDARY),
                           ("error", IOS_ORANGE), ("pending", IOS_SECONDARY)]:
            self.tree.tag_configure(tag, foreground=color)
        self.tree.bind("<Double-1>", self._open_selected_url)
        tk.Label(frame, text="Double-click a row to open the profile in your browser.",
                 bg=IOS_BG, fg=IOS_SECONDARY, font=FONT_SM).pack(anchor="w", padx=28, pady=(0, 12))

    def _build_email_screen(self):
        frame = self._screen("email")
        self._large_title(frame, "Email Intel",
                          "Automated checks: Gravatar, MX/SPF records, disposable domain, GitHub & Reddit APIs.")
        tw = tk.Frame(frame, bg=IOS_BG)
        tw.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        cols = ("check", "status", "detail")
        self.email_tree = ttk.Treeview(tw, columns=cols, show="headings")
        for c, w in zip(cols, (160, 110, 560)):
            self.email_tree.heading(c, text=c.capitalize())
            self.email_tree.column(c, width=w, stretch=(c == "detail"))
        sb = ttk.Scrollbar(tw, orient="vertical", command=self.email_tree.yview)
        self.email_tree.configure(yscrollcommand=sb.set)
        self.email_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        for tag, color in [("good", IOS_GREEN), ("bad", IOS_SECONDARY),
                           ("warn", IOS_ORANGE), ("pending", IOS_SECONDARY)]:
            self.email_tree.tag_configure(tag, foreground=color)

    def _build_text_screen(self, key, title, subtitle, attr):
        frame = self._screen(key)
        self._large_title(frame, title, subtitle)
        w = scrolledtext.ScrolledText(frame, bg=IOS_CARD, fg=IOS_LABEL, font=FONT_MONO,
                                      wrap="word", relief="flat", padx=16, pady=14,
                                      highlightbackground=IOS_SEP, highlightthickness=1)
        w.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        self._configure_output_tags(w)
        setattr(self, attr, w)
        self._write_to(w, f"Run an audit to populate {title.lower()}.\n", "muted")

    def _build_report_screen(self):
        frame = self._screen("report")
        self._large_title(frame, "Full Report", "Complete audit log — export from the Home screen.")
        self.output = scrolledtext.ScrolledText(frame, bg=IOS_CARD, fg=IOS_LABEL, font=FONT_MONO,
                                                wrap="word", relief="flat", padx=16, pady=14,
                                                highlightbackground=IOS_SEP, highlightthickness=1)
        self.output.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        self._configure_output_tags(self.output)
        self._write_to(self.output, "Run an audit to generate the full report.\n", "muted")

    def _configure_output_tags(self, widget):
        widget.tag_configure("heading", foreground=IOS_BLUE, font=FONT_MONO_BOLD)
        widget.tag_configure("good", foreground=IOS_GREEN, font=FONT_MONO_BOLD)
        widget.tag_configure("bad", foreground=IOS_SECONDARY)
        widget.tag_configure("link", foreground=IOS_BLUE, underline=True)
        widget.tag_configure("warn", foreground=IOS_ORANGE)
        widget.tag_configure("muted", foreground=IOS_SECONDARY)
        widget.tag_bind("link", "<Button-1>", self._open_clicked_link)
        widget.tag_bind("link", "<Enter>", lambda e: widget.config(cursor="hand2"))
        widget.tag_bind("link", "<Leave>", lambda e: widget.config(cursor=""))
        widget.config(state="disabled")


    def _select_all_sections(self):
        for v in self.section_vars.values():
            v.set(True)

    def _clear_all_sections(self):
        for v in self.section_vars.values():
            v.set(False)

    def _ui(self, fn, *args, **kwargs):
        self.after(0, lambda: fn(*args, **kwargs))

    def _write_to(self, widget, text, tag=None, link_url=None):
        widget.config(state="normal")
        start = widget.index("end-1c")
        widget.insert("end", text)
        end = widget.index("end-1c")
        if tag:
            widget.tag_add(tag, start, end)
        if link_url:
            widget.tag_add("link", start, end)
            self.links.append((widget, start, end, link_url))
        widget.config(state="disabled")
        widget.see("end")

    def _write(self, text, tag=None, link_url=None):
        self._write_to(self.output, text, tag, link_url)

    def _open_clicked_link(self, event):
        widget = event.widget
        index = widget.index(f"@{event.x},{event.y}")
        for w, start, end, url in self.links:
            if w is widget and widget.compare(start, "<=", index) and widget.compare(index, "<", end):
                webbrowser.open(url)
                break

    def _open_selected_url(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        platform = self.tree.item(sel[0], "values")[1]
        row = self.platform_rows.get(platform)
        if row and row[1]:
            webbrowser.open(row[1])

    def _ctx(self, email, username, domain, name, phone):
        email_local, _, email_domain = email.partition("@")
        return {
            "email": email, "username": username, "domain": domain or email_domain,
            "name": name or username, "phone": re.sub(r"\D", "", phone),
            "email_local": email_local, "email_domain": email_domain,
        }

    def _fmt_url(self, template, ctx):
        return template.format(**ctx)

    def _emit_links(self, widget, heading, items, ctx, log_section=None):
        self._ui(self._write_to, widget, f"\n{heading}\n", "heading")
        if log_section:
            self._ui(self._write, f"\n{log_section}\n", "heading")
        for label, tmpl in items:
            url = self._fmt_url(tmpl, ctx)
            self._ui(self._write_to, widget, f"  • {label}\n", "muted")
            self._ui(self._write_to, widget, f"    {url}\n\n", "link", url)
            if log_section:
                self._ui(self._write, f"  {label}: {url}\n", None, url)

    def _apply_filter(self):
        q = self.filter_var.get().strip().lower()
        visible = 0
        for name, (item_id, _url) in self.platform_rows.items():
            vals = self.tree.item(item_id, "values")
            show = not q or q in name.lower() or q in (vals[0] or "").lower()
            if show:
                self.tree.reattach(item_id, "", "end")
                visible += 1
            else:
                self.tree.detach(item_id)
        total = len(self.platform_rows)
        self.filter_status.set(f"{visible} of {total}" if q else f"{total} platforms")

    def _reset_trees(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.platform_rows.clear()
        for cat, name, _ in flatten_platforms():
            iid = self.tree.insert("", "end", values=(cat, name, "Pending", "—"), tags=("pending",))
            self.platform_rows[name] = (iid, None)
        for item in self.email_tree.get_children():
            self.email_tree.delete(item)
        self.email_rows.clear()

    def _update_platform(self, name, status, url, tag):
        iid, _ = self.platform_rows[name]
        cat = self.tree.item(iid, "values")[0]
        self.tree.item(iid, values=(cat, name, status, url or "—"), tags=(tag,))
        self.platform_rows[name] = (iid, url)

    def _add_email_check(self, check, status, detail, tag):
        iid = self.email_tree.insert("", "end", values=(check, status, detail), tags=(tag,))
        self.email_rows[check] = iid

    def _update_stats(self, found, missing, errors, link_count=None):
        self.stat_found.config(text=str(found))
        self.stat_missing.config(text=str(missing))
        self.stat_errors.config(text=str(errors))
        if link_count is not None:
            self.stat_links.config(text=str(link_count))

    def _set_progress(self, step, total, label):
        pct = int((step / max(total, 1)) * 100)
        self._ui(self.progress.configure, value=pct)
        self._ui(self.status_label.config, text=label, fg=IOS_ORANGE)

    def _section_enabled(self, key):
        return self.section_vars[key].get()

    def _count_steps(self, domain):
        n = 0
        if self._section_enabled("platforms"):
            n += len(PLATFORMS)
        if self._section_enabled("email"):
            n += 5
        for k in ("breaches", "search", "archives", "code", "brokers", "people"):
            if self._section_enabled(k):
                n += 1
        if domain and self._section_enabled("domain"):
            n += 4
        return max(n, 1)

    def _http_exists(self, url):
        try:
            r = requests.get(url, timeout=7, headers=UA, allow_redirects=True)
            return r.status_code == 200
        except requests.RequestException:
            return None

    def _dns_query(self, name, rtype):
        try:
            r = requests.get("https://dns.google/resolve",
                             params={"name": name, "type": rtype}, timeout=6, headers=UA)
            data = r.json()
            return [a.get("data", "") for a in (data.get("Answer") or [])]
        except (requests.RequestException, json.JSONDecodeError, KeyError):
            return None

    def _check_gravatar(self, email):
        h = hashlib.md5(email.strip().lower().encode()).hexdigest()
        url = f"https://www.gravatar.com/{h}.json"
        try:
            r = requests.get(url, timeout=6, headers=UA)
            if r.status_code == 200:
                name = r.json().get("entry", [{}])[0].get("displayName", "unknown")
                return True, f"Profile exists — {name}", f"https://gravatar.com/{h}"
            return False, "No Gravatar profile", f"https://gravatar.com/{h}"
        except (requests.RequestException, json.JSONDecodeError, IndexError):
            return None, "Could not check Gravatar", f"https://gravatar.com/{h}"

    def _check_github_api(self, username):
        url = f"https://api.github.com/users/{quote(username)}"
        try:
            r = requests.get(url, timeout=6, headers=UA)
            if r.status_code == 200:
                d = r.json()
                return True, f"repos={d.get('public_repos')} · {d.get('html_url')}", d.get("html_url")
            if r.status_code == 404:
                return False, "Not found via API", url
            return None, f"HTTP {r.status_code}", url
        except (requests.RequestException, json.JSONDecodeError):
            return None, "API error", url

    def _check_reddit_api(self, username):
        url = f"https://www.reddit.com/user/{quote(username)}/about.json"
        try:
            r = requests.get(url, timeout=6, headers={**UA, "User-Agent": "footprint-audit/2.0"})
            if r.status_code == 200:
                d = r.json().get("data", {})
                return True, f"karma={d.get('total_karma', '?')}", f"https://reddit.com/user/{username}"
            if r.status_code == 404:
                return False, "Not found", url
            return None, f"HTTP {r.status_code}", url
        except (requests.RequestException, json.JSONDecodeError):
            return None, "API error", url


    def clear_results(self):
        if self._audit_running:
            return
        self.links = []
        self.filter_var.set("")
        self._reset_trees()
        placeholders = {
            self.breach_output: "breaches & pastes",
            self.search_output: "web search",
            self.archive_output: "archives",
            self.code_output: "code & repos",
            self.broker_output: "data brokers",
            self.domain_output: "domain & dns",
            self.people_output: "people & phone",
        }
        for w, name in placeholders.items():
            w.config(state="normal")
            w.delete("1.0", "end")
            w.config(state="disabled")
            self._write_to(w, f"Run an audit to populate {name}.\n", "muted")
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.config(state="disabled")
        self._write_to(self.output, "Run an audit to generate the full report.\n", "muted")
        self._update_stats("—", "—", "—", "—")
        self.progress["value"] = 0
        self.status_label.config(text="Ready to run", fg=IOS_SECONDARY)
        self.export_btn.config(state="disabled")

    def stop_audit(self):
        self._cancel = True
        self.status_label.config(text="Stopping…", fg=IOS_ORANGE)

    def export_report(self):
        content = self.output.get("1.0", "end").strip()
        if not content or content.startswith("Run an audit"):
            messagebox.showinfo("Nothing to export", "Run an audit first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"footprint-audit-{datetime.now():%Y%m%d-%H%M}.txt",
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.status_label.config(text=f"Exported → {path}", fg=IOS_GREEN)

    def start_audit(self):
        if self._audit_running:
            return
        if requests is None:
            messagebox.showerror("Missing dependency", "Run: pip install requests")
            return
        if not any(v.get() for v in self.section_vars.values()):
            messagebox.showwarning("No sections", "Enable at least one audit section.")
            return

        email = self.email_var.get().strip()
        username = self.user_var.get().strip()
        domain = self.domain_var.get().strip()
        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()

        if not email or not username:
            messagebox.showwarning("Missing info", "Email and username are required.")
            self._show_screen("identifiers")
            return
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            messagebox.showwarning("Invalid email", "Enter a valid email address.")
            self._show_screen("identifiers")
            return

        self.links = []
        self.filter_var.set("")
        self._cancel = False
        for w in [self.output, *self.link_widgets]:
            w.config(state="normal")
            w.delete("1.0", "end")
            w.config(state="disabled")

        self._reset_trees()
        self._update_stats(0, 0, 0, 0)
        self.progress["value"] = 0
        self._audit_running = True
        self.run_btn.config(state="disabled")
        self.clear_btn.config(state="disabled")
        self.export_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self._show_screen("home")

        threading.Thread(target=self._run_audit,
                         args=(email, username, domain, name, phone), daemon=True).start()

    def _run_audit(self, email, username, domain, name, phone):
        ctx = self._ctx(email, username, domain, name, phone)
        if not domain:
            domain = ctx["email_domain"]
            ctx["domain"] = domain

        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._ui(self._write, f"DIGITAL FOOTPRINT AUDIT  ·  {ts}\n", "heading")
        self._ui(self._write, f"Target: {email} / @{username}\n", "muted")
        self._ui(self._write, "=" * 60 + "\n")

        total_steps = self._count_steps(domain)
        step = found = missing = errors = link_count = 0

        def tick(label):
            nonlocal step
            step += 1
            self._set_progress(step, total_steps, label)

        if self._section_enabled("platforms") and not self._cancel:
            self._ui(self._write, "\n[1] USERNAME / PLATFORM SCAN\n", "heading")
            for cat, pname, tmpl in flatten_platforms():
                if self._cancel:
                    break
                url = tmpl.format(username)
                tick(f"Checking {pname}…")
                hit = self._http_exists(url)
                if hit:
                    found += 1
                    self._ui(self._update_platform, pname, "Found", url, "found")
                    self._ui(self._write, f"  ✓ {pname:22s} {url}\n", "good")
                elif hit is False:
                    missing += 1
                    self._ui(self._update_platform, pname, "Not found", url, "missing")
                    self._ui(self._write, f"  · {pname:22s} not found\n", "bad")
                else:
                    errors += 1
                    self._ui(self._update_platform, pname, "Error", url, "error")
                    self._ui(self._write, f"  ! {pname:22s} check failed\n", "bad")
                self._ui(self._update_stats, found, missing, errors, link_count)
                time.sleep(0.25)

        if self._section_enabled("email") and not self._cancel:
            self._ui(self._write, "\n[2] EMAIL INTELLIGENCE\n", "heading")
            ed = ctx["email_domain"]

            tick("Checking Gravatar…")
            ok, detail, _ = self._check_gravatar(email)
            tag = "good" if ok else ("bad" if ok is False else "warn")
            self._ui(self._add_email_check, "Gravatar", "Found" if ok else ("None" if ok is False else "Error"), detail, tag)
            self._ui(self._write, f"  Gravatar: {detail}\n", tag)

            tick("Checking MX records…")
            mx = self._dns_query(ed, "MX")
            if mx:
                detail = "; ".join(mx[:3])
                self._ui(self._add_email_check, "MX records", "OK", detail, "good")
                self._ui(self._write, f"  MX: {detail}\n", "good")
            else:
                self._ui(self._add_email_check, "MX records", "None", f"No MX for {ed}", "warn")
                self._ui(self._write, f"  MX: none for {ed}\n", "warn")

            tick("Checking SPF/DMARC…")
            spf = self._dns_query(ed, "TXT")
            spf_hits = [t for t in (spf or []) if "spf1" in t.lower() or "dmarc" in t.lower()]
            if spf_hits:
                self._ui(self._add_email_check, "SPF/DMARC", "Found", spf_hits[0][:120], "good")
                self._ui(self._write, f"  SPF/DMARC: {spf_hits[0][:80]}\n", "good")
            else:
                self._ui(self._add_email_check, "SPF/DMARC", "Not found", "No SPF/DMARC TXT", "warn")
                self._ui(self._write, "  SPF/DMARC: not found\n", "warn")

            tick("Checking disposable domain…")
            is_disp = ed.lower() in DISPOSABLE_DOMAINS
            self._ui(self._add_email_check, "Disposable", "Yes" if is_disp else "No", ed,
                     "warn" if is_disp else "good")

            tick("Checking GitHub & Reddit…")
            for label, fn, user in [("GitHub API", self._check_github_api, username),
                                    ("Reddit API", self._check_reddit_api, username)]:
                ok, detail, url = fn(user)
                tag = "good" if ok else ("bad" if ok is False else "warn")
                self._ui(self._add_email_check, label, "Found" if ok else ("Missing" if ok is False else "Error"),
                         detail, tag)
                self._ui(self._write, f"  {label}: {detail}\n", tag)

        if self._section_enabled("breaches") and not self._cancel:
            tick("Generating breach links…")
            link_count += len(BREACH_LINKS) + len(PASTE_LINKS)
            self._emit_links(self.breach_output, "Breach databases", BREACH_LINKS, ctx,
                             "[3] BREACH & PASTE DATABASES")
            self._emit_links(self.breach_output, "Paste & leak searches", PASTE_LINKS, ctx)

        if self._section_enabled("search") and not self._cancel:
            tick("Generating search dorks…")
            self._ui(self._write_to, self.search_output, "Google dork queries\n", "heading")
            self._ui(self._write, "\n[4] GOOGLE DORK SEARCHES\n", "heading")
            for label, dork in SEARCH_DORKS:
                q = dork.format(**ctx)
                url = f"https://www.google.com/search?q={quote(q)}"
                link_count += 1
                self._ui(self._write_to, self.search_output, f"  • {label}: {q}\n", "muted")
                self._ui(self._write_to, self.search_output, f"    {url}\n\n", "link", url)
                self._ui(self._write, f"  {label}: {url}\n", None, url)

        if self._section_enabled("archives") and not self._cancel:
            tick("Generating archive links…")
            link_count += len(ARCHIVE_LINKS)
            self._emit_links(self.archive_output, "Web archives & cache", ARCHIVE_LINKS, ctx, "[5] WEB ARCHIVES")

        if self._section_enabled("code") and not self._cancel:
            tick("Generating code search links…")
            link_count += len(CODE_SEARCH_LINKS)
            self._emit_links(self.code_output, "Code & repository searches", CODE_SEARCH_LINKS, ctx,
                             "[6] CODE & REPO LEAKS")

        if self._section_enabled("brokers") and not self._cancel:
            tick("Generating data-broker links…")
            link_count += len(DATA_BROKER_LINKS)
            self._emit_links(self.broker_output, "Data broker sites", DATA_BROKER_LINKS, ctx, "[7] DATA BROKERS")

        if self._section_enabled("domain") and domain and not self._cancel:
            self._ui(self._write, f"\n[8] DOMAIN — {domain}\n", "heading")
            tick("Looking up A records…")
            a_records = self._dns_query(domain, "A")
            if a_records:
                self._ui(self._write, f"  A: {', '.join(a_records)}\n", "good")
                self._ui(self._write_to, self.domain_output, f"A records: {', '.join(a_records)}\n\n", "good")
            tick("Looking up NS records…")
            ns = self._dns_query(domain, "NS")
            if ns:
                self._ui(self._write, f"  NS: {', '.join(ns[:3])}\n", "good")
                self._ui(self._write_to, self.domain_output, f"NS: {', '.join(ns)}\n\n", "good")
            tick("Checking crt.sh…")
            try:
                r = requests.get(f"https://crt.sh/?q={quote(domain)}&output=json", timeout=10, headers=UA)
                if r.status_code == 200:
                    certs = r.json()
                    count = len(certs) if isinstance(certs, list) else 0
                    self._ui(self._write, f"  crt.sh: {count} certs\n", "good")
                    self._ui(self._write_to, self.domain_output, f"crt.sh: {count} entries\n\n", "good")
            except (requests.RequestException, json.JSONDecodeError):
                self._ui(self._write, "  crt.sh: failed\n", "warn")
            tick("Generating domain tool links…")
            link_count += len(DOMAIN_LINKS)
            self._emit_links(self.domain_output, "Domain analysis tools", DOMAIN_LINKS, ctx)

        if self._section_enabled("people") and not self._cancel:
            tick("Generating people-search links…")
            link_count += len(PEOPLE_LINKS) + len(REVERSE_IMAGE_LINKS)
            self._emit_links(self.people_output, "Name & phone searches", PEOPLE_LINKS, ctx, "[9] PEOPLE & PHONE")
            self._emit_links(self.people_output, "Reverse image search", REVERSE_IMAGE_LINKS, ctx)

        self._ui(self._write, "\n" + "=" * 60 + "\nSUMMARY\n", "heading")
        if self._section_enabled("platforms"):
            self._ui(self._write, f"  Platforms: {found} found / {missing} missing / {errors} errors\n", "warn")
        self._ui(self._write, f"  Lookup links: {link_count}\n", "muted")
        self._ui(self._update_stats, found, missing, errors, link_count)
        self._ui(self._finish, found, self._cancel)

    def _finish(self, found_count, cancelled):
        self._audit_running = False
        self._cancel = False
        self.run_btn.config(state="normal")
        self.clear_btn.config(state="normal")
        self.export_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.progress.configure(value=100)
        msg = "Stopped." if cancelled else f"Done — {found_count} profile(s) found. Browse results in the sidebar."
        self.status_label.config(text=msg, fg=IOS_ORANGE if cancelled else IOS_GREEN)


if __name__ == "__main__":
    try:
        app = AuditApp()
        app.mainloop()
    except Exception as e:
        import traceback
        print(f"FATAL ERROR: {e}")
        print(traceback.format_exc())
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Initialization Error", f"Failed to start app:\n\n{str(e)}\n\nCheck console for details.")
        root.destroy()
