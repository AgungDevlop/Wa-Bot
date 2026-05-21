import cv2
import numpy as np
import os
import glob
import subprocess
import concurrent.futures

def process_video(input_path):
    print(f"🔄 Memulai: {input_path}")
    
    # Membuat path file temporary agar tidak bentrok saat membaca & menulis
    temp_cv_path = input_path + ".cvtemp.mp4"
    temp_final_path = input_path + ".finaltemp.mp4"
    
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"❌ Error membuka video: {input_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 1. PRE-COMPUTE MASK
    roi_x = int(width * 0.72)
    roi_y = int(height * 0.82)
    roi_w = int(width * 0.28)
    roi_h = int(height * 0.18)
    
    mask = np.full((roi_h, roi_w), 255, dtype=np.uint8)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_cv_path, fourcc, fps, (width, height))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if roi_x + roi_w <= width and roi_y + roi_h <= height:
            roi = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
            cleaned_roi = cv2.inpaint(roi, mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)
            frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w] = cleaned_roi
            
        out.write(frame)
            
    cap.release()
    out.release()
    
    # 2. RESTORE AUDIO (Menggabungkan audio asli ke file video baru)
    ffmpeg_cmd = [
        "ffmpeg", "-y", 
        "-i", temp_cv_path,
        "-i", input_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0", "-map", "1:a:0?",
        temp_final_path
    ]
    
    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Hapus file temporary dari OpenCV
    if os.path.exists(temp_cv_path):
        os.remove(temp_cv_path)
        
    # 3. OVERWRITE (Menimpa video lama dengan yang sudah bersih)
    if os.path.exists(temp_final_path):
        if os.path.exists(input_path):
            os.remove(input_path)  # Hapus video lama terlebih dahulu
        os.rename(temp_final_path, input_path)  # Ganti nama file temp menjadi nama asli
        print(f"✅ Selesai & Ditimpa: {input_path}")
    else:
        print(f"❌ Gagal memproses audio untuk: {input_path}")

if __name__ == "__main__":
    # Mengambil semua file video asli, abaikan file temporary jika ada sisa crash
    video_files = glob.glob("videos/*.mp4") + glob.glob("videos/*.mov") + glob.glob("*.mp4")
    video_files = [f for f in video_files if not (f.endswith(".cvtemp.mp4") or f.endswith(".finaltemp.mp4"))]
    
    if not video_files:
        print("Tidak ada video yang ditemukan untuk diproses.")
    else:
        print(f"Menemukan {len(video_files)} video. Memulai pemrosesan paralel...")
        with concurrent.futures.ProcessPoolExecutor() as executor:
            executor.map(process_video, video_files)
            
        print("\n🎉 SEMUA VIDEO BERHASIL DIPROSES!")
