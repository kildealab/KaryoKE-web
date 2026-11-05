import subprocess
from pathlib import Path

from app.config import KaryoKE_PATH


def run_karyoke(file_path:Path , input_file_type:str, user_folder:Path):  # , output_file_type:str):
    # log = {
    #     'success': False,
    #     'errors': []
    # }
    try:
        result = subprocess.run(
            [KaryoKE_PATH,
             f"--{input_file_type}",
             str(file_path),
             "-kh",
             user_folder
             # f"--save-{output_file_type}"
             ],
            # , "-sdr SDDparser/examples/exampleSDR_dicentrics_rings.txt --karyogram human --save-png"],  # Pass arguments as a list
            capture_output=True,  # Captures stdout and stderr
            text=True  # Returns strings instead of bytes
        )
        if result.stderr:
            return False, result.stderr
            # log['errors'].append(result.stderr)
        elif 'successfully' in result.stdout:
            return True, None
        else:
            return False, "Unknown error"
            # log['errors'].append("Unknown error")
    except FileNotFoundError:
        return False, "SDDparser executable not found"
        # log['errors'].append("SDDparser executable not found")
    except IOError as e:
        return False, e
        # log['errors'].append(e)
    # return log

#
# def run_karyoke(file_path:Path , input_file_type:str, user_folder:Path):  # , output_file_type:str):
#     log = {
#         'success': False,
#         'errors': []
#     }
#     result = subprocess.run(
#         [KaryoKE_PATH,
#          f"--{input_file_type}",
#          str(file_path),
#          "-kh",
#          user_folder
#          #f"--save-{output_file_type}"
#          ],
#         # , "-sdr SDDparser/examples/exampleSDR_dicentrics_rings.txt --karyogram human --save-png"],  # Pass arguments as a list
#         capture_output=True,  # Captures stdout and stderr
#         text=True  # Returns strings instead of bytes
#     )
#     print(result)
#     if result.stderr:
#         log['errors'].append(result.stderr)
#     elif 'successfully' in result.stdout:
#         log['success'] = True
#     else:
#         log['errors'].append("Unknown error")
#     return log
