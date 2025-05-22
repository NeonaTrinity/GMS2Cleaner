import os
import json
import glob
import re
from collections import defaultdict

def fix_json_trailing_commas(json_str):
    """Remove trailing commas from JSON string to make it valid."""
    json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
    json_str = re.sub(r',\s*(\n\s*[\]}])', r'\1', json_str)
    return json_str

def scan_gms2_project(project_dir, log_fn=None, progress_callback=None):
    sprites_dir = os.path.join(project_dir, "sprites")
    sprite_data = defaultdict(lambda: {"sprites": [], "used": set()})
    file_sizes = defaultdict(list)
    used_frames_global = set()

    if not os.path.isdir(sprites_dir):
        raise FileNotFoundError("sprites folder not found in project.")

    yyp_files = glob.glob(os.path.join(project_dir, "*.yyp"))
    sprite_folders = set()
    if yyp_files:
        yyp_path = yyp_files[0]
        try:
            with open(yyp_path, "r", encoding="utf-8") as f:
                yyp_content = f.read()
                for line in yyp_content.splitlines():
                    if '"path": "sprites/' in line:
                        folder = line.split('"path": "sprites/')[1].split('/')[0]
                        sprite_folders.add(folder)
            if log_fn:
                log_fn(f"Found sprite folders in {yyp_path}: {', '.join(sprite_folders)}", "info")
        except Exception as e:
            if log_fn:
                log_fn(f"⚠ Error reading {yyp_path}: {e}", "error")

    folders = [f for f in os.listdir(sprites_dir) if os.path.isdir(os.path.join(sprites_dir, f)) and (not sprite_folders or f in sprite_folders)]
    total_folders = len(folders)
    for i, folder in enumerate(folders):
        if progress_callback:
            progress_callback((i + 1) / total_folders * 100)
        folder_path = os.path.join(sprites_dir, folder)
        yy_path = os.path.join(folder_path, f"{folder}.yy")
        used_pngs = set()

        if log_fn:
            log_fn(f"Scanning {yy_path}...")

        try:
            with open(yy_path, "r", encoding="utf-8") as f:
                yy_content = f.read()
                yy_content = fix_json_trailing_commas(yy_content)
                yy_data = json.loads(yy_content)
                for frame in yy_data.get("frames", []):
                    for key in ("name", "%Name"):
                        if key in frame and isinstance(frame[key], str):
                            png_name = f"{frame[key]}.png"
                            used_pngs.add(png_name)
                            used_frames_global.add(png_name)
                if log_fn and used_pngs:
                    log_fn(f"Found names in {folder}: {', '.join([n[:-4] for n in used_pngs])}", "info")
        except Exception as e:
            if log_fn:
                log_fn(f"⚠ Failed to read {yy_path}: {e}", "error")
            continue

        sprite_data[folder]["used"] = used_pngs

        # Scan only root folder, ignore layers
        for file in os.listdir(folder_path):
            path = os.path.join(folder_path, file)
            if file.lower().endswith(".png") and os.path.isfile(path):
                size = os.path.getsize(path)
                file_sizes[(folder, size)].append((file, path))
                if file not in used_pngs:
                    sprite_data[folder]["sprites"].append((file, path, size))

    if progress_callback:
        progress_callback(100)
    return sprite_data, file_sizes, used_frames_global

def scan_layers(project_dir, log_fn=None, progress_callback=None):
    sprites_dir = os.path.join(project_dir, "sprites")
    layer_data = defaultdict(lambda: {"unused_folders": [], "used_pngs": set()})

    if not os.path.isdir(sprites_dir):
        raise FileNotFoundError("sprites folder not found in project.")

    folders = [f for f in os.listdir(sprites_dir) if os.path.isdir(os.path.join(sprites_dir, f))]
    total_folders = len(folders)
    for i, folder in enumerate(folders):
        if progress_callback:
            progress_callback((i + 1) / total_folders * 100)
        folder_path = os.path.join(sprites_dir, folder)
        yy_path = os.path.join(folder_path, f"{folder}.yy")
        used_pngs = set()
        used_names = set()

        if log_fn:
            log_fn(f"Scanning layers for {yy_path}...")

        try:
            with open(yy_path, "r", encoding="utf-8") as f:
                yy_content = f.read()
                yy_content = fix_json_trailing_commas(yy_content)
                yy_data = json.loads(yy_content)
                for frame in yy_data.get("frames", []):
                    for key in ("name", "%Name"):
                        if key in frame and isinstance(frame[key], str):
                            used_names.add(frame[key])
                            used_pngs.add(f"{frame[key]}.png")
                if log_fn and used_names:
                    log_fn(f"Found names in {folder}: {', '.join(used_names)}", "info")
        except Exception as e:
            if log_fn:
                log_fn(f"⚠ Error reading {yy_path}: {e}", "error")
            continue

        layer_data[folder]["used_pngs"] = used_pngs

        # Collect root PNGs
        root_pngs = set()
        for file in os.listdir(folder_path):
            if file.lower().endswith(".png") and os.path.isfile(os.path.join(folder_path, file)):
                root_pngs.add(file)

        layers_path = os.path.join(folder_path, "layers")
        if os.path.isdir(layers_path):
            for subfolder in os.listdir(layers_path):
                subfolder_path = os.path.join(layers_path, subfolder)
                if os.path.isdir(subfolder_path):
                    has_matching_png = False
                    if f"{subfolder}.png" in root_pngs:
                        has_matching_png = True
                        if log_fn:
                            log_fn(f"Subfolder {subfolder} matches root PNG in {folder}", "info")
                    elif subfolder in used_names:
                        has_matching_png = True
                        if log_fn:
                            log_fn(f"Subfolder {subfolder} matches name in {folder}.yy", "info")
                    if not has_matching_png:
                        png_files = []
                        for root, _, files in os.walk(subfolder_path):
                            for file in files:
                                if file.lower().endswith(".png"):
                                    path = os.path.join(root, file)
                                    size = os.path.getsize(path)
                                    png_files.append((file, path, size))
                        layer_data[folder]["unused_folders"].append((subfolder, subfolder_path, png_files))
                        if log_fn:
                            log_fn(f"Found unused layer folder: {subfolder} in {folder}", "info")
                    else:
                        if log_fn:
                            log_fn(f"Skipped layer folder: {subfolder} in {folder} (used in .yy or has root PNG)", "info")

    if progress_callback:
        progress_callback(100)
    return layer_data