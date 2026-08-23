from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import yt_dlp
import os
import uuid
import imageio_ffmpeg


# ==========================================
# CREATE APP
# ==========================================

app = FastAPI()


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# REQUEST MODEL
# ==========================================

class VideoRequest(BaseModel):
    url: str


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():
    return {
        "message": "YouTube Downloader API is running"
    }


# ==========================================
# VIDEO INFORMATION
# ==========================================

@app.post("/api/info")
def get_video_info(request: VideoRequest):

    if not request.url.startswith(
        (
            "https://www.youtube.com/",
            "https://youtu.be/",
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL"
        )

    options = {
        "quiet": True,
        "noplaylist": True,
    }

    try:

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                request.url,
                download=False
            )

        return {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "channel": info.get("uploader"),
        }

    except Exception as e:

        print("INFO ERROR:", e)

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ==========================================
# DOWNLOAD VIDEO
# ==========================================

@app.post("/api/download")
def download_video(request: VideoRequest):

    print("\n==============================")
    print("DOWNLOAD REQUEST")
    print("URL:", request.url)
    print("==============================")

    if not request.url.startswith(
        (
            "https://www.youtube.com/",
            "https://youtu.be/",
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL"
        )

    download_dir = "downloads"

    os.makedirs(
        download_dir,
        exist_ok=True
    )

    file_id = str(uuid.uuid4())

    output_template = os.path.join(
        download_dir,
        f"{file_id}.%(ext)s"
    )

    # Get FFmpeg supplied by imageio-ffmpeg
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    print("FFmpeg:", ffmpeg_path)

    options = {
        "format": "bestvideo+bestaudio/best",
        "noplaylist": True,

        "js_runtimes": {
            "deno": {}
        },
        "ffmpeg_location": ffmpeg_path,

        "merge_output_format": "mp4",

        "outtmpl": "downloads/%(title)s.%(ext)s",

        "quiet": False,
    }

    try:

        print("Starting yt-dlp...")

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                request.url,
                download=True
            )

            filename = ydl.prepare_filename(info)

        # After merging, yt-dlp should create MP4
        base_name = os.path.splitext(filename)[0]

        mp4_filename = base_name + ".mp4"

        if os.path.exists(mp4_filename):

            filename = mp4_filename

        elif not os.path.exists(filename):

            raise Exception(
                f"Downloaded file not found: {filename}"
            )

        print("DOWNLOAD SUCCESS")
        print("File:", filename)

        return FileResponse(
            filename,
            media_type="video/mp4",
            filename="video.mp4"
        )

    except Exception as e:

        print("\n==============================")
        print("ACTUAL DOWNLOAD ERROR")
        print(type(e).__name__)
        print(str(e))
        print("==============================\n")

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )