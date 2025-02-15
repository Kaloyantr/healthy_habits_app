from flask import current_app

def allowed_file(filename, allowed_extensions=None):
    """
    Checks if a given file has an allowed extension.
    If allowed_extensions is not specified, the setting ALLOWED_EXTENSIONS 
    from the application's configuration (current_app.config) will be used.
    """
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get("ALLOWED_EXTENSIONS", set())
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions
