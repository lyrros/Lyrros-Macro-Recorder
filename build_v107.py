import os, shutil, datetime, py_compile, subprocess, sys

root = os.path.expanduser("~/Desktop/LyrrosMacroRecorder")
src = os.path.join(root, "src")
app_out_dir = os.path.expanduser("~/Desktop/LyrrosMacroRecorder App")
icns_path = os.path.join(app_out_dir, "Lyrro's Macro Recorder v1.0.6.app", "Contents", "Resources", "app_icon.icns")

stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
bk_root = os.path.join(root, f"backups_v107_{stamp}")
before_dir = os.path.join(bk_root, "before")
after_dir = os.path.join(bk_root, "after")
os.makedirs(before_dir, exist_ok=True)
os.makedirs(after_dir, exist_ok=True)

targets = ["windows/help/about.py", "windows/main/main_app.py"]
for rel in targets:
    p = os.path.join(src, rel)
    dst = os.path.join(before_dir, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(p, dst)

p_about = os.path.join(src, "windows/help/about.py")
with open(p_about, "r", encoding="utf-8") as f:
    about_txt = f.read()

about_txt = about_txt.replace('FORK_VERSION = "v1.0.6 (Beta)"', 'FORK_VERSION = "v1.0.7 (Beta)"')
v107_entry = (
    'CHANGELOG_TEXT = (\n'
    '    "v1.0.7 (Beta)\\n"\n'
    '    "• Added \\"Lyrro\'s Macro Recorder Github\\" button above \\"Original GitHub\\" in About\\n\\n"\n'
)
if '"v1.0.7 (Beta)' not in about_txt:
    about_txt = about_txt.replace('CHANGELOG_TEXT = (\n', v107_entry, 1)

about_txt = about_txt.replace('500, 445', '500, 480', 1)

old_btns = '''        btns = Frame(self)
        btns.pack(side="bottom", pady=(8, 16))
        Button(btns, text="Changelog", width=12, command=lambda: ChangelogPopup(self)).pack(side="left", padx=5)
        Button(btns, text="Original GitHub", width=14, command=lambda: OpenUrl("https://github.com")).pack(side="left", padx=5)
        Button(btns, text="Close", width=10, command=self.destroy).pack(side="left", padx=5)'''

new_btns = '''        btns_wrap = Frame(self)
        btns_wrap.pack(side="bottom", pady=(8, 16))
        top_row = Frame(btns_wrap)
        top_row.pack(side="top", pady=(0, 6))
        Button(top_row, text="Lyrro's Macro Recorder Github", width=26, command=lambda: OpenUrl("https://github.com")).pack()
        btns = Frame(btns_wrap)
        btns.pack(side="top")
        Button(btns, text="Changelog", width=12, command=lambda: ChangelogPopup(self)).pack(side="left", padx=5)
        Button(btns, text="Original GitHub", width=14, command=lambda: OpenUrl("https://github.com")).pack(side="left", padx=5)
        Button(btns, text="Close", width=10, command=self.destroy).pack(side="left", padx=5)'''

if old_btns in about_txt:
    about_txt = about_txt.replace(old_btns, new_btns, 1)

with open(p_about, "w", encoding="utf-8") as f:
    f.write(about_txt)

p_main = os.path.join(src, "windows/main/main_app.py")
with open(p_main, "r", encoding="utf-8") as f:
    main_txt = f.read()
main_txt = main_txt.replace('text="v1.0.6"', 'text="v1.0.7"')
with open(p_main, "w", encoding="utf-8") as f:
    f.write(main_txt)

for rel in targets:
    p = os.path.join(src, rel)
    dst = os.path.join(after_dir, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(p, dst)

for dirpath, _, filenames in os.walk(src):
    for fn in filenames:
        if fn.endswith(".py"):
            py_compile.compile(os.path.join(dirpath, fn), doraise=True)

undo_path = os.path.join(bk_root, "undo_v107.py")
with open(undo_path, "w", encoding="utf-8") as f:
    f.write(f'''import os, shutil
for root_d, _, files in os.walk({before_dir!r}):
    for fn in files:
        full = os.path.join(root_d, fn)
        shutil.copy2(full, os.path.join({src!r}, os.path.relpath(full, {before_dir!r})))
print("Reverted v1.0.7 back to v1.0.6!")
''')

app_name = "Lyrro's Macro Recorder v1.0.7"
build_work = os.path.join(root, "build_v107_tmp")
shutil.rmtree(build_work, ignore_errors=True)
os.makedirs(build_work, exist_ok=True)

subprocess.run([
    sys.executable, "-m", "PyInstaller",
    "--noconfirm", "--clean", "--windowed",
    "--name", app_name,
    "--osx-bundle-identifier", "com.lyrrofame.lyrrosmacrorecorder",
    "--icon", icns_path,
    "--paths", src,
    "--collect-submodules", "windows",
    "--collect-submodules", "utils",
    "--collect-submodules", "macro",
    "--collect-submodules", "pynput",
    "--add-data", f"{os.path.join(src, 'assets')}:assets",
    "--add-data", f"{os.path.join(src, 'langs')}:langs",
    "--distpath", app_out_dir,
    "--workpath", os.path.join(build_work, "work"),
    "--specpath", build_work,
    os.path.join(src, "main.py"),
], check=True)

built_app = os.path.join(app_out_dir, f"{app_name}.app")
plist_path = os.path.join(built_app, "Contents", "Info.plist")
with open(plist_path, "r", encoding="utf-8") as f:
    plist = f.read().replace("<string>0.0.0</string>", "<string>1.0.7</string>")
with open(plist_path, "w", encoding="utf-8") as f:
    f.write(plist)

subprocess.run(["codesign", "--force", "--deep", "--sign", "-", built_app], check=True)
shutil.rmtree(os.path.join(app_out_dir, app_name), ignore_errors=True)
shutil.rmtree(build_work, ignore_errors=True)

zip_path = os.path.join(app_out_dir, "Lyrros-Macro-Recorder-v1.0.7-macOS.zip")
if os.path.exists(zip_path):
    os.remove(zip_path)
subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", built_app, zip_path], check=True)

print("SUCCESS! Built:", built_app)
print("Release Zip:", zip_path)
print("Instant Undo: python3", undo_path)
