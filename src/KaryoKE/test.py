import io
import subprocess
from pathlib import Path
from werkzeug.utils import secure_filename

from app.config import KaryoKE_PATH, TEMP_FOLDER


print(f"KaryoKE_PATH: {KaryoKE_PATH}")
print(TEMP_FOLDER)
# BASE_DIR = Path(__file__).resolve().parent
# TEMP_FOLDER = BASE_DIR / "temp"
# SDDparser_PATH = BASE_DIR / "executable" / "karyoke"


def extract_cell_number(fn:str):
    image_name = fn.split('/')[-1]
    return image_name.split('_')[-3]


def get_images(output_file_type:str):
    images = list(TEMP_FOLDER.glob(f'*.{output_file_type}'))
    return [{"title": extract_cell_number(fn=str(f)), "path": f} for f in images]


def create_mock_uploaded_file(file_path, filename="mock_file.txt", content_type="text/plain"):
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    file_like_uploaded = io.BytesIO(file_bytes)
    file_like_uploaded.name = filename
    file_like_uploaded.filename = filename  # Flask uses .filename, Django uses .name
    file_like_uploaded.content_type = content_type
    file_like_uploaded.size = len(file_bytes)

    return file_like_uploaded


def clean_temp_files():
    for file in TEMP_FOLDER.iterdir():
        if file.is_file():
            file.unlink()


def run_karyoke_test():
    errors = []
    try:
        result = subprocess.run(
            #[SDDparser_PATH,  "-sdr", "executable/examples/exampleSDR_dicentrics_rings.txt", "--karyogram","human", "--save-png"], #, "-sdr SDDparser/examples/exampleSDR_dicentrics_rings.txt --karyogram human --save-png"],  # Pass arguments as a list
            [KaryoKE_PATH,
             "--sdr",
             "executable/examples/exampleSDR_dicentrics_rings.txt",
             "-kh",
             #"--save-png",
             TEMP_FOLDER
             ],
            capture_output=True,                 # Captures stdout and stderr
            text=True                            # Returns strings instead of bytes
        )
        if result.stderr:
            print('aaa')
            print("Errors:\n", result.stderr)

        elif 'successfully' in result.stdout:
            print('bbb')
            print("Output:\n", result.stdout)

        # 3. Check the results
        # print("Output:\n", result.stdout)
        # print("Errors:\n", result.stderr)
        # print("Exit Code:", result.returncode)
    except FileNotFoundError:
        errors.append("karyoke executable not found")
    except IOError as e:
        errors.append(e)
    return errors



def run_karyoke(file , file_type:str):
    errors = []
    fn = secure_filename(file.filename)
    if not fn:
        errors.append("Invalid file")
    if not file_type in ['sdd', 'sdr']:
        errors.append("Invalid file type")
    if not errors:
        try:
            clean_temp_files()
            filepath = Path(TEMP_FOLDER, fn)
            file.save(filepath)
            result = subprocess.run(
                [KaryoKE_PATH,
                 f"-{file_type}",
                 str(filepath),
                 "--karyogram",
                 "human",
                 "--save-svg"],
                capture_output=True,  # Captures stdout and stderr
                text=True  # Returns strings instead of bytes
            )
            if result.stderr:
                errors.append(result.stderr)
            elif 'successfully' in result.stdout:
                pass
            else:
                errors.append("Unknown error")
        except IOError as e:
            errors.append(e)
    return errors


if '__main__' == __name__:
    print(run_karyoke_test())

    # filename = "exampleSDR_multi.txt"
    # path_to_file = BASE_DIR / "executable" / "examples" / filename
    # file_uploaded = create_mock_uploaded_file(file_path=path_to_file, filename=filename)
    # print(file_uploaded.filename)
    # result = run_sdd_parser(file=file_uploaded , file_type='sdr')
    # print(result)

    # images = [Path('/static/exampleSDR_multi_cell2_karyogram_human.png'),
    #           Path('/static/exampleSDR_multi_cell4_karyogram_human.png'),
    #           Path('/static/exampleSDR_multi_cell1_karyogram_human.png'),
    #           Path('/static/exampleSDR_multi_cell3_karyogram_human.png'),
    #           Path('/static/exampleSDR_multi_cell0_karyogram_human.png')]
