import os
from pathlib import Path
from app.config import TEMP_FOLDER

def extract_cell_number(fn:str):
    image_name = fn.split('/')[-1]
    return image_name.split('_')[-3]


def get_images(session_id:str, output_file_type:str):
    return sorted([f for f in os.listdir(TEMP_FOLDER / session_id) if f.lower().endswith(output_file_type)])


def get_html_file(user_temp_folder: Path):
    html_folder = user_temp_folder / 'temp'
    html_files = [f for f in os.listdir(html_folder) if f.lower().endswith('.html')]
    if len(html_files) == 1:
        print(html_files[0])
        return True, html_files[0]
    elif len(html_files) > 1:
        return False, "Too many html files found"
    else:
        return False, "No html file found"


def get_summary(session_id:str):
    txt_files = [f for f in os.listdir(TEMP_FOLDER / session_id) if f.lower().endswith('_summary.txt')]
    if len(txt_files) == 1:
        return True, txt_files[0]
    elif len(txt_files) > 1:
        return False, "Too many summaries found"
    else:
        return False, "No summary found"


def prepare_temp_folder(session_id:str):
    path = TEMP_FOLDER / session_id
    path.mkdir(parents=True, exist_ok=True)
    for file in path.iterdir():
        if file.is_file():
            file.unlink()
    return path
