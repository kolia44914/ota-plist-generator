import os
import zipfile
import plistlib
import tkinter as tk
from tkinter import filedialog, messagebox

ipa_paths = [None] * 10
website_url = ""


def extract_metadata_from_ipa(ipa_path):
    with zipfile.ZipFile(ipa_path, 'r') as ipa:
        info_plist_path = None
        for name in ipa.namelist():
            if name.endswith("Info.plist") and "Payload/" in name:
                info_plist_path = name
                break

        if not info_plist_path:
            return None, None, None

        with ipa.open(info_plist_path) as plist_file:
            try:
                # Try reading as XML plist first
                plist_data = plistlib.load(plist_file)
            except Exception:
                # If fail, try reading as binary plist
                plist_file.seek(0)
                plist_data = plistlib.loads(plist_file.read())

            name = plist_data.get("CFBundleName", "Unknown")
            version = plist_data.get("CFBundleShortVersionString", "1.0")
            bundle_id = plist_data.get("CFBundleIdentifier", "com.example.unknown")
            return name, version, bundle_id


def generate_manifest(ipa_url, bundle_id, bundle_version, display_name, output_path):
    manifest = {
        "items": [{
            "assets": [{
                "kind": "software-package",
                "url": ipa_url
            }],
            "metadata": {
                "bundle-identifier": bundle_id,
                "bundle-version": bundle_version,
                "kind": "software",
                "title": display_name
            }
        }]
    }

    with open(output_path, 'wb') as f:
        plistlib.dump(manifest, f)


def process_ipas(output_dir):
    global website_url
    if not any(ipa_paths):
        messagebox.showwarning("No IPAs", "Please select at least one IPA file.")
        return

    if not website_url.strip():
        messagebox.showwarning("Missing Website URL", "Please enter the website URL.")
        return

    for ipa_path in ipa_paths:
        if ipa_path:
            name, version, bundle_id = extract_metadata_from_ipa(ipa_path)
            if not name:
                continue

            base_name = os.path.splitext(os.path.basename(ipa_path))[0]
            output_file = os.path.join(output_dir, f"manifest{base_name}.plist")
            ipa_url = f"{website_url}/{base_name}.ipa"  # No extra /ipa/ folder added

            generate_manifest(ipa_url, bundle_id, version, name, output_file)

    messagebox.showinfo("Done", f"Manifests saved to {output_dir}.")


def select_ipa(index):
    path = filedialog.askopenfilename(filetypes=[("IPA files", "*.ipa")])
    if path:
        ipa_paths[index] = path
        ipa_labels[index].config(text=os.path.basename(path))


def select_output_dir():
    folder = filedialog.askdirectory()
    if folder:
        process_ipas(folder)


def show_help():
    help_text = (
        "ipasign-devtool Instructions:\n\n"
        "1. Click each 'Select IPA' button to choose up to 10 .ipa files.\n"
        "2. Enter your website base URL (e.g., https://www.mywebsite.com/manifest).\n"
        "3. Click 'Generate Plists' and choose the output folder.\n"
        "4. Manifest .plist files will be saved there.\n\n"
        "These .plist files are for Over-the-Air installation (iOS method)."
        "Do NOT put the ipa file name into the url IT WILL BE ADDED AUTOMATICALLY"
    )
    messagebox.showinfo("How to Use", help_text)


# GUI Setup
root = tk.Tk()
root.title("Over-The-Air Manifest PLIST Generator")
root.geometry("550x700")
root.resizable(False, False)

title = tk.Label(root, text="Over-The-Air Manifest PLIST Generator", font=("Segoe UI", 18, "bold"))
title.pack(pady=10)

website_frame = tk.Frame(root)
website_frame.pack(pady=10)
tk.Label(website_frame, text="IPA File Link URL:", font=("Segoe UI", 10)).pack(side="left")
website_entry = tk.Entry(website_frame, width=50)
website_entry.pack(side="left", padx=5)


def update_website_url():
    global website_url
    website_url = website_entry.get().strip()


ipa_labels = []
for i in range(10):
    frame = tk.Frame(root)
    frame.pack(pady=3)
    btn = tk.Button(frame, text=f"Select IPA {i + 1}", command=lambda idx=i: select_ipa(idx), width=20)
    btn.pack(side="left")
    lbl = tk.Label(frame, text="No file selected", width=30, anchor="w")
    lbl.pack(side="left", padx=10)
    ipa_labels.append(lbl)

tk.Button(root, text="Generate Plists", command=lambda: [update_website_url(), select_output_dir()], bg="#ff7722", fg="white", width=30, height=2).pack(pady=20)
tk.Button(root, text="How to Use", command=show_help).pack(pady=5)

tk.Label(root, text="WARNING: this tool does NOT support ipa files with binary plist's, support for that will be added later.", font=("Segoe UI", 9)).pack(side="bottom", pady=10)

root.mainloop()
