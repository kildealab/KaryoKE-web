# KaryoKE web

Web application written in Python (version 3.13) with FastHTML. 

### Requirements ###
* Since the web application is written in Python with the package and project manager [uv](https://docs.astral.sh/uv/), it is recommended to install and use uv.
* A compiled [KaryoKE](https://github.com/kildealab/KaryoKE) executable.

### Installation ###
1. Install dependencies.
   ```bash
   cd KaryoKE-web
   uv sync
   ```
2. Create a folder on your server to save temporary files (uploaded sdr or sdd files and the generated html files).
3. Configure environment.
   ```bash
   cp .env.example .env
   # Edit .env and set:
   TEMP_FOLDER=
   ```
   _Note: You may want to keep the original .env_template files for Git update compatibility._
4. Copy the karyoke executable file to the folder KaryoKE/executable/ 
_Note: A symlink won't work. This is a limitation of the Python package subprocess._
5. Run the web application.
     ```bash
   # Go to the source folder
   cd src
   
   #Start the fasthtml uvicorn development server
    uv run karyoke-web.py   
   ```
Open http://localhost:5001