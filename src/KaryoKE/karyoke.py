import os
import subprocess
from pathlib import Path

from app.config import KaryoKE_PATH, TIMEOUT_SECONDS


def run_karyoke(file_path: Path, input_file_type: str, user_folder: Path, genome: str = "human"):
    """Runs: karyoke --sdd|--sdr <file_path> -kh|-ko <user_folder>
    karyoke writes the summary file and the karyogram viewer (in user_folder/temp/) there. Returns (success, error)."""
    # Argument order is fixed by karyoke: --sdd|--sdr <file> [-kh|-ko] [output directory last].
    command = [str(KaryoKE_PATH), f"--{input_file_type}", str(file_path),
               "-kh" if genome == "human" else "-ko", str(user_folder)]

    # karyoke must never open a browser itself: the website shows the viewer. On the server there is no screen, so it
    # never does, but on a desktop it would. On WSL it opens the Windows browser with explorer.exe, which lives in the
    # Windows folders on PATH; a Linux-only PATH hides it, as does removing DISPLAY/WAYLAND_DISPLAY on a Linux desktop.
    # Then local tests behave like the server.
    environment = {key: value for key, value in os.environ.items() if key not in ("DISPLAY", "WAYLAND_DISPLAY")}
    environment["PATH"] = "/usr/local/bin:/usr/bin:/bin"

    try:
        result = subprocess.run(
            command,
            cwd=user_folder,
            env=environment,
            capture_output=True,  # Captures stdout and stderr
            text=True,            # Returns strings instead of bytes
            timeout=TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        return False, f"KaryoKE executable not found at {KaryoKE_PATH}"
    except subprocess.TimeoutExpired:
        return False, (f"Drawing took longer than {TIMEOUT_SECONDS} seconds and was stopped. "
                       "Try fewer cells, or use the karyoke program on your own computer.")
    except OSError as e:                                    # e.g. the executable is not marked executable (chmod +x)
        return False, f"KaryoKE could not be started: {e}"

    # The exit code is the reliable signal: 0 means every cell was processed. (Text on stderr alone does not mean
    # failure, and the wording of the success line may change between karyoke versions.)
    if result.returncode != 0:
        # karyoke's own messages, e.g. "--> SDR file line 12: ...", without the server's folder names.
        messages = (result.stdout + result.stderr).replace(f"{user_folder}/", "").strip()
        return False, messages or f"KaryoKE stopped with exit code {result.returncode}."

    return True, None
