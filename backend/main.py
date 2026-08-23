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

app = FastAPI(
    title="YouTube Downloader API",
    version="1.0.0"
)


# ==========================================
# CORS
# ==========================================

# Local development + deployed frontend
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

# Add deployed frontend URL through environment variable
frontend_url = os.getenv("FRONTEND_URL")

if frontend_url:
    ALLOWED_ORIGINS.append(frontend_url)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
# URL VALIDATION
# ==========================================

def validate_youtube_url(url: str):

    if not url.startswith(
        (
            "https://www.youtube.com/",
            "https://youtube.com/",
            "https://youtu.be/",
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid YouTube URL."
        )


# ==========================================
# YOUTUBE ERROR HANDLER
# ==========================================

def format_youtube_error(error):

    message = str(error)

    if (
        "Sign in to confirm" in message
        or "not a bot" in message
    ):
        return (
            "YouTube is currently blocking requests from "
            "the server. Please try another video later."
        )

    if "This video is not available" in message:
        return "This YouTube video is not available."

    if "Requested format is not available" in message:
        return (
            "The requested video format is not available. "
            "Please try another video."
        )

    return message


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    return {
        "message": "YouTube Downloader API is running",
        "status": "online"
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ==========================================
# VIDEO INFORMATION
# ==========================================

@app.post("/api/info")
def get_video_info(request: VideoRequest):

    validate_youtube_url(request.url)

    options = {
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
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
            detail=format_youtube_error(e)
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

    validate_youtube_url(request.url)

    # Create downloads directory
    download_dir = "downloads"

    os.makedirs(
        download_dir,
        exist_ok=True
    )

    # Unique filename
    file_id = str(uuid.uuid4())

    output_template = os.path.join(
        download_dir,
        f"{file_id}.%(ext)s"
    )

    # ======================================
    # FFmpeg
    # ======================================

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    print("FFmpeg:", ffmpeg_path)

    # ======================================
    # yt-dlp OPTIONS
    # ======================================

    options = {

        # Prefer MP4 video + M4A audio.
        # If unavailable, fall back to best available.
        "format": (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
            "bestvideo+bestaudio/best"
        ),

        "noplaylist": True,

        "ffmpeg_location": ffmpeg_path,

        "merge_output_format": "mp4",

        "outtmpl": output_template,

        "quiet": False,

        "no_warnings": False,
    }

    try:

        print("Starting yt-dlp...")

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                request.url,
                download=True
            )

            filename = ydl.prepare_filename(info)

        print("Initial filename:", filename)

        # ==================================
        # FIND FINAL MP4
        # ==================================

        base_name = os.path.splitext(filename)[0]

        mp4_filename = base_name + ".mp4"

        if os.path.exists(mp4_filename):

            filename = mp4_filename

        elif os.path.exists(filename):

            # File already exists
            pass

        else:

            # Search for file using UUID
            possible_files = []

            for file in os.listdir(download_dir):

                if file.startswith(file_id):

                    possible_files.append(
                        os.path.join(
                            download_dir,
                            file
                        )
                    )

            if possible_files:

                filename = possible_files[0]

            else:

                raise Exception(
                    "Downloaded file was not found."
                )

        print("DOWNLOAD SUCCESS")
        print("File:", filename)

        # ==================================
        # RETURN FILE
        # ==================================

        return FileResponse(
            filename,
            media_type="video/mp4",
            filename="video.mp4"
        )

    except Exception as e:

        print("DOWNLOAD ERROR:", e)

        raise HTTPException(
            status_code=400,
            detail=format_youtube_error(e)
        )