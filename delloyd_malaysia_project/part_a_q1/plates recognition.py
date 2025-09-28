import os, re, cv2, tkinter as tk
from PIL import Image, ImageTk

# ====== UPDATE THESE PATHS ======
image_folder = r"C:\Users\Hp\Downloads\delloyd_malaysia_project\part_a_q1\images"
label_folder = r"C:\Users\Hp\Downloads\delloyd_malaysia_project\part_a_q1\labels"
# =================================

class_names = {0:'plate', 1:'character intact', 2:'character broken'}

# helper: find matching label file (case-insensitive base name)
def find_label_file(base):
    if not os.path.isdir(label_folder):
        return None
    for f in os.listdir(label_folder):
        if os.path.splitext(f)[0].lower() == base.lower():
            return os.path.join(label_folder, f)
    return None

# parse label file robustly (accepts spaces or commas); expects YOLO-style: class x y w h
def parse_label_file(path):
    intact = broken = parsed = skipped = 0
    with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            parts = re.split(r'[\s,]+', s)
            # we expect at least 5 parts: cls x y w h
            if len(parts) < 5:
                skipped += 1
                continue
            try:
                cls = int(float(parts[0]))
            except:
                skipped += 1
                continue
            if cls == 1:
                intact += 1
            elif cls == 2:
                broken += 1
            parsed += 1
    return intact, broken, parsed, skipped

# Processing per image: returns img, status, counts and debug info
def process_image(fname):
    img_path = os.path.join(image_folder, fname)
    base = os.path.splitext(fname)[0]
    img = cv2.imread(img_path)
    if img is None:
        print(f"[DEBUG] {fname}: cannot read image at {img_path}")
        return None, "Cannot read", 0, 0, None
    label_path = find_label_file(base)
    if label_path is None:
        print(f"[DEBUG] {fname}: NO label file found for base='{base}' in {label_folder}")
        return img, "No labels", 0, 0, None
    intact, broken, parsed, skipped = parse_label_file(label_path)
    if parsed == 0:
        status = "No character labels"
    else:
        status = "Broken" if broken > 0 else "Intact"
    print(f"[DEBUG] {fname}: label='{os.path.basename(label_path)}' parsed={parsed} skipped={skipped} intact={intact} broken={broken}")
    return img, status, intact, broken, os.path.basename(label_path)

# --- Simple GUI ---
root = tk.Tk()
root.title("Plate char check (debug)")
root.geometry("1000x700")

info_label = tk.Label(root, text="", font=('Helvetica', 14, 'bold'))
info_label.pack(pady=8)
img_label = tk.Label(root, bg="black")
img_label.pack(expand=True)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=8)
prev_btn = tk.Button(btn_frame, text="<< Previous", width=14)
next_btn = tk.Button(btn_frame, text="Next >>", width=14)
prev_btn.pack(side='left', padx=8); next_btn.pack(side='left', padx=8)

# load file list
if not os.path.isdir(image_folder):
    raise SystemExit(f"Image folder not found: {image_folder}")
image_files = sorted([f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg','.png','.jpeg'))])
if not image_files:
    raise SystemExit(f"No images found in {image_folder}")

current = 0

def show(i):
    global current
    current = i % len(image_files)
    fname = image_files[current]
    img, status, intact, broken, labelname = process_image(fname)
    if img is None:
        info_label.config(text=f"{fname} → {status}", fg="gray")
        img_label.config(image=''); img_label.image = None
        return
    # resize for display
    h, w = img.shape[:2]
    max_w, max_h = 900, 520
    scale = min(max_w / w, max_h / h, 1.0)
    new_w, new_h = max(1, int(w*scale)), max(1, int(h*scale))
    img_r = cv2.resize(img, (new_w, new_h))
    img_pil = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(img_r, cv2.COLOR_BGR2RGB)))
    img_label.config(image=img_pil); img_label.image = img_pil

    color = "green" if status=="Intact" else ("red" if status=="Broken" else "orange" if status in ("No labels","No character labels") else "gray")
    label_text = f"{fname}  |  {status}  |  intact={intact} broken={broken}"
    if labelname: label_text += f"  |  label={labelname}"
    info_label.config(text=label_text, fg=color)

def next_img():
    show(current + 1)
def prev_img():
    show(current - 1)

prev_btn.config(command=prev_img)
next_btn.config(command=next_img)

# show first image
show(0)
root.mainloop()
