import tkinter as tk
from tkinter import messagebox

def show_summary_popup(root, stats, unused_total_size, trash_path, backup_path, on_clear_all_backups):
    summary = tk.Toplevel(root)
    summary.title("Scan Summary")
    summary.geometry("500x400")

    text = tk.Text(summary, wrap="word")
    text.insert("end", f"📊 Scan Summary\n\n")
    text.insert("end", f"Total sprite folders scanned: {stats['total_folders']}\n")
    text.insert("end", f"Clean sprite folders: {stats['clean_folders']}\n")
    text.insert("end", f"Folders with unused files: {stats['flagged_folders']}\n")
    text.insert("end", f"Total unused files: {stats['unused_files']}\n")
    text.insert("end", f"Estimated space recoverable: {round(unused_total_size / 1024, 2)} KB\n\n")
    text.insert("end", f"Backup directory: {backup_path or 'Not enabled'}\n")
    text.insert("end", f"Trash path: {trash_path}\n")

    text.config(state="disabled")
    text.pack(fill="both", expand=True, padx=10, pady=10)

    button_frame = tk.Frame(summary)
    button_frame.pack(fill="x", pady=5)

    tk.Button(button_frame, text="Clear All Sprites", command=stats['clear_all_sprites']).pack(side="left", padx=5)
    tk.Button(button_frame, text="Clear All Layers", command=stats['clear_all_layers']).pack(side="left", padx=5)
    tk.Button(button_frame, text="Undo Last Delete", command=stats['undo']).pack(side="left", padx=5)

    if backup_path:
        tk.Button(button_frame, text="Clear All Backups", command=lambda: clear_backups_confirm(backup_path, on_clear_all_backups)).pack(side="right", padx=5)

def clear_backups_confirm(backup_path, clear_callback):
    confirm = messagebox.askyesno("Clear All Backups", f"""Delete all backups in:
{backup_path}?""")
    if confirm:
        clear_callback()
        messagebox.showinfo("Backups Deleted", "All backups have been cleared.")