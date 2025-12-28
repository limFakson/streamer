import subprocess
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FFmpegService:
    def transcode_to_hls(self, input_path: str, output_dir: str, job_id: str):
        """
        Transcodes input video file to HLS format (m3u8 + ts segments).
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Create subdirectories for variants (v0, v1)
        # FFmpeg with -hls_segment_filename .../v%v/... requires the directories to exist.
        for i in range(2):
            os.makedirs(os.path.join(output_dir, f"v{i}"), exist_ok=True)
            
        output_playlist = os.path.join(output_dir, "master.m3u8")
        
        # FFmpeg command for Adaptive Bitrate HLS transcoding
        # Generates 2 renditions: 720p, 360p
        command = [
            "ffmpeg",
            "-i", input_path,
            "-filter_complex", 
            "[0:v]split=2[v1][v2];"
            "[v1]scale=w=1280:h=720[v1out];"
            "[v2]scale=w=640:h=360[v2out]",
            
            # Stream 1: 720p
            "-map", "[v1out]", "-c:v:0", "libx264", "-preset", "veryfast", "-b:v:0", "2800k", "-maxrate:v:0", "2996k", "-bufsize:v:0", "4200k",
            "-map", "0:a", "-c:a:0", "aac", "-b:a:0", "128k", "-ac", "2",
            
            # Stream 2: 360p
            "-map", "[v2out]", "-c:v:1", "libx264", "-preset", "veryfast", "-b:v:1", "800k", "-maxrate:v:1", "856k", "-bufsize:v:1", "1200k",
            "-map", "0:a", "-c:a:1", "aac", "-b:a:1", "96k", "-ac", "2",
            
            # HLS settings
            "-f", "hls",
            "-hls_time", "10",
            "-hls_playlist_type", "vod",
            "-hls_flags", "independent_segments",
            "-hls_segment_type", "mpegts",
            
            # Variant map
            "-var_stream_map", "v:0,a:0 v:1,a:1",
            
            # Output pattern
            "-master_pl_name", "master.m3u8",
            "-hls_segment_filename", os.path.join(output_dir, "v%v", "segment_%03d.ts"),
            os.path.join(output_dir, "v%v", "playlist.m3u8")
        ]

        logger.info(f"Starting transcoding for job {job_id}...")
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Transcoding finished for job {job_id}")
            return output_playlist
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e.stderr.decode()}")
            raise e
        except Exception as e:
            logger.error(f"Transcoding error: {e}")
            raise e

ffmpeg_service = FFmpegService()
