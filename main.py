import customtkinter as ctk
import threading
import re
import os
import subprocess
from pytubefix import YouTube

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class YoutubeDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Youtube video downloader: yaman kashyap")
        self.geometry("600x550")

        self.stream_options = {} 
        self.yt = None

        # --- UI Elements ---
        self.label = ctk.CTkLabel(self, text="YouTube Video & Audio Downloader", font=("Arial", 20, "bold"))
        self.label.pack(pady=20)

        self.url_entry = ctk.CTkEntry(self, width=450, placeholder_text="Paste Link Here...")
        self.url_entry.pack(pady=10)

        self.fetch_btn = ctk.CTkButton(self, text="Fetch All Formats", command=self.start_fetch_thread, fg_color="#1f538d")
        self.fetch_btn.pack(pady=10)

        self.format_menu = ctk.CTkOptionMenu(self, width=400, values=["No formats loaded"])
        self.format_menu.pack(pady=15)

        self.download_btn = ctk.CTkButton(self, text="Download (Video + Audio)", command=self.start_download_thread, state="disabled", fg_color="green")
        self.download_btn.pack(pady=20)

        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.pack(pady=5)

        self.progress_bar = ctk.CTkProgressBar(self, width=450)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)

    def start_fetch_thread(self):
        threading.Thread(target=self.fetch_formats, daemon=True).start()

    def fetch_formats(self):
        url = self.url_entry.get()
        if not url: return
        try:
            self.status_label.configure(text="Searching for streams...", text_color="yellow")
            self.yt = YouTube(url)
            self.stream_options = {}
            dropdown_values = []

            # We fetch all mp4 video streams
            streams = self.yt.streams.filter(file_extension='mp4').order_by('resolution').desc()

            for s in streams:
                if s.resolution:
                    # Logic: If it's adaptive, we add the best audio size to the total
                    if s.is_adaptive:
                        audio_size = self.yt.streams.get_audio_only().filesize_mb
                        total_size = s.filesize_mb + audio_size
                        type_label = "High Quality (Merged)"
                    else:
                        total_size = s.filesize_mb
                        type_label = "Standard (Direct)"

                    label = f"{s.resolution} | {type_label} | {total_size:.1f} MB"
                    
                    if label not in dropdown_values:
                        dropdown_values.append(label)
                        self.stream_options[label] = s

            self.format_menu.configure(values=dropdown_values)
            self.format_menu.set(dropdown_values[0])
            self.download_btn.configure(state="normal")
            self.status_label.configure(text="Formats loaded successfully!", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)[:45]}", text_color="red")

    def start_download_thread(self):
        threading.Thread(target=self.download_logic, daemon=True).start()

    def download_logic(self):
        selection = self.format_menu.get()
        selected_stream = self.stream_options.get(selection)
        if not selected_stream: return

        try:
            self.download_btn.configure(state="disabled")
            title_clean = re.sub(r'[\\/*?:"<>|]', "", self.yt.title)
            output_name = f"{title_clean}_{selected_stream.resolution}.mp4"

            if selected_stream.is_adaptive:
                # --- CASE 1: HQ Video (needs audio merge) ---
                self.status_label.configure(text="Downloading Video Track...", text_color="white")
                self.progress_bar.set(0.2)
                selected_stream.download(filename="v_temp.mp4")

                self.status_label.configure(text="Downloading Audio Track...")
                self.progress_bar.set(0.5)
                self.yt.streams.get_audio_only().download(filename="a_temp.mp4")

                self.status_label.configure(text="Merging tracks (FFmpeg)...")
                self.progress_bar.set(0.8)
                
                # Command to merge without re-encoding (copy) for speed
                cmd = ['ffmpeg', '-y', '-i', 'v_temp.mp4', '-i', 'a_temp.mp4', '-c', 'copy', output_name]
                subprocess.run(cmd, check=True, capture_output=True)
                
                # Clean up
                os.remove("v_temp.mp4")
                os.remove("a_temp.mp4")
            else:
                # --- CASE 2: Standard (already has audio) ---
                self.status_label.configure(text="Downloading Standard Video...")
                self.progress_bar.set(0.5)
                selected_stream.download(filename=output_name)

            self.progress_bar.set(1.0)
            self.status_label.configure(text=f"Saved: {output_name[:30]}...", text_color="green")

        except Exception as e:
            self.status_label.configure(text=f"Download Error: {str(e)[:45]}", text_color="red")
        finally:
            self.download_btn.configure(state="normal")

if __name__ == "__main__":
    app = YoutubeDownloader()
    app.mainloop()