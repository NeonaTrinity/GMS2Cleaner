import tkinter as tk
from tkinter import filedialog

class LogPanel:
    def __init__(self, parent):
        self.log_frame = tk.Frame(parent)
        self.log_visible = False
        self.log_lines = []

        self.log_box = tk.Text(self.log_frame, height=10, wrap="word", state="disabled")
        self.log_scroll = tk.Scrollbar(self.log_frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=self.log_scroll.set)
        self.log_scroll.pack(side="right", fill="y")
        self.log_box.pack(side="left", fill="both", expand=True)

        self.log_box.tag_config("info", foreground="white")
        self.log_box.tag_config("success", foreground="green")
        self.log_box.tag_config("warn", foreground="orange")
        self.log_box.tag_config("error", foreground="red")

    def apply_theme(self, theme):
        colors = {"dark": {"bg": "#2e2e2e", "fg": "#ffffff"},
                  "light": {"bg": "#f0f0f0", "fg": "#000000"}}
        self.log_box.configure(bg=colors[theme]["bg"], fg=colors[theme]["fg"])
        self.log_box.tag_config("info", foreground=colors[theme]["fg"])
        self.log_scroll.configure(bg=colors[theme]["bg"])

    def toggle(self):
        if self.log_visible:
            self.log_frame.pack_forget()
        else:
            self.log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_visible = not self.log_visible

    def log(self, message, level="info"):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n", level)
        self.log_box.configure(state="disabled")
        self.log_box.see("end")
        self.log_lines.append(f"[{level.upper()}] {message}")

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text Files", "*.txt")],
                                             title="Export Log")
        if path:
            with open(path, "w") as f:
                for line in self.log_lines:
                    f.write(line + "\n")