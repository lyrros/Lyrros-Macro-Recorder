import os
import plistlib
import shutil
import subprocess
import sys
import tempfile

root = os.path.abspath(".")
src = os.path.join(root, "src")
app_out_dir = os.path.expanduser("~/Desktop/LyrrosMacroRecorder App")
os.makedirs(app_out_dir, exist_ok=True)

app_name = "Lyrro's Macro Recorder v1.0.9"
bundle_id = "com.lyrrofame.lyrrosmacrorecorder"
version = "1.0.9"
app_filename = app_name + ".app"
zip_filename = "Lyrros-Macro-Recorder-v1.0.9-macOS.zip"

build_work = tempfile.mkdtemp(prefix="lyrros_v109_build_")
staging_dist = os.path.join(build_work, "dist")
pyinstaller_config = os.path.join(build_work, "pyinstaller_config")
os.makedirs(pyinstaller_config, exist_ok=True)
pyinstaller_env = os.environ.copy()
pyinstaller_env["PYINSTALLER_CONFIG_DIR"] = pyinstaller_config
target_app = os.path.join(app_out_dir, app_filename)
target_zip = os.path.join(app_out_dir, zip_filename)

try:
    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--clean", "--windowed",
            "--name", app_name,
            "--osx-bundle-identifier", bundle_id,
            "--icon", os.path.join(src, "assets/app_icon.icns"),
            "--paths", src,
            "--collect-submodules", "windows",
            "--collect-submodules", "utils",
            "--collect-submodules", "macro",
            "--collect-submodules", "pynput",
            "--hidden-import", "AppKit",
            "--hidden-import", "Foundation",
            "--hidden-import", "objc",
            "--add-data", f"{os.path.join(src, 'assets')}:assets",
            "--add-data", f"{os.path.join(src, 'langs')}:langs",
            "--distpath", staging_dist,
            "--workpath", os.path.join(build_work, "work"),
            "--specpath", os.path.join(build_work, "spec"),
            os.path.join(src, "main.py"),
        ],
        check=True,
        env=pyinstaller_env,
    )

    built_app = os.path.join(staging_dist, app_filename)
    plist_path = os.path.join(built_app, "Contents", "Info.plist")
    with open(plist_path, "rb") as plist_file:
        plist_data = plistlib.load(plist_file)
    plist_data["CFBundleName"] = app_name
    plist_data["CFBundleDisplayName"] = app_name
    plist_data["CFBundleIdentifier"] = bundle_id
    plist_data["CFBundleShortVersionString"] = version
    plist_data["CFBundleVersion"] = version
    macro_uti = "com.lyrrofame.lyrrosmacrorecorder.macro"
    plist_data["UTExportedTypeDeclarations"] = [
        {
            "UTTypeIdentifier": macro_uti,
            "UTTypeDescription": "Lyrro Macro Recording",
            "UTTypeConformsTo": ["public.json"],
            "UTTypeTagSpecification": {"public.filename-extension": ["lmr"]},
        }
    ]
    plist_data["CFBundleDocumentTypes"] = [
        {
            "CFBundleTypeName": "Lyrro Macro Recording",
            "CFBundleTypeRole": "Editor",
            "LSHandlerRank": "Owner",
            "LSItemContentTypes": [macro_uti],
            "CFBundleTypeExtensions": ["lmr"],
        }
    ]
    with open(plist_path, "wb") as plist_file:
        plistlib.dump(plist_data, plist_file)

    # Pinning the designated requirement to the bundle identifier instead of the
    # build's cdhash keeps macOS treating every rebuild as the same app, so
    # Input Monitoring / post-event grants survive future versions.
    stable_requirement = f'=designated => identifier "{bundle_id}"'
    subprocess.run(
        [
            "codesign", "--force", "--deep", "--sign", "-",
            "--identifier", bundle_id,
            "--requirements", stable_requirement,
            built_app,
        ],
        check=True,
    )

    staged_zip = os.path.join(build_work, zip_filename)
    subprocess.run(
        ["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", built_app, staged_zip],
        check=True,
    )

    backup_app = os.path.join(build_work, "previous.app")
    backup_zip = os.path.join(build_work, "previous.zip")
    if os.path.exists(target_app):
        shutil.copytree(target_app, backup_app, symlinks=True)
    if os.path.exists(target_zip):
        shutil.copy2(target_zip, backup_zip)

    installed_app = False
    try:
        if os.path.exists(target_app):
            shutil.rmtree(target_app)
        shutil.copytree(built_app, target_app, symlinks=True)
        installed_app = True
        shutil.copy2(staged_zip, target_zip)
    except Exception:
        if installed_app and os.path.exists(target_app):
            shutil.rmtree(target_app)
        if os.path.exists(backup_app):
            shutil.copytree(backup_app, target_app, symlinks=True)
        if os.path.exists(backup_zip):
            shutil.copy2(backup_zip, target_zip)
        raise

    print("SUCCESS! Built:", target_app)
    print("Updated archive:", target_zip)
finally:
    shutil.rmtree(build_work, ignore_errors=True)
