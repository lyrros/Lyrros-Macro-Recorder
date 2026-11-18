import json, os
from tkinter import BOTH, END, LEFT, RIGHT, SINGLE, Y, Canvas, Frame as TkFrame, Listbox
from tkinter.ttk import Button, Frame, Label
from utils.get_file import resource_path
from windows.popup import Popup


class SelectLanguage(Popup):
    def __init__(self, parent, main_app):
        tc = main_app.text_content["options_menu"]["settings_menu"]["lang_settings"]
        super().__init__(tc["title"], 440, 380, parent)
        self.resizable(False, False)
        main_app.prevent_record = True
        self.settings = main_app.settings
        self.items = []

        for lang in sorted(os.listdir(resource_path("langs"))):
            if not lang.endswith(".json"):
                continue
            with open(os.path.join(resource_path("langs"), lang), encoding="UTF-8") as f:
                c = json.load(f)
                self.items.append((c["information"]["lang_long"], c["information"]["lang_short"]))

        self.header_title = Label(self, text=tc["title"], font=("Helvetica Neue", 15, "bold"))
        self.header_title.pack(pady=(14, 2))
        self.header_sub = Label(self, text=tc["sub_text"], font=("Helvetica Neue", 11), foreground="#9e9e9e")
        self.header_sub.pack(pady=(0, 10))

        btns = Frame(self)
        btns.pack(side="bottom", pady=(8, 14))
        self.confirm_button = Button(btns, text=main_app.text_content["global"]["confirm_button"], width=12, command=lambda: self._apply(main_app))
        self.confirm_button.pack(side="left", padx=6)
        self.cancel_button = Button(btns, text=main_app.text_content["global"]["cancel_button"], width=12, command=self.destroy)
        self.cancel_button.pack(side="left", padx=6)

        border = TkFrame(self, bg="#3c3c3c", padx=1, pady=1)
        border.pack(fill=BOTH, expand=True, padx=24)
        wrap = Frame(border)
        wrap.pack(fill=BOTH, expand=True)

        sb = Canvas(wrap, width=10, height=1, bg="#262626", highlightthickness=0, bd=0)
        sb.pack(side=RIGHT, fill=Y)

        def _upd_sb(lo, hi):
            sb.delete("all")
            lo, hi = float(lo), float(hi)
            h = max(1, sb.winfo_height())
            y1 = max(2, int(lo * h) + 2)
            y2 = min(h - 2, max(y1 + 18, int(hi * h) - 2))
            sb.create_rectangle(2, y1, 8, y2, fill="#5c5c5c", outline="")

        self.lb = Listbox(wrap, yscrollcommand=_upd_sb, selectmode=SINGLE, activestyle="none", bg="#1e1e1e", fg="#e0e0e0", selectbackground="#2b5b84", selectforeground="#ffffff", font=("Helvetica Neue", 12), highlightthickness=0, bd=0, height=5)
        self.lb.pack(side=LEFT, fill=BOTH, expand=True)
        sb.bind("<Configure>", lambda e: _upd_sb(*self.lb.yview()))
        sb.bind("<B1-Motion>", lambda e: self.lb.yview_moveto(max(0.0, min(1.0, e.y / max(1, sb.winfo_height())))))
        sb.bind("<Button-1>", lambda e: self.lb.yview_moveto(max(0.0, min(1.0, e.y / max(1, sb.winfo_height())))))

        sel_idx = 0
        for idx, (lang_long, lang_short) in enumerate(self.items):
            self.lb.insert(END, f"  [{lang_short.upper()}]   {lang_long}")
            if lang_short == main_app.lang:
                sel_idx = idx
        self.lb.selection_set(sel_idx)
        self.lb.see(sel_idx)

        self.wait_window()
        main_app.prevent_record = False

    def _apply(self, main_app):
        sel = self.lb.curselection()
        if not sel:
            return
        self.setNewLanguage(self.items[sel[0]][1], main_app)

    def setNewLanguage(self, lang_code, main_app):
        self.settings.change_settings("Language", None, None, lang_code)
        main_app.load_language()
        main_app.version.refresh_locale_text()
        old_menu = main_app["menu"]
        if old_menu:
            main_app.nametowidget(old_menu).destroy()
        from windows.main.menu_bar import MenuBar
        main_app.menu = MenuBar(main_app)
        main_app.macro.main_menu = main_app.menu
        main_app.macro.macro_file_management.menu_bar = main_app.menu
        tc = main_app.text_content["options_menu"]["settings_menu"]["lang_settings"]
        self.title(tc["title"])
        self.header_title.configure(text=tc["title"])
        self.header_sub.configure(text=tc["sub_text"])
        self.confirm_button.configure(text=main_app.text_content["global"]["confirm_button"])
        self.cancel_button.configure(text=main_app.text_content["global"]["cancel_button"])
