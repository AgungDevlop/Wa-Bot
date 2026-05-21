import cv2
import os
import glob
import subprocess
import concurrent.futures

def process_video(input_path):
    print(f"🔄 Memulai proses presisi: {input_path}")
    temp_final_path = input_path + ".finaltemp.mp4"
    
    # 1. Dapatkan resolusi video menggunakan OpenCV
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"❌ Error membaca video: {input_path}")
        return
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    # 2. Koordinat PRESISI untuk Veo 3 di pojok kanan bawah
    # Dibandingkan sebelumnya, kita perkecil areanya agar blur spot lebih kecil.
    # Nilai ini diasumsikan untuk video 16:9 standar.
    
    roi_w = int(width * 0.08)  # Lebih kecil (sekitar 8% lebar)
    roi_h = int(height * 0.05) # Lebih tipis (sekitar 5% tinggi)
    roi_x = int(width * 0.89)  # Lebih ke kanan (mulai dari 89% lebar)
    roi_y = int(height * 0.90) # Lebih ke bawah (mulai dari 90% tinggi)
    
    # Pastikan x + w dan y + h tidak melebihi resolusi asli
    if roi_x + roi_w > width: roi_w = width - roi_x - 1
    if roi_y + roi_h > height: roi_h = height - roi_y - 1

    # 3. Gunakan FFmpeg Delogo dengan parameter BAND minimal
    # 'band' adalah ketebalan garis batas untuk interpolasi. Kita setel ke 1 (minimal)
    # agar batas antara area bersih dan area diperbaiki terlihat tajam, bukan gradien blur.
    
    vf_filter = f"delogo=x={roi_x}:y={roi_y}:w={roi_w}:h={roi_h}:band=1"
    
    ffmpeg_cmd = [
        "ffmpeg", "-y", 
        "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "slow",       # Gunakan slow preset untuk kualitas encoding video lebih baik
        "-crf", "18",            # Kualitas video tinggi (semakin kecil angkanya, semakin tinggi kualitasnya. 18-22 adalah standar visual lossless)
        "-pix_fmt", "yuv420p",    # Wajib agar bisa diputar dimana-mana
        "-c:a", "copy",           # Copy audio asli UTUH
        temp_final_path
    ]
    
    # Jalankan perintah FFmpeg
    result = subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    
    # 4. Overwrite (Timpa) file asli
    if result.returncode == 0 and os.path.exists(temp_final_path):
        try:
            os.remove(input_path)
            os.rename(temp_final_path, input_path)
            print(f"✅ Selesai & Berhasil (Bersih): {input_path}")
        except OSError as e:
            print(f"❌ Gagal menimpa file asli: {e}")
    else:
        print(f"❌ Gagal memproses: {input_path}")
        error_output = result.stderr.decode('utf-8')
        if "Invalid specifications" in error_output:
             print("❌ Error: Koordinat area ROI tidak valid. Mungkin video terlalu kecil.")
        if os.path.exists(temp_final_path):
            os.remove(temp_final_path)

if __name__ == "__main__":
    # Cari semua video di folder videos/
    video_files = glob.glob("videos/*.mp4") + glob.glob("videos/*.mov") + glob.glob("*.mp4")
    
    # Abaikan file temporary yang mungkin sisa dari proses gagal sebelumnya
    video_files = [f for f in video_files if not f.endswith(".finaltemp.mp4")]
    
    if video_files:
        print(f"Menemukan {len(video_files)} video. Memulai pemrosesan paralel berkualitas tinggi...")
        # Proses beberapa video sekaligus
        with concurrent.futures.ProcessPoolExecutor() as executor:
            executor.map(process_video, video_files)
        print("\n🎉 SEMUA VIDEO BERHASIL DIPROSES DENGAN HASIL LEBIH BERSIH!")
    else:
        print("Tidak ada video yang ditemukan.")
        
