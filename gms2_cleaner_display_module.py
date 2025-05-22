import os
from tkinter import *
from PIL import Image, ImageTk

def populate_folder_list(listbox, sprite_data, layer_data=None):
    listbox.delete(0, END)
    for folder in sorted(sprite_data):
        total_unused = len(sprite_data[folder]["sprites"])
        if layer_data and folder in layer_data:
            total_unused += len(layer_data[folder]["unused_folders"])
        if total_unused == 0:
            listbox.insert(END, f"{folder} (OK)")
        else:
            listbox.insert(END, f"{folder} ({total_unused} unused)")

def load_folder_contents(folder_name, frame, file_vars, sprite_data, layer_data, file_sizes, image_label, mode="sprites", search_term=""):
    for widget in frame.winfo_children():
        widget.destroy()
    file_vars.clear()

    def show_image(path):
        try:
            if os.path.isfile(path):
                img = Image.open(path).resize((96, 96))
                preview = ImageTk.PhotoImage(img)
                image_label.configure(image=preview)
                image_label.image = preview
            else:
                image_label.configure(text=f"Folder: {os.path.basename(path)}")
        except:
            image_label.configure(text="Error loading preview.")

    search_term = search_term.lower()

    if mode == "sprites" and folder_name in sprite_data:
        folder_data = sprite_data[folder_name]
        if folder_data["sprites"]:  # Check if there are unused sprites
            for name, path, size in folder_data["sprites"]:
                if search_term in name.lower():
                    var = IntVar()
                    if len(file_sizes.get((folder_name, size), [])) > 1:
                        var.set(1)  # Auto-check duplicates
                    cb = Checkbutton(frame, text=f"{name} ({size} B)", variable=var, anchor="w",
                                     command=lambda p=path: show_image(p))
                    cb.pack(fill=X, anchor="w")
                    file_vars.append((var, path))
        else:
            Label(frame, text="No unused sprites found.", anchor="w").pack(fill=X, anchor="w")
    elif mode == "layers" and folder_name in layer_data:
        for folder, folder_path, pngs in layer_data[folder_name]["unused_folders"]:
            if search_term in folder.lower():
                var = IntVar()
                cb = Checkbutton(frame, text=f"Folder: {folder} ({len(pngs)} PNGs)", variable=var, anchor="w",
                                 command=lambda p=folder_path: show_image(p))
                cb.pack(fill=X, anchor="w")
                file_vars.append((var, folder_path))
                for name, path, size in pngs:
                    if search_term in name.lower():
                        var = IntVar()
                        cb = Checkbutton(frame, text=f"  {name} ({size} B)", variable=var, anchor="w",
                                         command=lambda p=path: show_image(p))
                        cb.pack(fill=X, anchor="w")
                        file_vars.append((var, path))
        if not layer_data[folder_name]["unused_folders"]:
            Label(frame, text="No unused layer folders found.", anchor="w").pack(fill=X, anchor="w")