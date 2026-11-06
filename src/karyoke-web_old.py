from fasthtml.common import *
from uuid import uuid4

from app.helpers import prepare_temp_folder
from KaryoKE.karyoke import run_karyoke

from app.config import PORT

app,rt = fast_app()


def image_card(img):
    return Div(
        Img(src=img['path'], alt=img['title'], cls="w-full h-64 object-cover transform duration-300 ease-in-out group-hover:scale-105"),
        Div(
            P(img['title'], cls="text-sm font-semibold text-gray-800 m-0"),
            cls="p-4 bg-white"
        ),
        cls="group overflow-hidden rounded-xl shadow-md border border-gray-100 hover:shadow-xl transition-shadow duration-300"
    )


@rt('/', methods=['GET'])
def get(session):
    if 'session_id' not in session:
        session['session_id'] = str(uuid4())
    return Titled(
        "KaryoKE web",
        Form(hx_post="/run", hx_target="#karyogram")(
            #Form(
            Fieldset(
                Legend("Choose the input file type:"),
                # sdd
                Label(
                    Input(type="radio", name="input_file_type", value="sdd"),
                    "sdd"
                ),
                # sdr
                Label(
                    Input(type="radio", name="input_file_type", value="sdr", checked=True),
                    "sdr"
                ),
                # Legend("Choose the output file type:"),
                # # sdd
                # Label(
                #     Input(type="radio", name="output_file_type", value="png", checked=True),
                #     "png"
                # ),
                # # sdr
                # Label(
                #     Input(type="radio", name="output_file_type", value="svg"),
                #     "svg"
                # ),
                Label(Input(name="file_data", type="file", accept=".txt,.sdd,.sdr", required=True)),
                Button("Run", type="submit", style="width: auto; display: inline-block;"),
            ),
            Div( id="karyogram"),
        )
    )

@rt('/run', methods=['POST'])
async def run(session, file_data: UploadFile, input_file_type:str):  # , output_file_type:str):
    errors = []
    if not input_file_type in ['sdd', 'sdr']:
        errors.append("Invalid file type")
    else:
        try:
            session_id = session.get('session_id')
            user_temp_folder = prepare_temp_folder(session_id=session_id)
            file_content = await file_data.read()
            file_path = user_temp_folder / file_data.filename
            file_path.write_bytes(file_content)
            success, error = run_karyoke(file_path=file_path,
                                 input_file_type=input_file_type,
                                 user_folder=user_temp_folder)  # , output_file_type=output_file_type)
            if success:
                # success, html_file = get_html_file(user_temp_folder)
                # result = user_temp_folder / 'temp' / html_file
                return "The result was opened in a new tab."
            else:
                errors.append(error)

        except IOError as e:
            errors.append(e)

    return Div(
        H2("Error", cls="font-bold"),
        *[H3(e, style='color: #842029') for e in errors],
    )


if __name__ == "__main__":
    # 2. Change the port using the port parameter here
    serve(port=PORT)