from dotenv import dotenv_values
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
config = dotenv_values(BASE_DIR / '.env')                   # Settings for this machine, see .env.example

TEMP_FOLDER = Path(config.get('TEMP_FOLDER', '/tmp/karyoke-web'))      # Each run gets its own folder in here
PORT = int(config.get('PORT', '5001'))                                  # Only used by `python main.py`
KaryoKE_PATH = BASE_DIR / "KaryoKE" / "executable" / "karyoke"

KEEP_MINUTES = int(config.get('KEEP_MINUTES', '60'))         # A run's viewer and summary can be opened for this long
MAX_INPUT_MB = int(config.get('MAX_INPUT_MB', '50'))         # Largest upload or paste
TIMEOUT_SECONDS = int(config.get('TIMEOUT_SECONDS', '300'))  # A karyoke run taking longer is stopped
MAX_JOBS = int(config.get('MAX_JOBS', '2'))                  # karyoke runs at the same time, per gunicorn worker
SECRET_KEY = config.get('SECRET_KEY')                        # Optional; FastHTML otherwise writes a .sesskey file
