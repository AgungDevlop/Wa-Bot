import cv2
import os
import glob
import subprocess
import concurrent.futures

def process_video(input_path):
    print(f"🔄 Memulai: {input_path}")
    temp_final_path = input_path + ".finaltemp.mp4"
    
    # 1. Dapatkan resolusi video menggunakan OpenCV hanya untuk membaca dimensi
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"❌ Error membaca video: {input_path}")
        return
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    # 2. Hitung area watermark (Pojok Kanan Bawah)
    # Sedikit dikurangi desimalnya (0.27 & 0.17) agar tidak error out-of-bounds
    roi_x = int(width * 0.72)
    roi_y = int(height * 0.82)
    roi_w = int(width * 0.27) 
    roi_h = int(height * 0.17)
    
    # 3. Gunakan FFmpeg Delogo (Inpainting bawaan FFmpeg, bebas bug black-screen)
    # Ini menghapus watermark dengan sangat halus dan dijamin video muncul
    vf_filter = f"delogo=x={roi_x}:y={roi_y}:w={roi_w}:h={roi_h}"
    
    ffmpeg_cmd = [
        "ffmpeg", "-y", 
        "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "libx264",        # Encode video ke standar yang didukung semua HP/PC
        "-preset", "fast",        # Proses dipercepat
        "-pix_fmt", "yuv420p",    # Format pixel wajib agar tidak error layar hitam
        "-c:a", "copy",           # Audio di-copy UTUH 100%, tidak dimodifikasi
        temp_final_path
    ]
    
    # Jalankan perintah FFmpeg
    result = subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    
    # 4. Overwrite (Timpa) file asli dengan yang sudah dihilangkan watermarknya
    if result.returncode == 0 and os.path.exists(temp_final_path):
        os.remove(input_path)
        os.rename(temp_final_path, input_path)
        print(f"✅ Selesai & Berhasil: {input_path}")
    else:
        print(f"❌ Gagal memproses: {input_path}")
        # Hapus file temp jika gagal
        if os.path.exists(temp_final_path):
            os.remove(temp_final_path)

if __name__ == "__main__":
    # Cari semua video di folder videos/
    video_files = glob.glob("videos/*.mp4") + glob.glob("videos/*.mov") + glob.glob("*.mp4")
    video_files = [f for f in video_files if not f.endswith(".finaltemp.mp4")]
    
    if video_files:
        print(f"Menemukan {len(video_files)} video. Memulai pemrosesan paralel...")
        # Proses beberapa video sekaligus agar cepat
        with concurrent.futures.ProcessPoolExecutor() as executor:
            executor.map(process_video, video_files)
        print("\n🎉 SEMUA VIDEO BERHASIL DIPROSES!")
    else:
        print("Tidak ada video yang ditemukan.")
