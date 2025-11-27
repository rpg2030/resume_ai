# import os
# from werkzeug.utils import secure_filename

# def save_upload(file_obj, folder):
#     if not os.path.exists(folder):
#         os.makedirs(folder)

#     filename = secure_filename(file_obj.filename)
#     file_path = os.path.join(folder, filename)
#     file_obj.save(file_path)
#     return file_path









import os
from werkzeug.utils import secure_filename


def save_upload(file_obj, folder):
    """
    Saves an uploaded file into a folder.
    Creates folder if missing.
    """

    if not os.path.isdir(folder):
        # basic mkdir (not using exist_ok for clarity)
        os.makedirs(folder)

    # keep filename simple & safe
    fname = secure_filename(file_obj.filename)
    full_path = os.path.join(folder, fname)

    # write file to disk
    file_obj.save(full_path)

    return full_path
