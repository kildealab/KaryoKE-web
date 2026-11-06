"""KaryoKE website (FastHTML): paste or upload SDD/SDR data and get the karyogram viewer back.

The server runs the normal karyoke executable on each request:
    ./karyoke --sdd|--sdr <file> [-kh|-ko] <job folder>
On a server there is no screen, so karyoke does not try to open a browser and instead writes the viewer to
<job folder>/temp/<name>_karyograms_<human|other>.html. This script sends that page back and deletes the job folder.

Run for testing:     KARYOKE_PATH=/path/to/karyoke uvicorn app:app --port 5001
Run on the server:   see README.md (gunicorn with uvicorn workers, behind nginx, or the Dockerfile).
"""

import asyncio
import os
import re
import secrets
import subprocess
import tempfile
from pathlib import Path

from fasthtml.common import (A, Body, Button, Div, Fieldset, Form, H1, Head, Html, Input, Label, Legend, Link, Main, Meta, P,
                             Pre, Script, Small, Textarea, Title, fast_app, to_xml)
from starlette.requests import Request
from starlette.responses import Response


# ------------------------------------------
# Settings (environment variables, so nothing in this file has to change between machines)
# ------------------------------------------
HERE = Path(__file__).resolve().parent
KARYOKE_PATH = os.environ.get("KARYOKE_PATH", str(HERE / "karyoke"))
MAX_INPUT_MB = int(os.environ.get("KARYOKE_MAX_INPUT_MB", "50"))        # Largest paste or upload accepted
TIMEOUT_SECONDS = int(os.environ.get("KARYOKE_TIMEOUT_SECONDS", "300"))  # A run taking longer than this is stopped
MAX_JOBS = int(os.environ.get("KARYOKE_MAX_JOBS", "2"))                 # Runs at the same time per gunicorn worker

MAX_INPUT_BYTES = MAX_INPUT_MB * 1024 * 1024

# pico=False: our own small stylesheet instead of FastHTML's default Pico CSS.
# static_path: only files in static/ are served (by default FastHTML would serve files from the app folder itself).
# secret_key: FastHTML sets up sessions, which this site does not use; this stops it writing a .sesskey file.
app, rt = fast_app(
    pico=False,
    static_path=str(HERE / "static"),
    secret_key=os.environ.get("KARYOKE_SECRET_KEY", secrets.token_hex(32)),
    hdrs=(Link(rel="stylesheet", href="/style.css"),),
)

job_slots = asyncio.Semaphore(MAX_JOBS)


class KaryokeError(Exception):
    """A run that failed; message is shown to the user, details is karyoke's own terminal output."""

    def __init__(self, message, details="", status=422):
        super().__init__(message)
        self.message = message
        self.details = details
        self.status = status


# ------------------------------------------
# Pages
# ------------------------------------------
@rt("/")
def get():
    """The input page: file type, genome, a file drop area and a paste box."""
    def choice(name, value, text, checked=False):
        return Label(Input(type="radio", name=name, value=value, checked=checked), " ", text)

    return (
        Title("KaryoKE karyograms"),
        Main(
            H1("KaryoKE karyograms"),
            P(f"Paste SDD or SDR data, or drop a file, to see one karyogram per cell. Limit: {MAX_INPUT_MB} MB.", cls="lead"),
            # target="_blank": the viewer opens in a new tab, so the data stays here for another try (e.g. the other genome).
            Form(
                Fieldset(Legend("File type"),
                         choice("file_type", "sdr", "SDR (mutations)", checked=True),
                         choice("file_type", "sdd", "SDD (DNA damage)")),
                Fieldset(Legend("Genome"),
                         choice("genome", "human", "Human (realistic centromere positions)", checked=True),
                         choice("genome", "other", "Other (generic centromere positions)")),
                Fieldset(Legend("Data"),
                         Div("Drop an SDD/SDR file here, or ", Input(type="file", name="data_file", id="file"), id="drop"),
                         Textarea(name="data_text", id="text", placeholder="...or paste the file contents here"),
                         Small("A chosen file is used instead of the text box.")),
                Div(Button("Draw karyograms", type="submit", name="action", value="viewer"),
                    Button("Download summary file", type="submit", name="action", value="summary"),
                    cls="buttons"),
                method="post", action="/draw", enctype="multipart/form-data", target="_blank",
            ),
        ),
        Script(src="/input.js"),
    )


