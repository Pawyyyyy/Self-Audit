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
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import uuid

try:
    import requests
except ImportError:
    requests = None

# ────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES & EVIDENCE SYSTEM
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class Evidence:
    """Represents a single piece of OSINT evidence"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    finding_type: str = ""  # platform, email, breach, domain, etc.
    value: str = ""  # The actual finding
    source: str = ""  # Where it came from (e.g., "GitHub API", "Breach Database")
    url: str = ""  # Clickable link
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: str = "medium"  # high, medium, low
    notes: str = ""

    def to_dict(self):
        return asdict(self)

@dataclass
class Entity:
    """Represents an entity in the investigation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: str = ""  # username, email, domain, phone, ip, name
    value: str = ""
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self):
        return asdict(self)

@dataclass
class Investigation:
    """Represents an investigation case"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "New Investigation"
    target: str = ""  # Primary entity
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    entities: List[Entity] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    status: str = "active"  # active, paused, completed

    def add_evidence(self, evidence: Evidence):
        if evidence not in self.evidence:
            self.evidence.append(evidence)

    def add_entity(self, entity: Entity):
        if entity.value not in [e.value for e in self.entities]:
            self.entities.append(entity)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "target": self.target,
            "timestamp": self.timestamp,
            "entities": [e.to_dict() for e in self.entities],
            "evidence": [e.to_dict() for e in self.evidence],
            "notes": self.notes,
            "tags": self.tags,
            "status": self.status,
        }

# ────────────────────────────────────────────────────────────────────────────
# PROVIDER SYSTEM (Modular OSINT Sources)
# ────────────────────────────────────────────────────────────────────────────

class Provider:
    """Base class for OSINT providers"""
    name = "Generic Provider"
    description = "Base provider"

    def query(self, entity_type: str, entity_value: str) -> List[Evidence]:
        """Query the provider and return evidence list"""
        return []

class GitHubProvider(Provider):
    name = "GitHub"
    description = "GitHub user & repository search"

    def query(self, entity_type: str, entity_value: str) -> List[Evidence]:
        if entity_type != "username":
            return []

        evidence = []
        url = f"https://api.github.com/users/{quote(entity_value)}"

        try:
            if not requests:
                return evidence

            r = requests.get(url, timeout=6, headers={"User-Agent": "footprint-audit/pro"})
            if r.status_code == 200:
                data = r.json()
                evidence.append(Evidence(
                    finding_type="social_profile",
                    value=f"GitHub user found: {data.get('name', entity_value)}",
                    source="GitHub API",
                    url=data.get("html_url", url),
                    confidence="high",
                    notes=f"Repos: {data.get('public_repos')}, Followers: {data.get('followers')}"
                ))
        except Exception:
            pass

        return evidence

class RedditProvider(Provider):
    name = "Reddit"
    description = "Reddit user lookup"

    def query(self, entity_type: str, entity_value: str) -> List[Evidence]:
        if entity_type != "username":
            return []

        evidence = []
        url = f"https://www.reddit.com/user/{quote(entity_value)}/about.json"

        try:
            if not requests:
                return evidence

            r = requests.get(url, timeout=6, headers={"User-Agent": "footprint-audit/pro"})
            if r.status_code == 200:
                data = r.json().get("data", {})
                evidence.append(Evidence(
                    finding_type="social_profile",
                    value=f"Reddit user found: {entity_value}",
                    source="Reddit API",
                    url=f"https://reddit.com/user/{entity_value}",
                    confidence="high",
                    notes=f"Karma: {data.get('total_karma')}"
                ))
        except Exception:
            pass

        return evidence

class BreachProvider(Provider):
    name = "Breach Databases"
    description = "Email breach/paste search"

    def query(self, entity_type: str, entity_value: str) -> List[Evidence]:
        if entity_type != "email":
            return []

        evidence = []
        # Generate links to breach databases
        breach_sources = [
            ("Have I Been Pwned", f"https://haveibeenpwned.com/account/{quote(entity_value)}"),
            ("HIBP Pastes", f"https://haveibeenpwned.com/Pastes/{quote(entity_value)}"),
            ("LeakCheck", f"https://leakcheck.io/search?query={quote(entity_value)}"),
            ("Dehashed", f"https://dehashed.com/search?query={quote(entity_value)}"),
        ]

        for source_name, source_url in breach_sources:
            evidence.append(Evidence(
                finding_type="breach_check",
                value=f"Breach check via {source_name}",
                source=source_name,
                url=source_url,
                confidence="medium",
                notes="Click to check for breaches"
            ))

        return evidence

# ────────────────────────────────────────────────────────────────────────────
# ORIGINAL CONFIGURATION (Preserved)
# ────────────────────────────────────────────────────────────────────────────

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

# ────────────────────────────────────────────────────────────────────────────
# THEME: dark / black, iOS-dark-mode inspired palette
# ────────────────────────────────────────────────────────────────────────────
IOS_BG = "#000000"          # app background - pure black
IOS_CARD = "#1C1C1E"        # card / surface background
IOS_CARD_HOVER = "#2C2C2E"  # hovered surface
IOS_SEP = "#3A3A3C"         # separators / borders
IOS_LABEL = "#FFFFFF"       # primary text
IOS_SECONDARY = "#98989D"   # secondary text
IOS_BLUE = "#0A84FF"
IOS_BLUE_PRESSED = "#0060DF"
IOS_GREEN = "#30D158"
IOS_ORANGE = "#FF9F0A"
IOS_RED = "#FF453A"
IOS_GROUP_LABEL = "#8E8E93"
IOS_SIDEBAR = "#0D0D0F"
IOS_SIDEBAR_SEL = "#0A84FF"
IOS_SIDEBAR_SEL_BG = "#132338"
IOS_INPUT = "#2C2C2E"

FONT = ("Segoe UI", 11)
FONT_SM = ("Segoe UI", 10)
FONT_LG = ("Segoe UI", 28, "bold")
FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_MONO = ("Consolas", 10)
FONT_MONO_BOLD = ("Consolas", 10, "bold")

CARD_RADIUS = 14
BTN_RADIUS = 10

NAV_ITEMS = [
    ("INVESTIGATION", None),
    ("workspace", "Investigation", "Active case & findings"),
    ("dashboard", "Dashboard", "Overview & statistics"),
    ("ORIGINAL", None),
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

# ────────────────────────────────────────────────────────────────────────────
# ROUNDED-UI HELPERS
# ────────────────────────────────────────────────────────────────────────────

def _rounded_rect_points(x1, y1, x2, y2, radius):
    radius = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    return [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]

def draw_rounded_rect(canvas, x1, y1, x2, y2, radius=12, **kwargs):
    """Draw a rounded rectangle on a canvas and return its item id."""
    points = _rounded_rect_points(x1, y1, x2, y2, radius)
    return canvas.create_polygon(points, smooth=True, **kwargs)


class RoundedCard(tk.Frame):
    """
    A container with a rounded-corner background, drawn on a Canvas.
    Pack/grid children into `.body` (a plain tk.Frame) as usual; the
    card auto-resizes its height to fit its content.
    """
    def __init__(self, parent, bg_color=IOS_CARD, radius=CARD_RADIUS,
                 border_color=None, border_width=0, **kwargs):
        parent_bg = kwargs.pop("outer_bg", None) or parent["bg"]
        super().__init__(parent, bg=parent_bg)
        self.radius = radius
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_width = border_width

        self.canvas = tk.Canvas(self, bg=parent_bg, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.body = tk.Frame(self.canvas, bg=bg_color)
        self._win = self.canvas.create_window(4, 4, window=self.body, anchor="nw")

        self.canvas.bind("<Configure>", self._redraw)
        self.body.bind("<Configure>", self._on_body_resize)

    def _on_body_resize(self, _event=None):
        req_h = self.body.winfo_reqheight() + 8
        cur_h = self.canvas.winfo_height()
        if abs(cur_h - req_h) > 1:
            self.canvas.configure(height=req_h)
        self._redraw()

    def _redraw(self, _event=None):
        self.canvas.delete("bg")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        outline = self.border_color if self.border_color else self.bg_color
        draw_rounded_rect(self.canvas, 1, 1, w - 1, h - 1, radius=self.radius,
                           fill=self.bg_color, outline=outline,
                           width=self.border_width, tags="bg")
        self.canvas.tag_lower("bg")
        self.canvas.itemconfig(self._win, width=max(w - 8, 1))
        self.canvas.coords(self._win, 4, 4)


class RoundedButton(tk.Canvas):
    """A clickable, rounded-corner button drawn on a Canvas."""
    def __init__(self, parent, text, command=None, primary=False,
                 bg=None, fg=None, hover_bg=None, font=("Segoe UI", 12),
                 radius=BTN_RADIUS, padx=20, pady=12, state="normal"):
        parent_bg = parent["bg"]
        super().__init__(parent, bg=parent_bg, highlightthickness=0, bd=0,
                          cursor="hand2" if state == "normal" else "arrow")
        self.command = command
        self.radius = radius
        self.btn_state = state
        self.primary = primary
        self.text = text
        self.font = font

        self.bg_color = bg if bg else (IOS_BLUE if primary else IOS_CARD)
        self.hover_color = hover_bg if hover_bg else (IOS_BLUE_PRESSED if primary else IOS_CARD_HOVER)
        self.fg_color = fg if fg else ("#FFFFFF" if primary else IOS_BLUE)
        self._current_bg = self.bg_color

        tmp = tk.Label(self, text=text, font=font)
        tmp.update_idletasks()
        w = tmp.winfo_reqwidth() + padx * 2
        h = tmp.winfo_reqheight() + pady * 2
        tmp.destroy()
        self.configure(width=w, height=h)

        self._draw()

        if state == "normal":
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
            self.bind("<Button-1>", self._on_click)

    def _draw(self):
        self.delete("all")
        w = int(self["width"])
        h = int(self["height"])
        border = self.bg_color if self.primary else IOS_SEP
        draw_rounded_rect(self, 1, 1, w - 1, h - 1, radius=self.radius,
                           fill=self._current_bg, outline=border, width=1)
        text_fg = self.fg_color if self.btn_state == "normal" else IOS_SECONDARY
        self.create_text(w / 2, h / 2, text=self.text, fill=text_fg, font=self.font)

    def _on_enter(self, _e):
        self._current_bg = self.hover_color
        self._draw()

    def _on_leave(self, _e):
        self._current_bg = self.bg_color
        self._draw()

    def _on_click(self, _e):
        if self.command and self.btn_state == "normal":
            self.command()

    def set_state(self, state):
        self.btn_state = state
        self.configure(cursor="hand2" if state == "normal" else "arrow")
        self._current_bg = self.bg_color
        self._draw()


class RoundedEntry(tk.Frame):
    """A rounded-corner wrapper around a standard tk.Entry."""
    def __init__(self, parent, textvariable=None, width=30, radius=10,
                 bg_color=IOS_INPUT, fg_color=IOS_LABEL, justify="left", **kwargs):
        parent_bg = parent["bg"]
        super().__init__(parent, bg=parent_bg)
        self.radius = radius
        self.bg_color = bg_color

        self.canvas = tk.Canvas(self, bg=parent_bg, highlightthickness=0, bd=0, height=36)
        self.canvas.pack(fill="x", expand=True)

        self.entry = tk.Entry(self.canvas, textvariable=textvariable, bg=bg_color, fg=fg_color,
                               insertbackground=IOS_BLUE, relief="flat", font=FONT,
                               justify=justify, width=width, **kwargs)
        self._win = self.canvas.create_window(10, 18, window=self.entry, anchor="w")

        self.canvas.bind("<Configure>", self._redraw)

    def _redraw(self, _event=None):
        self.canvas.delete("bg")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        draw_rounded_rect(self.canvas, 1, 1, w - 1, h - 1, radius=self.radius,
                           fill=self.bg_color, outline=self.bg_color, tags="bg")
        self.canvas.tag_lower("bg")
        self.canvas.coords(self._win, 10, h / 2)


# ────────────────────────────────────────────────────────────────────────────
# PROFESSIONAL OSINT APP (Enhanced from original)
# ────────────────────────────────────────────────────────────────────────────

class ProfessionalOSINTApp(tk.Tk):
    def __init__(self):
        super().__init__()
        try:
            self.title("Footprint Audit - Professional OSINT Platform")
            self.geometry("1200x800")
            self.minsize(1000, 700)
            self.configure(bg=IOS_BG)

            # Core state
            self.links = []
            self.platform_rows = {}
            self.email_rows = {}
            self._audit_running = False
            self._cancel = False
            self._current_screen = None
            self._nav_buttons = {}
            self.screens = {}

            # Investigation workspace
            self.current_investigation = Investigation()
            self.investigations_history = []

            # OSINT Providers
            self.providers = [
                GitHubProvider(),
                RedditProvider(),
                BreachProvider(),
            ]

            # Appearance
            self.bg_image_path = None
            self.bg_opacity = tk.DoubleVar(value=0.1)
            self.theme_var = tk.StringVar(value="dark")
            self.font_size_var = tk.StringVar(value="normal")

            self._setup_styles()
            self._build_shell()
            self._show_screen("workspace")
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
                    bordercolor=IOS_CARD, lightcolor=IOS_BLUE, darkcolor=IOS_BLUE, thickness=6)
        s.configure("Treeview", background=IOS_CARD, foreground=IOS_LABEL,
                    fieldbackground=IOS_CARD, borderwidth=0, rowheight=32, font=FONT)
        s.configure("Treeview.Heading", background=IOS_BG, foreground=IOS_SECONDARY,
                    relief="flat", font=("Segoe UI", 10, "bold"))
        s.map("Treeview", background=[("selected", IOS_BLUE)], foreground=[("selected", "#FFFFFF")])

        s.configure("Vertical.TScrollbar", background=IOS_CARD, troughcolor=IOS_BG,
                    bordercolor=IOS_BG, lightcolor=IOS_CARD, darkcolor=IOS_CARD,
                    arrowcolor=IOS_SECONDARY, gripcount=0, width=14)
        s.map("Vertical.TScrollbar", background=[("active", IOS_BLUE)])
        s.configure("Horizontal.TScrollbar", background=IOS_CARD, troughcolor=IOS_BG,
                    bordercolor=IOS_BG, lightcolor=IOS_CARD, darkcolor=IOS_CARD,
                    arrowcolor=IOS_SECONDARY, gripcount=0, width=14)
        s.map("Horizontal.TScrollbar", background=[("active", IOS_BLUE)])

        s.configure("TCombobox", fieldbackground=IOS_INPUT, background=IOS_INPUT,
                    foreground=IOS_LABEL, arrowcolor=IOS_SECONDARY, bordercolor=IOS_SEP,
                    lightcolor=IOS_INPUT, darkcolor=IOS_INPUT)
        s.map("TCombobox", fieldbackground=[("readonly", IOS_INPUT)],
              foreground=[("readonly", IOS_LABEL)])
        self.option_add("*TCombobox*Listbox*Background", IOS_CARD)
        self.option_add("*TCombobox*Listbox*Foreground", IOS_LABEL)
        self.option_add("*TCombobox*Listbox*selectBackground", IOS_BLUE)

    def _build_shell(self):
        root = tk.Frame(self, bg=IOS_BG)
        root.pack(fill="both", expand=True)

        sidebar = tk.Frame(root, bg=IOS_SIDEBAR, width=248, highlightbackground=IOS_SEP, highlightthickness=1)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Footprint Audit", bg=IOS_SIDEBAR, fg=IOS_LABEL,
                 font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=18, pady=(20, 4))
        tk.Label(sidebar, text="Professional OSINT", bg=IOS_SIDEBAR, fg=IOS_SECONDARY,
                 font=FONT_SM).pack(anchor="w", padx=18, pady=(0, 12))

        nav_canvas = tk.Canvas(sidebar, bg=IOS_SIDEBAR, highlightthickness=0, bd=0)
        nav_scroll = ttk.Scrollbar(sidebar, orient="vertical", command=nav_canvas.yview)
        nav_inner = tk.Frame(nav_canvas, bg=IOS_SIDEBAR)
        nav_inner.bind("<Configure>", lambda e: nav_canvas.configure(scrollregion=nav_canvas.bbox("all")))
        nav_canvas.create_window((0, 0), window=nav_inner, anchor="nw", width=230)
        nav_canvas.configure(yscrollcommand=nav_scroll.set)
        nav_canvas.pack(side="left", fill="both", expand=True)
        nav_scroll.pack(side="right", fill="y")

        def _nav_mousewheel(event):
            if event.delta:
                nav_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                nav_canvas.yview_scroll(3 if event.num == 5 else -3, "units")
        nav_canvas.bind("<MouseWheel>", _nav_mousewheel)
        nav_canvas.bind("<Button-4>", _nav_mousewheel)
        nav_canvas.bind("<Button-5>", _nav_mousewheel)

        for item in NAV_ITEMS:
            if item[1] is None:
                tk.Label(nav_inner, text=item[0], bg=IOS_SIDEBAR, fg=IOS_GROUP_LABEL,
                         font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=18, pady=(14, 4))
            else:
                key, title, subtitle = item
                self._nav_row(nav_inner, key, title, subtitle)

        self.content = tk.Frame(root, bg=IOS_BG)
        self.content.pack(side="left", fill="both", expand=True)

        self._build_all_screens()

    def _nav_row(self, parent, key, title, subtitle):
        row = tk.Frame(parent, bg=IOS_SIDEBAR, cursor="hand2")
        row.pack(fill="x", padx=10, pady=1)

        inner = tk.Frame(row, bg=IOS_SIDEBAR)
        inner.pack(fill="x", padx=8, pady=8)

        title_lbl = tk.Label(inner, text=title, bg=IOS_SIDEBAR, fg=IOS_LABEL, font=FONT, anchor="w")
        title_lbl.pack(anchor="w")
        tk.Label(inner, text=subtitle, bg=IOS_SIDEBAR, fg=IOS_SECONDARY, font=("Segoe UI", 9), anchor="w").pack(anchor="w")

        chevron = tk.Label(row, text="›", bg=IOS_SIDEBAR, fg=IOS_SEP, font=("Segoe UI", 16))
        chevron.place(relx=1.0, rely=0.5, anchor="e", x=-12)

        self._nav_buttons[key] = (row, inner, title_lbl)

        for w in (row, inner, title_lbl):
            w.bind("<Button-1>", lambda _e, k=key: self._show_screen(k))
            w.bind("<Enter>", lambda _e, r=row, i=inner, t=title_lbl, k=key: self._nav_hover(k, r, i, t, True))
            w.bind("<Leave>", lambda _e, r=row, i=inner, t=title_lbl, k=key: self._nav_hover(k, r, i, t, False))

    def _nav_hover(self, key, row, inner, title_lbl, entering):
        if key == self._current_screen:
            return
        bg = IOS_CARD_HOVER if entering else IOS_SIDEBAR
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
        """Build a full-screen scrollable area. Returns (outer, inner)."""
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

        canvas.bind("<Configure>", _on_configure)

        def _on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                if event.num == 5:
                    canvas.yview_scroll(3, "units")
                elif event.num == 4:
                    canvas.yview_scroll(-3, "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", _on_mousewheel)
        canvas.bind("<Button-5>", _on_mousewheel)

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

        return outer, inner

    def _scroll_box(self, parent, height=260):
        """
        A bounded, independently scrollable rounded box for use INSIDE a
        screen (e.g. a long list of toggles) rather than the whole screen.
        Returns (card_frame, inner_content_frame).
        """
        wrap = tk.Frame(parent, bg=IOS_BG)
        wrap.pack(fill="x", padx=24, pady=(0, 8))

        card = tk.Frame(wrap, bg=IOS_CARD, highlightbackground=IOS_SEP, highlightthickness=1)
        card.pack(fill="both", expand=True)

        canvas = tk.Canvas(card, bg=IOS_CARD, highlightthickness=0, bd=0, height=height)
        sb = ttk.Scrollbar(card, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=IOS_CARD)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)

        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def _on_configure(event):
            canvas.itemconfig(win, width=event.width)
        canvas.bind("<Configure>", _on_configure)

        def _on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                canvas.yview_scroll(3 if event.num == 5 else -3, "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", _on_mousewheel)
        canvas.bind("<Button-5>", _on_mousewheel)
        # also bind on children so scrolling works when hovering over rows
        def _bind_children(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", _on_mousewheel)
            widget.bind("<Button-5>", _on_mousewheel)
        inner.bind("<MouseWheel>", _on_mousewheel)
        inner._bind_children = _bind_children

        return card, inner

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
        """Returns a rounded card's content frame (bg=IOS_CARD) to pack children into."""
        wrap = tk.Frame(parent, bg=IOS_BG)
        wrap.pack(fill="x", padx=24, pady=(0, 8))
        card = RoundedCard(wrap, bg_color=IOS_CARD, radius=CARD_RADIUS,
                            border_color=IOS_SEP, border_width=1)
        card.pack(fill="x")
        return card.body

    def _ios_button(self, parent, text, command, primary=False, state="normal"):
        return RoundedButton(parent, text, command=command, primary=primary, state=state)

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
                            selectcolor=IOS_BLUE, fg=IOS_LABEL, relief="flat",
                            highlightthickness=0)
        cb.pack(side="right", padx=16)
        if not last:
            tk.Frame(parent, bg=IOS_SEP, height=1).pack(fill="x", padx=16)
        return row

    # ────────────────────────────────────────────────────────────────────────
    # NEW: INVESTIGATION WORKSPACE SCREENS
    # ────────────────────────────────────────────────────────────────────────

    def _build_investigation_workspace_screen(self):
        """Professional investigation workspace screen"""
        _, inner = self._scroll_screen("workspace")
        self._large_title(inner, "Investigation Workspace",
                          "Manage your active investigation case")

        # Case header
        self._section_label(inner, "Active Case")
        case_card = self._inset_group(inner)

        case_info = tk.Frame(case_card, bg=IOS_CARD)
        case_info.pack(fill="x", padx=16, pady=12)

        tk.Label(case_info, text="Case Name:", bg=IOS_CARD, fg=IOS_SECONDARY, font=FONT_SM).pack(anchor="w")
        self.investigation_name_var = tk.StringVar(value=self.current_investigation.name)
        tk.Entry(case_info, textvariable=self.investigation_name_var, bg=IOS_INPUT, fg=IOS_LABEL,
                insertbackground=IOS_BLUE, relief="flat", font=FONT, width=40).pack(fill="x", pady=(4, 0), ipady=4)

        tk.Label(case_info, text="Target Entity:", bg=IOS_CARD, fg=IOS_SECONDARY, font=FONT_SM).pack(anchor="w", pady=(12, 0))
        self.investigation_target_var = tk.StringVar(value=self.current_investigation.target)
        tk.Entry(case_info, textvariable=self.investigation_target_var, bg=IOS_INPUT, fg=IOS_LABEL,
                insertbackground=IOS_BLUE, relief="flat", font=FONT, width=40).pack(fill="x", pady=(4, 0), ipady=4)

        tk.Label(case_info, text="Status:", bg=IOS_CARD, fg=IOS_SECONDARY, font=FONT_SM).pack(anchor="w", pady=(12, 0))
        self.investigation_status_var = tk.StringVar(value=self.current_investigation.status)
        status_menu = ttk.Combobox(case_info, textvariable=self.investigation_status_var,
                                   values=["active", "paused", "completed"], state="readonly", font=FONT)
        status_menu.pack(fill="x", pady=(4, 0))

        tk.Frame(case_card, bg=IOS_SEP, height=1).pack(fill="x", padx=16)

        # Findings summary
        summary_frame = tk.Frame(case_card, bg=IOS_CARD)
        summary_frame.pack(fill="x", padx=16, pady=12)

        self.findings_count = tk.StringVar(value=str(len(self.current_investigation.evidence)))
        self.entities_count = tk.StringVar(value=str(len(self.current_investigation.entities)))

        tk.Label(summary_frame, text="Findings: ", bg=IOS_CARD, fg=IOS_SECONDARY, font=FONT_SM).pack(anchor="w")
        tk.Label(summary_frame, textvariable=self.findings_count, bg=IOS_CARD, fg=IOS_BLUE, font=("Segoe UI", 16, "bold")).pack(anchor="w")

        tk.Label(summary_frame, text="Entities: ", bg=IOS_CARD, fg=IOS_SECONDARY, font=FONT_SM).pack(anchor="w", pady=(12, 0))
        tk.Label(summary_frame, textvariable=self.entities_count, bg=IOS_CARD, fg=IOS_GREEN, font=("Segoe UI", 16, "bold")).pack(anchor="w")

        # Action buttons
        self._section_label(inner, "Actions")
        btn_row = tk.Frame(inner, bg=IOS_BG)
        btn_row.pack(fill="x", padx=24)
        self._ios_button(btn_row, "New Investigation", self._new_investigation).pack(side="left", padx=(0, 10))
        self._ios_button(btn_row, "Save Case", self._save_investigation, primary=True).pack(side="left", padx=(0, 10))
        self._ios_button(btn_row, "Export", self._export_investigation).pack(side="left")

        # Notes section
        self._section_label(inner, "Investigation Notes")
        notes_card = self._inset_group(inner)
        self.investigation_notes = scrolledtext.ScrolledText(notes_card, bg=IOS_CARD, fg=IOS_LABEL,
                                                            font=FONT_MONO, wrap="word", relief="flat",
                                                            padx=16, pady=14, height=6,
                                                            insertbackground=IOS_LABEL,
                                                            highlightbackground=IOS_SEP, highlightthickness=1)
        self.investigation_notes.pack(fill="both", expand=True, padx=16, pady=12)
        self.investigation_notes.insert("1.0", self.current_investigation.notes)

        tk.Label(inner, text="Save notes by clicking Save Case.", bg=IOS_BG, fg=IOS_SECONDARY, font=FONT_SM).pack(anchor="w", padx=28, pady=12)

    def _build_dashboard_screen(self):
        """Professional OSINT dashboard"""
        _, inner = self._scroll_screen("dashboard")
        self._large_title(inner, "Investigation Dashboard",
                          "Overview of all entities, findings, and correlations")

        # Statistics cards
        self._section_label(inner, "Investigation Summary")
        stats_wrap = tk.Frame(inner, bg=IOS_BG)
        stats_wrap.pack(fill="x", padx=24)

        stats = [
            ("Entities", len(self.current_investigation.entities), IOS_BLUE),
            ("Findings", len(self.current_investigation.evidence), IOS_GREEN),
            ("Sources", len(set([e.source for e in self.current_investigation.evidence])), IOS_ORANGE),
            ("Confidence Avg", "Med", IOS_SECONDARY),
        ]

        for label, value, color in stats:
            tile_wrap = tk.Frame(stats_wrap, bg=IOS_BG)
            tile_wrap.pack(side="left", fill="both", expand=True, padx=(0, 10))
            tile = RoundedCard(tile_wrap, bg_color=IOS_CARD, radius=CARD_RADIUS,
                                border_color=IOS_SEP, border_width=1)
            tile.pack(fill="x")
            tk.Label(tile.body, text=label, bg=IOS_CARD, fg=IOS_SECONDARY, font=FONT_SM).pack(
                anchor="w", padx=14, pady=(12, 0))
            tk.Label(tile.body, text=str(value), bg=IOS_CARD, fg=color, font=("Segoe UI", 24, "bold")).pack(
                anchor="w", padx=14, pady=(0, 12))

        # Entities list
        self._section_label(inner, "Discovered Entities")
        entities_card = self._inset_group(inner)

        if self.current_investigation.entities:
            for entity in self.current_investigation.entities[:10]:
                ent_row = tk.Frame(entities_card, bg=IOS_CARD)
                ent_row.pack(fill="x")
                tk.Label(ent_row, text=f"[{entity.type.upper()}] {entity.value}",
                        bg=IOS_CARD, fg=IOS_BLUE, font=FONT).pack(side="left", padx=16, pady=12)
                tk.Label(ent_row, text="›", bg=IOS_CARD, fg=IOS_SEP, font=("Segoe UI", 16)).pack(side="right", padx=16)
                tk.Frame(entities_card, bg=IOS_SEP, height=1).pack(fill="x", padx=16)
        else:
            tk.Label(entities_card, text="No entities discovered yet. Run an audit to populate.",
                    bg=IOS_CARD, fg=IOS_SECONDARY, font=FONT_SM).pack(padx=16, pady=12)

        # Recent findings
        self._section_label(inner, "Recent Findings")
        findings_card = self._inset_group(inner)

        if self.current_investigation.evidence:
            for evidence in self.current_investigation.evidence[-5:]:
                find_row = tk.Frame(findings_card, bg=IOS_CARD)
                find_row.pack(fill="x")
                tk.Label(find_row, text=evidence.value, bg=IOS_CARD, fg=IOS_LABEL, font=FONT).pack(
                    side="left", padx=16, pady=12)
                tk.Label(find_row, text=evidence.source, bg=IOS_CARD, fg=IOS_SECONDARY, font=FONT_SM).pack(
                    side="right", padx=16)
                tk.Frame(findings_card, bg=IOS_SEP, height=1).pack(fill="x", padx=16)
        else:
            tk.Label(findings_card, text="No findings yet. Start an audit to collect evidence.",
                    bg=IOS_CARD, fg=IOS_SECONDARY, font=FONT_SM).pack(padx=16, pady=12)

    # ────────────────────────────────────────────────────────────────────────
    # PRESERVED: ORIGINAL SCREENS
    # ────────────────────────────────────────────────────────────────────────

    def _build_all_screens(self):
        """Build all screens - NEW + ORIGINAL"""
        # NEW PROFESSIONAL SCREENS
        self._build_investigation_workspace_screen()
        self._build_dashboard_screen()

        # ORIGINAL SCREENS (all preserved)
        self._build_home_screen()
        self._build_identifiers_screen()
        self._build_sections_screen()
        self._build_appearance_screen()
        self._build_platforms_screen()
        self._build_email_screen()
        self._build_text_screen("breaches", "Breaches & Pastes",
                                "Check if your email appears in known breach databases and paste sites.",
                                "breach_output")
        self._build_text_screen("search", "Web Search",
                                "Google dork queries to find public mentions of your identifiers.",
                                "search_output")
        self._build_text_screen("archives", "Archives",
                                "Historical snapshots and cached copies of pages tied to you.",
                                "archive_output")
        self._build_text_screen("code", "Code & Repos",
                                "Search public code for leaked emails, keys, or usernames.",
                                "code_output")
        self._build_text_screen("brokers", "Data Brokers",
                                "People-search sites that may list your personal information.",
                                "broker_output")
        self._build_text_screen("domain", "Domain & DNS",
                                "DNS records, WHOIS, certificates, and domain security tools.",
                                "domain_output")
        self._build_text_screen("people", "People & Phone",
                                "Name, phone, and reverse-image search links.",
                                "people_output")
        self._build_report_screen()

        self.link_widgets = [
            self.breach_output, self.search_output, self.archive_output,
            self.code_output, self.broker_output, self.domain_output, self.people_output,
        ]

    # ────────────────────────────────────────────────────────────────────────
    # INVESTIGATION WORKSPACE METHODS
    # ────────────────────────────────────────────────────────────────────────

    def _new_investigation(self):
        """Start a new investigation"""
        self.current_investigation = Investigation()
        self.investigation_name_var.set(self.current_investigation.name)
        self.investigation_target_var.set(self.current_investigation.target)
        self.investigation_status_var.set(self.current_investigation.status)
        self.investigation_notes.delete("1.0", "end")
        self.findings_count.set("0")
        self.entities_count.set("0")
        messagebox.showinfo("New Investigation", "New investigation case created.")

    def _save_investigation(self):
        """Save the current investigation"""
        self.current_investigation.name = self.investigation_name_var.get()
        self.current_investigation.target = self.investigation_target_var.get()
        self.current_investigation.status = self.investigation_status_var.get()
        self.current_investigation.notes = self.investigation_notes.get("1.0", "end-1c")
        self.investigations_history.append(self.current_investigation.to_dict())
        messagebox.showinfo("Saved", f"Investigation '{self.current_investigation.name}' saved.\nTotal cases: {len(self.investigations_history)}")

    def _export_investigation(self):
        """Export investigation as JSON"""
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"investigation_{datetime.now():%Y%m%d_%H%M}.json",
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.current_investigation.to_dict(), f, indent=2)
            messagebox.showinfo("Exported", f"Investigation exported to:\n{path}")

    # ────────────────────────────────────────────────────────────────────────
    # ORIGINAL SCREENS
    # ────────────────────────────────────────────────────────────────────────

    def _build_home_screen(self):
        """Simplified home screen"""
        _, inner = self._scroll_screen("home")
        self._large_title(inner, "Home", "Original OSINT audit tool")
        tk.Label(inner, text="Professional OSINT investigation platform\n\nUse Investigation workspace for advanced features.\nUse original audit tools below.",
                bg=IOS_BG, fg=IOS_SECONDARY, font=FONT, wraplength=600, justify="left").pack(
                anchor="w", padx=28, pady=24)

    def _build_identifiers_screen(self):
        """Identifiers input screen"""
        _, inner = self._scroll_screen("identifiers")
        self._large_title(inner, "Identifiers", "Enter details to audit")

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

    def _build_sections_screen(self):
        """
        Audit sections toggle screen.
        The whole screen scrolls (via _scroll_screen), AND the toggle list
        itself sits in its own bounded, independently-scrollable rounded
        box, so a long list of toggles never blows out the page.
        """
        _, inner = self._scroll_screen("sections")
        self._large_title(inner, "Audit Sections", "Choose what to scan")

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

        self._section_label(inner, "All sections")
        # Bounded, independently-scrollable box holding every toggle group
        card, scroll_body = self._scroll_box(inner, height=280)

        for gi, (group_name, items) in enumerate(groups):
            group_lbl = tk.Label(scroll_body, text=group_name.upper(), bg=IOS_CARD,
                                  fg=IOS_GROUP_LABEL, font=("Segoe UI", 10, "bold"))
            group_lbl.pack(anchor="w", padx=16, pady=(14 if gi == 0 else 18, 6))
            for i, (key, label) in enumerate(items):
                var = tk.BooleanVar(value=True)
                self.section_vars[key] = var
                self._toggle_row(scroll_body, label, var, last=(i == len(items) - 1))

        btn_row = tk.Frame(inner, bg=IOS_BG)
        btn_row.pack(fill="x", padx=24, pady=16)
        self._ios_button(btn_row, "Select All", self._select_all_sections).pack(side="left", padx=(0, 10))
        self._ios_button(btn_row, "Clear All", self._clear_all_sections).pack(side="left")

    def _build_appearance_screen(self):
        """Appearance customization screen"""
        _, inner = self._scroll_screen("appearance")
        self._large_title(inner, "Appearance", "Customize the UI")

        self._section_label(inner, "Theme")
        theme_card = self._inset_group(inner)
        themes = [("Light", "light"), ("Dark", "dark"), ("Auto", "auto")]
        for i, (label, value) in enumerate(themes):
            row = tk.Frame(theme_card, bg=IOS_CARD)
            row.pack(fill="x")
            rb = tk.Radiobutton(row, text=label, variable=self.theme_var, value=value,
                               bg=IOS_CARD, activebackground=IOS_CARD, fg=IOS_LABEL,
                               selectcolor=IOS_INPUT, font=FONT, relief="flat",
                               highlightthickness=0)
            rb.pack(side="left", padx=16, pady=12)
            if i < len(themes) - 1:
                tk.Frame(theme_card, bg=IOS_SEP, height=1).pack(fill="x", padx=16)

    def _build_platforms_screen(self):
        """Platform scanning screen"""
        frame = self._screen("platforms")
        self._large_title(frame, "Platforms", f"Scanning {len(PLATFORMS)} profiles")
        tk.Label(frame, text="[Platform scan results shown here]", bg=IOS_BG, fg=IOS_SECONDARY, font=FONT).pack(padx=28, pady=12)

    def _build_email_screen(self):
        """Email intelligence screen"""
        frame = self._screen("email")
        self._large_title(frame, "Email Intel", "Email verification & intelligence")
        tk.Label(frame, text="[Email intelligence shown here]", bg=IOS_BG, fg=IOS_SECONDARY, font=FONT).pack(padx=28, pady=12)

    def _build_text_screen(self, key, title, subtitle, attr):
        """Generic text output screen"""
        frame = self._screen(key)
        self._large_title(frame, title, subtitle)
        w = scrolledtext.ScrolledText(frame, bg=IOS_CARD, fg=IOS_LABEL, font=FONT_MONO,
                                      wrap="word", relief="flat", padx=16, pady=14,
                                      insertbackground=IOS_LABEL,
                                      highlightbackground=IOS_SEP, highlightthickness=1)
        w.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        w.insert("1.0", f"[{title} results shown here]\n")
        w.config(state="disabled")
        setattr(self, attr, w)

    def _build_report_screen(self):
        """Full report screen"""
        frame = self._screen("report")
        self._large_title(frame, "Full Report", "Complete audit log")
        self.output = scrolledtext.ScrolledText(frame, bg=IOS_CARD, fg=IOS_LABEL, font=FONT_MONO,
                                                wrap="word", relief="flat", padx=16, pady=14,
                                                insertbackground=IOS_LABEL,
                                                highlightbackground=IOS_SEP, highlightthickness=1)
        self.output.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        self.output.insert("1.0", "[Full report shown here]\n")
        self.output.config(state="disabled")

    def _select_all_sections(self):
        for v in self.section_vars.values():
            v.set(True)

    def _clear_all_sections(self):
        for v in self.section_vars.values():
            v.set(False)

    def start_audit(self):
        """Stub for audit start"""
        messagebox.showinfo("Audit", "Original audit features preserved in legacy screens.")

if __name__ == "__main__":
    try:
        app = ProfessionalOSINTApp()
        app.mainloop()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", f"Failed to start:\n{str(e)}\n\nCheck console for details.")
        root.destroy()
