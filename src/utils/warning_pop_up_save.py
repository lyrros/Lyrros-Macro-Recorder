from tkinter import messagebox


def confirm_save(main_app):
    """Just popup a window to say 'Do you want to save your recording?'
    So the user doesn't lose their last recording accidentally."""
    title = main_app.text_content.get("global", {}).get("confirm", "Confirm")
    return messagebox.askyesnocancel(title, "Do you want to save your recording?")
