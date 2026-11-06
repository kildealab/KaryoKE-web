import re
import shutil
import time
from pathlib import Path
from uuid import uuid4

from app.config import KEEP_MINUTES, TEMP_FOLDER

JOB_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def prepare_temp_folder():
    """Creates an empty folder for one run and returns (job_id, path). Old runs are deleted first.
    One folder per run, not per session: two runs from the same browser (e.g. two tabs) cannot overwrite each other,
    and an earlier run's viewer in temp/ can never be picked up by mistake."""
    delete_old_runs()
    job_id = uuid4().hex                                    # Random and unguessable: the job id is what lets a user open their results
    path = TEMP_FOLDER / job_id
    path.mkdir(parents=True)
    return job_id, path


def get_user_folder(job_id: str):
    """The folder of an existing run, or None if the id is malformed, unknown or expired."""
    if not JOB_ID_PATTERN.match(job_id or ""):              # Safeguard: the id comes from the URL, never use it as a path unchecked
        return None
    path = TEMP_FOLDER / job_id
    return path if path.is_dir() else None


def safe_filename(name: str, default: str = "pasted"):
    """A file name that is safe to create on the server: no folders, no spaces or special characters."""
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name or "").stem).strip("._")
    return stem or default


def get_html_file(user_temp_folder: Path):
    """The karyogram viewer karyoke wrote: <folder>/temp/<name>_karyograms_<human|other>.html.
    Returns (True, path) or (False, error). karyoke writes it into the folder itself if it could not create temp/."""
    for html_folder in (user_temp_folder / 'temp', user_temp_folder):
        html_files = sorted(html_folder.glob('*_karyograms_*.html'))
        if len(html_files) == 1:
            return True, html_files[0]
        elif len(html_files) > 1:
            return False, "Too many html files found"
    return False, "No html file found"


def get_summary(user_temp_folder: Path):
    """The summary karyoke writes for every run: <folder>/<name>_summary.txt. Returns (True, path) or (False, error)."""
    txt_files = sorted(user_temp_folder.glob('*_summary.txt'))
    if len(txt_files) == 1:
        return True, txt_files[0]
    elif len(txt_files) > 1:
        return False, "Too many summaries found"
    else:
        return False, "No summary found"


def delete_old_runs():
    """Deletes run folders older than KEEP_MINUTES, so the server's disk does not fill up."""
    if not TEMP_FOLDER.is_dir():
        return
    cutoff = time.time() - KEEP_MINUTES * 60
    for path in TEMP_FOLDER.iterdir():
        try:
            if path.is_dir() and path.stat().st_mtime < cutoff:
                shutil.rmtree(path, ignore_errors=True)
        except OSError:
            pass                                            # Another worker deleted it at the same moment