@rt("/draw")
async def post(req: Request):
    """Runs karyoke on the submitted data. action=viewer returns the karyogram viewer, action=summary the summary file."""
    if int(req.headers.get("content-length", "0")) > MAX_INPUT_BYTES:
        return error_page(f"The data is larger than the {MAX_INPUT_MB} MB limit of this website. "
                          "Use the karyoke program on your own computer for files this big.", status=413)

    form = await req.form(max_part_size=MAX_INPUT_BYTES)       # Starlette's default limit for the paste box is only 1 MB
    file_type = form.get("file_type")                           # "sdd" or "sdr"
    genome = form.get("genome")                                 # "human" or "other"
    action = form.get("action", "viewer")

    if file_type not in ("sdd", "sdr") or genome not in ("human", "other") or action not in ("viewer", "summary"):
        return error_page("Please choose the file type and the genome.", status=400)

    data, name = await read_input(form)
    if not data.strip():
        return error_page("No data given. Paste SDD/SDR data into the box or choose a file.", status=400)

    if job_slots.locked():                                      # Safeguard: a few big files at once could exhaust the server
        return error_page("The server is busy drawing other karyograms. Please try again in a minute.", status=503)

    async with job_slots:
        try:
            # karyoke runs in a separate thread, so other visitors' pages keep loading while it draws.
            body = await asyncio.to_thread(run_karyoke, data, name, file_type, genome, action == "viewer")
        except KaryokeError as error:
            return error_page(error.message, error.details, status=error.status)

    if action == "summary":
        return Response(body, media_type="text/plain",
                        headers={"Content-Disposition": f'attachment; filename="{name}_summary.txt"'})

    return Response(body, media_type="text/html",
                    headers={"Content-Disposition": f'inline; filename="{name}_karyograms_{genome}.html"'})


# ------------------------------------------
# Helpers
# ------------------------------------------
async def read_input(form):
    """Returns (text, name). An uploaded file wins over the text box; the name is used for the viewer title and downloads."""
    upload = form.get("data_file")

    if upload is not None and getattr(upload, "filename", ""):
        name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(upload.filename).stem).strip("._") or "uploaded"   # Safe as a file name
        return (await upload.read()).decode("utf-8", errors="replace"), name

    return form.get("data_text", ""), "pasted"


def run_karyoke(data, name, file_type, genome, draw):
    """Runs karyoke on the data in a temporary job folder and returns the viewer (or summary) it wrote, as bytes."""
    with tempfile.TemporaryDirectory(prefix="karyoke-") as folder:
        job = Path(folder)
        input_path = job / f"{name}.txt"
        input_path.write_text(data.replace("\r\n", "\n"), encoding="utf-8")   # Pasted text from Windows browsers uses CRLF

        # Argument order is fixed by karyoke: --sdd|--sdr <file> [-kh|-ko] [output directory last].
        command = [KARYOKE_PATH, f"--{file_type}", str(input_path)]
        if draw:
            command.append("-kh" if genome == "human" else "-ko")
        command.append(str(job))

        # No DISPLAY/WAYLAND_DISPLAY: karyoke then never tries to open a browser on the server.
        environment = {key: value for key, value in os.environ.items() if key not in ("DISPLAY", "WAYLAND_DISPLAY")}

        try:
            result = subprocess.run(command, cwd=job, env=environment, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            raise KaryokeError(f"Drawing took longer than {TIMEOUT_SECONDS} seconds and was stopped. "
                               "Try fewer cells, or use the karyoke program on your own computer.")
        except OSError as error:                                # e.g. KARYOKE_PATH is wrong: a server setup problem, not the user's
            print(f"Could not start karyoke at {KARYOKE_PATH}: {error}", flush=True)
            raise KaryokeError("The website could not start KaryoKE. Please tell the site's maintainer.", status=500)

        terminal_output = (result.stdout + result.stderr).replace(f"{job}/", "").strip()   # Hide the server's temp folder from users

        output = (job / "temp" / f"{name}_karyograms_{genome}.html") if draw else (job / f"{name}_summary.txt")
        if not output.is_file() and draw:
            output = job / f"{name}_karyograms_{genome}.html"   # karyoke falls back to the output folder if it cannot create temp/

        if result.returncode != 0 or not output.is_file():
            raise KaryokeError("KaryoKE could not process this data. Its messages are below.", terminal_output)

        return output.read_bytes()                              # Read now: the job folder is deleted when this block ends


def error_page(message, details="", status=400):
    # A full page built by hand, because FastHTML's automatic page wrapping always answers with status 200.
    page = Html(
        Head(Meta(charset="utf-8"), Meta(name="viewport", content="width=device-width, initial-scale=1"),
             Title("KaryoKE: could not draw"), Link(rel="stylesheet", href="/style.css")),
        Body(Main(
            H1("Could not draw the karyograms", cls="error"),
            P(message),
            Pre(details) if details else "",
            P(A("Back", href="/")),
        )),
    )
    return Response("<!doctype html>\n" + to_xml(page), media_type="text/html", status_code=status)
