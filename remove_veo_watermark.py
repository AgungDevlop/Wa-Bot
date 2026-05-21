import cv2
import numpy as np
import os
import glob

def remove_veo_watermark_frame(frame):
    h, w = frame.shape[:2]
    
    # Area watermark Veo 3 biasanya di pojok kanan bawah
    roi_x = int(w * 0.72)   # mulai dari 72% lebar
    roi_y = int(h * 0.82)   # mulai dari 82% tinggi
    roi_w = int(w * 0.28)
    roi_h = int(h * 0.18)
    
    if roi_x + roi_w > w or roi_y + roi_h > h:
        return frame
    
    roi = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w].copy()
    
    # Mask untuk inpainting
    mask = np.zeros((roi_h, roi_w), dtype=np.uint8)
    mask[:] = 255
    
    # Inpainting (cukup bagus untuk watermark semi-transparan)
    cleaned_roi = cv2.inpaint(roi, mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)
    
    frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w] = cleaned_roi
    return frame

def process_video(input_path, output_path):
    print(f"Processing: {input_path}")
    
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        cleaned = remove_veo_watermark_frame(frame)
        out.write(cleaned)
        
        frame_count += 1
        if frame_count % 200 == 0:
            print(f"  ✓ Processed {frame_count} frames")
    
    cap.release()
    out.release()
    print(f"✅ Selesai: {output_path}\n")

if __name__ == "__main__":
    os.makedirs("cleaned", exist_ok=True)
    
    video_files = glob.glob("videos/*.mp4") + glob.glob("videos/*.mov") + glob.glob("*.mp4")
    
    if not video_files:
        print("Tidak ada video ditemukan di folder videos/ atau root.")
    else:
        for video_path in video_files:
            output_path = os.path.join("cleaned", os.path.basename(video_path))
            process_video(video_path, output_path)
