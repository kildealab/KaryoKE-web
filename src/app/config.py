from dotenv import dotenv_values
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
config = dotenv_values(BASE_DIR / '.env')
TEMP_FOLDER = Path(config.get('TEMP_FOLDER'))
KaryoKE_PATH = BASE_DIR / "KaryoKE" / "executable" / "karyoke"
