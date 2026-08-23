import { useState } from "react";
import "./App.css";

function App() {
  const [url, setUrl] = useState("");
  const [video, setVideo] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const API_URL = "https://yt-downloader-sxb5.onrender.com";

  // Get video information
  const handleSubmit = async () => {
    if (!url.trim()) {
      setError("Please enter a YouTube URL");
      return;
    }

    setLoading(true);
    setError("");
    setVideo(null);

    try {
      const response = await fetch(`${API_URL}/api/info`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            url: url.trim(),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to get video information"
        );
      }

      setVideo(data);
    } catch (error) {
      console.error("Info error:", error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Download video
  const handleDownload = async () => {
    if (!url.trim()) {
      setError("Please enter a YouTube URL");
      return;
    }

    setDownloading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/download`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            url: url.trim(),
          }),
        }
      );

      if (!response.ok) {
        let message = "Download failed";

        try {
          const data = await response.json();
          message = data.detail || message;
        } catch {
          // Response wasn't JSON
        }

        throw new Error(message);
      }

      // Convert response to a file
      const blob = await response.blob();

      // Create temporary download URL
      const downloadUrl = window.URL.createObjectURL(blob);

      // Create download link
      const link = document.createElement("a");

      link.href = downloadUrl;
      link.download = "video.mp4";

      document.body.appendChild(link);

      // Start download
      link.click();

      // Clean up
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

    } catch (error) {
      console.error("Download error:", error);
      setError(error.message);
    } finally {
      setDownloading(false);
    }
  };

  // Convert seconds to MM:SS
  const formatDuration = (seconds) => {
    if (!seconds) {
      return "Unknown";
    }

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
  };

  return (
    <div className="app">
      <div className="container">

        <h1>YouTube Downloader</h1>

        <p className="subtitle">
          Download videos you have permission to download
        </p>

        {/* URL input */}
        <div className="download-box">

          <input
            type="text"
            placeholder="Paste YouTube URL here..."
            value={url}
            onChange={(e) => {
              setUrl(e.target.value);
              setError("");
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSubmit();
              }
            }}
          />

          <button
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? "Loading..." : "Get Video"}
          </button>

        </div>

        {/* Error message */}
        {error && (
          <p className="error">
            {error}
          </p>
        )}

        {/* Video information */}
        {video && (
          <div className="video-card">

            {/* Thumbnail */}
            {video.thumbnail && (
              <img
                src={video.thumbnail}
                alt={video.title || "Video thumbnail"}
                className="thumbnail"
              />
            )}

            <div className="video-info">

              {/* Title */}
              <h2>
                {video.title || "Unknown title"}
              </h2>

              {/* Channel */}
              <p>
                <strong>Channel:</strong>{" "}
                {video.channel || "Unknown"}
              </p>

              {/* Duration */}
              <p>
                <strong>Duration:</strong>{" "}
                {formatDuration(video.duration)}
              </p>

              {/* Download button */}
              <button
                onClick={handleDownload}
                className="download-button"
                disabled={downloading}
              >
                {downloading
                  ? "Downloading..."
                  : "Download Video"}
              </button>

            </div>

          </div>
        )}

      </div>
    </div>
  );
}

export default App;