"""KaryoKE website: upload or paste SDD/SDR data, then open the karyogram viewer or download the summary file.

Local testing:  python main.py                       (then open http://localhost:5001)
On the server:  gunicorn -k uvicorn_worker.UvicornWorker main:app   (see DEPLOY.md)
"""

import asyncio
import secrets

from fasthtml.common import *
from starlette.responses import FileResponse

from app.config import BASE_DIR, KEEP_MINUTES, MAX_INPUT_MB, MAX_JOBS, PORT, SECRET_KEY
from app.helpers import get_html_file, get_summary, get_user_folder, prepare_temp_folder, safe_filename
from KaryoKE.karyoke import run_karyoke

MAX_INPUT_BYTES = MAX_INPUT_MB * 1024 * 1024

# static_path: only files in static/ are served (FastHTML's default would serve files from the project folder itself).
# secret_key: FastHTML would otherwise write a .sesskey file into the working folder, which fails if the server's
# user may not write there. The site does not use sessions, so a random key per start is fine unless .env sets one.
app, rt = fast_app(
    static_path=str(BASE_DIR / "static"),
    secret_key=SECRET_KEY or secrets.token_hex(32),
    hdrs=(Link(rel="stylesheet", href="/style.css"),),
)

job_slots = asyncio.Semaphore(MAX_JOBS)


# ------------------------------------------
# Input page
# ------------------------------------------
def choice(name, value, text, checked=False):
    return Label(Input(type="radio", name=name, value=value, checked=checked), text)


@rt('/', methods=['GET'])
def get():
    return Titled(
        "KaryoKE karyograms",
        P("Upload or paste SDD or SDR data to see one karyogram per cell, and download the summary file. "
          f"Limit: {MAX_INPUT_MB} MB.", cls="lead"),
        Form(hx_post="/run", hx_target="#result", hx_disabled_elt="find button", hx_indicator="#busy")(
            Div(
                Fieldset(Legend("File type"),
                         choice("input_file_type", "sdr", "SDR (mutations)", checked=True),
                         choice("input_file_type", "sdd", "SDD (DNA damage)")),
                Fieldset(Legend("Genome"),
                         choice("genome", "human", "Human (realistic centromere positions)", checked=True),
                         choice("genome", "other", "Other (generic centromere positions)")),
                cls="grid",
            ),
            Fieldset(
                Legend("Data"),
                Div("Drop an SDD/SDR file here, or ",
                    Input(type="file", name="file_data", id="file", accept=".txt,.sdd,.sdr"), id="drop"),
                Textarea(name="data_text", id="text", rows=10, placeholder="...or paste the file contents here"),
                Small("A chosen file is used instead of the text box."),
            ),
            Button("Draw karyograms", type="submit"),
            Span("Drawing karyograms...", id="busy", cls="htmx-indicator", aria_busy="true"),
        ),
        Div(id="result"),
        Script(src="/input.js"),
    )


# ------------------------------------------
# Running karyoke
# ------------------------------------------
@rt('/run', methods=['POST'])
async def run(req):
    """Runs karyoke on the uploaded or pasted data and returns the result box shown under the form."""
    if int(req.headers.get("content-length", "0")) > MAX_INPUT_BYTES:
        return error_box(f"The data is larger than the {MAX_INPUT_MB} MB limit of this website. "
                         "Use the karyoke program on your own computer for files this big.")

    form = await req.form(max_part_size=MAX_INPUT_BYTES)       # The default limit for the paste box is only 1 MB
    input_file_type = form.get("input_file_type")
    genome = form.get("genome")

    if input_file_type not in ("sdd", "sdr") or genome not in ("human", "other"):
        return error_box("Please choose the file type and the genome.")

    upload = form.get("file_data")
    if upload is not None and getattr(upload, "filename", ""):    # An uploaded file wins over the text box
        name = safe_filename(upload.filename, default="uploaded")
        data = await upload.read()
    else:
        name = "pasted"
        data = form.get("data_text", "").encode("utf-8")

    if not data.strip():
        return error_box("No data given. Choose a file or paste SDD/SDR data into the box.")

    if job_slots.locked():                                      # Safeguard: a few big files at once could exhaust the server
        return error_box("The server is busy drawing other karyograms. Please try again in a minute.")

    async with job_slots:
        job_id, folder = prepare_temp_folder()
        file_path = folder / f"{name}.txt"
        file_path.write_bytes(data.replace(b"\r\n", b"\n"))       # Pasted text from Windows browsers uses CRLF
        # karyoke runs in a separate thread, so the site keeps answering other visitors while it draws.
        success, error = await asyncio.to_thread(run_karyoke, file_path=file_path, input_file_type=input_file_type,
                                                 user_folder=folder, genome=genome)

    if not success:
        return error_box("KaryoKE could not process this data. Its messages are below.", error)

    found_html, html_error = get_html_file(folder)
    if not found_html:
        return error_box(f"KaryoKE finished but the karyogram viewer is missing ({html_error}), "
                         "for example because no cell has data.")
    found_summary, _ = get_summary(folder)

    return Article(
        Header(Strong("Karyograms ready")),
        Div(
            A("Open karyogram viewer", href=f"/jobs/{job_id}/viewer", target="_blank", role="button"),
            A("Download summary file", href=f"/jobs/{job_id}/summary", role="button", cls="secondary outline")
            if found_summary else "",
            cls="actions",
        ),
        Footer(Small(f"The viewer opens in a new tab and has its own PNG/SVG downloads. "
                     f"These results are deleted from the server after {KEEP_MINUTES} minutes.")),
    )


# ------------------------------------------
# Results of a run
# ------------------------------------------
@rt('/jobs/{job_id}/viewer', methods=['GET'])
def viewer(job_id: str):
    folder = get_user_folder(job_id)
    found, viewer_path = get_html_file(folder) if folder else (False, None)
    if not found:
        return expired_page()
    return FileResponse(viewer_path, media_type="text/html")


@rt('/jobs/{job_id}/summary', methods=['GET'])
def summary(job_id: str):
    folder = get_user_folder(job_id)
    found, summary_path = get_summary(folder) if folder else (False, None)
    if not found:
        return expired_page()
    return FileResponse(summary_path, media_type="text/plain", filename=summary_path.name)


# ------------------------------------------
# Messages
# ------------------------------------------
def error_box(message, details=""):
    # Status 200 on purpose: htmx only shows answers with a success status.
    return Article(
        Header(Strong("Could not draw the karyograms"), cls="error"),
        P(message),
        Pre(details) if details else "",
    )


def expired_page():
    return Titled("Results no longer available",
                  P(f"Results are kept for {KEEP_MINUTES} minutes. Please run your data again."),
                  A("Back to KaryoKE", href="/", role="button"))


if __name__ == "__main__":
    serve(port=PORT)
