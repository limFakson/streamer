import urllib.request
import urllib.parse
import json
import time
import os
import sys

API_URL = "http://localhost:8000"

def create_local_video():
    filename = "test_video.mp4"
    if not os.path.exists(filename):
        # Create a small dummy file with just bytes if ffmpeg fails
        # But we really want a valid video for HLS.
        # If ffmpeg is on system, use it. Generates Video + Audio (sine wave)
        # Explicitly map inputs 0:v and 1:a to output to ensure audio is present.
        cmd = f"ffmpeg -f lavfi -i testsrc=size=1280x720:rate=30:duration=5 -f lavfi -i sine=frequency=1000:duration=5 -c:v libx264 -c:a aac -map 0:v -map 1:a -shortest {filename} -y"
        ret = os.system(cmd)
        if ret != 0:
            print("FFmpeg failed locally. Creating dummy bytes.")
            with open(filename, "wb") as f:
                f.write(b"0" * 1024 * 1024)
    return filename

def run_test():
    print("Preparing test video...")
    filename = create_local_video()

    print(f"Uploading {filename}...")
    url = f"{API_URL}/api/v1/videos/upload"
    
    # Simple multipart upload using urllib is painful.
    # We will use curl via subprocess if possible, or construct multipart body manually.
    # Constructing multipart manually for robustness.
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    data = []
    data.append(f'--{boundary}')
    data.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"')
    data.append('Content-Type: video/mp4')
    data.append('')
    
    with open(filename, 'rb') as f:
        data.append(f.read().decode('latin-1'))
    
    data.append(f'--{boundary}--')
    data.append('')
    
    body = "\r\n".join(data).encode('latin-1')
    req = urllib.request.Request(url, data=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    
    try:
        with urllib.request.urlopen(req) as res:
            response = json.loads(res.read().decode('utf-8'))
            print(f"Upload response: {response}")
            job_id = response['job_id']
    except Exception as e:
        print(f"Upload failed: {e}")
        return

    # Poll status
    print(f"Polling job {job_id}...")
    for _ in range(30):
        time.sleep(2)
        try:
            with urllib.request.urlopen(f"{API_URL}/api/v1/videos/{job_id}") as res:
                job = json.loads(res.read().decode('utf-8'))
                print(f"Status: {job['status']}")
                
                if job['status'] == 'completed':
                    print("Job completed!")
                    stream_url = f"{API_URL}{job['hls_url']}"
                    print(f"Fetching master playlist: {stream_url}")
                    try:
                        with urllib.request.urlopen(stream_url) as sres:
                            master_content = sres.read().decode('utf-8')
                            print("Master Playlist content:")
                            print(master_content)
                            
                            # Parse one variant to verify
                            import re
                            # Find first m3u8 link (e.g. v0/playlist.m3u8)
                            match = re.search(r'(v\d+/playlist\.m3u8)', master_content)
                            if match:
                                variant_path = match.group(1)
                                variant_url = f"{API_URL}/stream/job/{job_id}/{variant_path}"
                                print(f"Fetching variant playlist: {variant_url}")
                                with urllib.request.urlopen(variant_url) as vres:
                                    print("Variant Playlist content:")
                                    print(vres.read().decode('utf-8')[:200])
                            else:
                                print("No variant found in master playlist!")

                    except Exception as e:
                        print(f"Failed to fetch playlist: {e}")
                    return
                
                if job['status'] == 'failed':
                    print("Job failed.")
                    print(job)
                    return
        except Exception as e:
             print(f"Polling error: {e}")

    print("Timeout.")

if __name__ == "__main__":
    run_test()
