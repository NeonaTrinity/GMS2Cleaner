from tkinter import *
from tkinter import ttk, filedialog, messagebox
import os

from gms2_cleaner_scan_module import scan_gms2_project, scan_layers
from gms2_cleaner_display_module import populate_folder_list, load_folder_contents
from gms2_cleaner_deletion_module import delete_files, undo_last_delete, cleanup_old_backups
from gms2_cleaner_summary_module import show_summary_popup
from gms2_cleaner_log_module import LogPanel
from gms2_cleaner_theme_module import ThemeManager

class GMS2Cleaner:
    def __init__(self, root):
        self.root = root
        self.root.title("GMS2 Sprite Cleaner")
        self.project_path = None
        self.project_name = ""
        self.sprite_data = {}
        self.layer_data = {}
        self.file_sizes = {}
        self.used_frames = set()
        self.file_vars = []
        self.selected_folder = None
        self.display_mode = "sprites"  # Tracks whether showing sprites or layers

        self.backup_enabled = BooleanVar(value=True)
        self.trash_dir = os.path.join(os.getcwd(), "_GMS2Cleaner_Trash")
        self.backup_dir = os.path.expanduser("~/Documents/GMS2_Cleaner_Backups")

        self.log_panel = LogPanel(self.root)
        self.theme_mgr = ThemeManager(self.root, self.apply_theme)

        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        top = Frame(self.root); top.pack(fill=X)
        Button(top, text="Select .yyp", command=self.select_project).pack(side=LEFT)
        Button(top, text="Scan Project", command=self.scan_project).pack(side=LEFT)
        Button(top, text="Scan Layers", command=self.scan_layers).pack(side=LEFT)
        Button(top, text="Delete", command=self.delete_selected).pack(side=LEFT)
        Button(top, text="Clear All Sprites", command=self.clear_all_sprites).pack(side=LEFT)
        Checkbutton(top, text="Backup Deletes", variable=self.backup_enabled).pack(side=LEFT)
        Button(top, text="Theme", command=self.theme_mgr.toggle_dark_mode).pack(side=LEFT)
        Button(top, text="Font +", command=self.theme_mgr.increase_font).pack(side=LEFT)
        Button(top, text="Font -", command=self.theme_mgr.decrease_font).pack(side=LEFT)
        Button(top, text="Toggle Log", command=self.log_panel.toggle).pack(side=LEFT)

        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progress.pack(fill=X, padx=5, pady=2)

        self.folder_listbox = Listbox(self.root, font=("Arial", self.theme_mgr.font_size), width=30)
        self.folder_listbox.pack(side=LEFT, fill=Y, padx=5)
        self.folder_listbox.bind("<<ListboxSelect>>", self.load_selected_folder)

        right = Frame(self.root); right.pack(side=LEFT, fill=BOTH, expand=True)
        self.canvas = Canvas(right)
        self.scrollbar = Scrollbar(right, orient="vertical", command=self.canvas.yview)
        self.inner_frame = Frame(self.canvas)

        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.image_label = Label(self.root)
        self.image_label.pack(side=BOTTOM, pady=5)

    def apply_theme(self):
        theme = "dark" if self.theme_mgr.dark_mode else "light"
        colors = self.theme_mgr.theme_colors[theme]
        self.root.configure(bg=colors["bg"])
        self.folder_listbox.configure(bg=colors["bg"], fg=colors["fg"], font=("Arial", self.theme_mgr.font_size))
        self.canvas.configure(bg=colors["bg"])
        self.inner_frame.configure(bg=colors["bg"])
        self.log_panel.apply_theme(theme)
        for widget in self.inner_frame.winfo_children():
            widget.configure(bg=colors["bg"], fg=colors["fg"], font=("Arial", self.theme_mgr.font_size))

    def select_project(self):
        path = filedialog.askopenfilename(filetypes=[("GameMaker Project", "*.yyp")])
        if path:
            self.project_path = os.path.dirname(path)
            self.project_name = os.path.splitext(os.path.basename(path))[0]
            self.log_panel.log(f"Loaded project: {self.project_name}", "success")
            self.folder_listbox.delete(0, END)
            self.sprite_data = {}
            self.layer_data = {}
            self.file_sizes = {}
            self.used_frames = set()
            self.display_mode = "sprites"

    def scan_project(self):
        if not self.project_path:
            messagebox.showerror("No Project", "Select a .yyp project file first.")
            return
        self.log_panel.log("Scanning project...", "info")
        try:
            self.sprite_data, self.file_sizes, self.used_frames = scan_gms2_project(
                self.project_path, log_fn=self.log_panel.log, progress_callback=self.update_progress
            )
            self.display_mode = "sprites"
            populate_folder_list(self.folder_listbox, self.sprite_data, self.layer_data)
            self.show_summary()
            self.log_panel.log("Project scan completed.", "success")
        except Exception as e:
            self.log_panel.log(f"⚠ Project scan failed: {e}", "error")
            messagebox.showerror("Error", f"Project scan failed: {e}")

    def scan_layers(self):
        if not self.project_path:
            messagebox.showerror("No Project", "Select a .yyp project file first.")
            return
        self.log_panel.log("Scanning layers...", "info")
        try:
            self.layer_data = scan_layers(self.project_path, log_fn=self.log_panel.log, progress_callback=self.update_progress)
            self.display_mode = "layers"
            populate_folder_list(self.folder_listbox, self.sprite_data, self.layer_data)
            self.show_summary()
            self.log_panel.log("Layer scan completed.", "success")
        except Exception as e:
            self.log_panel.log(f"⚠ Layer scan failed: {e}", "error")
            messagebox.showerror("Error", f"Layer scan failed: {e}")

    def update_progress(self, value):
        self.progress["value"] = value
        self.root.update()

    def load_selected_folder(self, event):
        sel = self.folder_listbox.curselection()
        if not sel:
            return
        name = self.folder_listbox.get(sel[0]).split(" (")[0]
        self.selected_folder = name
        load_folder_contents(name, self.inner_frame, self.file_vars, self.sprite_data, self.layer_data, self.file_sizes, self.image_label, mode=self.display_mode)

    def show_summary(self):
        stats = {
            "total_folders": len(self.sprite_data),
            "clean_folders": sum(1 for f in self.sprite_data if not self.sprite_data[f]["sprites"] and (f not in self.layer_data or not self.layer_data[f]["unused_folders"])),
            "flagged_folders": sum(1 for f in self.sprite_data if self.sprite_data[f]["sprites"] or (f in self.layer_data and self.layer_data[f]["unused_folders"])),
            "unused_files": sum(len(self.sprite_data[f]["sprites"]) + (len(self.layer_data[f]["unused_folders"]) if f in self.layer_data else 0) for f in self.sprite_data),
            "clear_all_sprites": self.clear_all_sprites,
            "undo": self.undo_last
        }
        total_bytes = sum(size for f in self.sprite_data for _, _, size in self.sprite_data[f]["sprites"])
        total_bytes += sum(size for f in self.layer_data for _, _, pngs in self.layer_data[f]["unused_folders"] for _, _, size in pngs)
        show_summary_popup(self.root, stats, total_bytes, self.trash_dir, self.backup_dir, self.clear_all_backups)

    def delete_selected(self):
        selected = [path for var, path in self.file_vars if var.get()]
        if not selected:
            messagebox.showinfo("Info", "No items selected for deletion.")
            return
        if messagebox.askyesno("Confirm", f"Delete {len(selected)} selected items?"):
            deleted = delete_files(selected, self.trash_dir, self.project_name, self.backup_enabled.get(), self.backup_dir)
            self.log_panel.log(f"Deleted {len(deleted)} items.", "warn")
            # Update data structures without rescanning
            if self.display_mode == "sprites":
                for path in deleted:
                    for folder in self.sprite_data:
                        self.sprite_data[folder]["sprites"] = [(name, p, size) for name, p, size in self.sprite_data[folder]["sprites"] if p != path]
            else:  # layers
                for path in deleted:
                    for folder in self.layer_data:
                        for i, (subfolder, folder_path, pngs) in enumerate(self.layer_data[folder]["unused_folders"]):
                            if path == folder_path:
                                self.layer_data[folder]["unused_folders"].pop(i)
                            else:
                                self.layer_data[folder]["unused_folders"][i] = (subfolder, folder_path, [(name, p, size) for name, p, size in pngs if p != path])
                        # Remove empty folders
                        self.layer_data[folder]["unused_folders"] = [(subfolder, folder_path, pngs) for subfolder, folder_path, pngs in self.layer_data[folder]["unused_folders"] if pngs or os.path.exists(folder_path)]
            # Advance listbox selection
            current_sel = self.folder_listbox.curselection()
            if current_sel:
                current_index = current_sel[0]
                next_index = min(current_index + 1, self.folder_listbox.size() - 1)
                self.folder_listbox.selection_clear(0, END)
                self.folder_listbox.selection_set(next_index)
                self.folder_listbox.see(next_index)
                next_folder = self.folder_listbox.get(next_index).split(" (")[0]
                self.selected_folder = next_folder
            # Refresh GUI
            if self.selected_folder:
                load_folder_contents(self.selected_folder, self.inner_frame, self.file_vars, self.sprite_data, self.layer_data, self.file_sizes, self.image_label, mode=self.display_mode)
            populate_folder_list(self.folder_listbox, self.sprite_data, self.layer_data)

    def clear_all_sprites(self):
        file_paths = [path for f in self.sprite_data for _, path, _ in self.sprite_data[f]["sprites"]]
        if not file_paths:
            self.log_panel.log("No unused sprite files to delete.", "info")
            messagebox.showinfo("Info", "No unused sprite files to delete.")
            return
        if messagebox.askyesno("Confirm Delete All Sprites", f"This will delete {len(file_paths)} unused sprite files.\nBack up your files first!\nContinue?"):
            deleted = delete_files(file_paths, self.trash_dir, self.project_name, self.backup_enabled.get(), self.backup_dir)
            self.log_panel.log(f"Deleted {len(deleted)} unused sprite files.", "warn")
            # Update sprite_data
            for f in self.sprite_data:
                self.sprite_data[f]["sprites"] = []
            # Refresh GUI
            if self.selected_folder:
                load_folder_contents(self.selected_folder, self.inner_frame, self.file_vars, self.sprite_data, self.layer_data, self.file_sizes, self.image_label, mode=self.display_mode)
            populate_folder_list(self.folder_listbox, self.sprite_data, self.layer_data)

    def undo_last(self):
        restored = undo_last_delete(self.trash_dir)
        if restored:
            self.log_panel.log("Undo successful. Last delete restored.", "success")
            # Rescan to restore data
            if self.display_mode == "sprites":
                self.scan_project()
            else:
                self.scan_layers()
        else:
            self.log_panel.log("No deletions found to undo.", "warn")

    def clear_all_backups(self):
        cleanup_old_backups(self.backup_dir, self.project_name, max_backups=0)
        self.log_panel.log("All backups cleared.", "info")

if __name__ == "__main__":
    root = Tk()
    app = GMS2Cleaner(root)
    root.mainloop()