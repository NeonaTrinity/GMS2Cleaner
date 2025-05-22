import json
import os
import tkinter as tk

SETTINGS_FILE = os.path.expanduser("~/.gms2_cleaner_settings.json")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except:
        pass

class ThemeManager:
    def __init__(self, root, apply_theme_fn):
        self.root = root
        self.settings = load_settings()
        self.font_size = self.settings.get("font_size", 10)
        self.dark_mode = self.settings.get("dark_mode", True)
        self.apply_theme_fn = apply_theme_fn

        self.theme_colors = {
            "dark": {"bg": "#2e2e2e", "fg": "#ffffff", "highlight": "#80ff80"},
            "light": {"bg": "#f0f0f0", "fg": "#000000", "highlight": "#008000"}
        }

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.save()
        self.apply_theme_fn()

    def increase_font(self):
        self.font_size = min(self.font_size + 1, 20)
        self.save()
        self.apply_theme_fn()

    def decrease_font(self):
        self.font_size = max(self.font_size - 1, 6)
        self.save()
        self.apply_theme_fn()

    def save(self):
        self.settings["font_size"] = self.font_size
        self.settings["dark_mode"] = self.dark_mode
        save_settings(self.settings)

    def apply(self, widgets):
        theme = "dark" if self.dark_mode else "light"
        colors = self.theme_colors[theme]
        for widget in widgets:
            try:
                widget.configure(bg=colors["bg"], fg=colors["fg"])
            except:
                pass