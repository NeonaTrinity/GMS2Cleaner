import os
import shutil
from datetime import datetime
import zipfile

TRASH_FOLDER_NAME = "_GMS2Cleaner_Trash"

def delete_files(file_paths, trash_root, project_name, allow_backup=True, backup_dir=None):
    deleted_files = []
    os.makedirs(trash_root, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(trash_root, f"delete_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)

    if allow_backup and backup_dir:
        os.makedirs(backup_dir, exist_ok=True)
        zip_path = os.path.join(backup_dir, f"{project_name}_{timestamp}.zip")
        zipf = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
    else:
        zipf = None

    for path in file_paths:
        try:
            target_path = os.path.join(session_dir, os.path.basename(path))
            if os.path.isfile(path):
                shutil.move(path, target_path)
                deleted_files.append(path)
                if zipf:
                    zipf.write(target_path, arcname=os.path.join(project_name, os.path.basename(path)))
            elif os.path.isdir(path):
                shutil.move(path, target_path)
                deleted_files.append(path)
                if zipf:
                    for root, _, files in os.walk(target_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, session_dir)
                            zipf.write(file_path, arcname=os.path.join(project_name, rel_path))
        except Exception as e:
            print(f"Failed to delete: {path} – {e}")

    if zipf:
        zipf.close()
        cleanup_old_backups(backup_dir, project_name)

    # Remove empty directories
    for path in file_paths:
        parent = os.path.dirname(path)
        while parent and parent != trash_root and os.path.exists(parent):
            try:
                os.rmdir(parent)
            except OSError:
                break
            parent = os.path.dirname(parent)

    return deleted_files

def undo_last_delete(trash_root):
    if not os.path.isdir(trash_root):
        return False
    sessions = sorted(os.listdir(trash_root), reverse=True)
    if not sessions:
        return False
    latest = sessions[0]
    full_path = os.path.join(trash_root, latest)
    for file in os.listdir(full_path):
        src = os.path.join(full_path, file)
        dst = os.path.join(os.getcwd(), file)
        try:
            shutil.move(src, dst)
        except:
            pass
    shutil.rmtree(full_path, ignore_errors=True)
    return True

def cleanup_old_backups(backup_dir, project_name, max_backups=3):
    if not os.path.isdir(backup_dir):
        return
    files = [f for f in os.listdir(backup_dir) if f.startswith(project_name) and f.endswith(".zip")]
    files.sort()
    while len(files) > max_backups:
        oldest = files.pop(0)
        try:
            os.remove(os.path.join(backup_dir, oldest))
        except:
            pass