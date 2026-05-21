import cv2
import numpy as np
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
import glob

def remove_veo_watermark_frame(frame):
    """
    Simple removal untuk Veo watermark (pojok kanan bawah)
    """
    h, w = frame.shape[:2]
    
    # Area watermark Veo biasanya di bottom-right (\~10-15% dari kanan bawah)
    roi_x = int(w * 0.75)   # mulai dari 75% lebar
    roi_y = int(h * 0.85)   # mulai dari 85% tinggi
    roi_w = int(w * 0.25)
    roi_h = int(h * 0.15)
    
    roi = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w].copy()
    
    # Simple inpainting (isi dengan pixel sekitar)
    mask = np.zeros((roi_h, roi_w), dtype=np.uint8)
    mask[:] = 255  # seluruh ROI
    
    # Inpaint
    cleaned_roi = cv2.inpaint(roi, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
    
    # Tempel kembali
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
        if frame_count % 100 == 0:
            print(f"Processed {frame_count} frames...")
    
    cap.release()
    out.release()
    print(f"Done: {output_path}")

if __name__ == "__main__":
    os.makedirs("cleaned", exist_ok=True)
    
    # Proses semua video di folder videos/
    for video_path in glob.glob("videos/*.mp4") + glob.glob("videos/*.mov"):
        output_path = os.path.join("cleaned", os.path.basename(video_path))
        process_video(video_path, output_path)
