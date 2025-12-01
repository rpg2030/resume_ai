import base64

def file_to_base64(file_obj):
    file_obj.seek(0)
    data = file_obj.read()
    return base64.b64encode(data).decode("utf-8")
