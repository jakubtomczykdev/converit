import os
import threading
from flask import Flask, request, jsonify, send_file, send_from_directory
import yt_dlp
import imageio_ffmpeg

app = Flask(__name__, static_folder='public', static_url_path='')

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/info')
def get_info():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get('title', 'Unknown Title')
        thumbnail = info.get('thumbnail', '')
        
        formats_list = []
        added_resolutions = set()

        for f in info.get('formats', []):
            if f.get('vcodec') != 'none':
                height = f.get('height')
                # Filter to standard resolutions
                if height and height in [144, 240, 360, 480, 720, 1080, 1440, 2160]:
                    if height not in added_resolutions:
                        formats_list.append({
                            'itag': str(height), # Use height as a unique identifier for our frontend
                            'quality': f'{height}p',
                            'container': 'mp4', # Display mp4 because we merge it to mp4 anyway
                            'height': height,
                            'format_id': f.get('format_id') # YT-DLP's format ID (e.g. 137, 299, etc)
                        })
                        added_resolutions.add(height)

        # Sort formats highest resolution first
        formats_list.sort(key=lambda x: x['height'], reverse=True)

        return jsonify({
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats_list
        })

    except Exception as e:
        print(f"Error fetching info: {e}")
        return jsonify({'error': 'Failed to fetch video information'}), 500

def delete_file_after_delay(path, delay=10):
    def delayed_delete():
        import time
        time.sleep(delay)
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"Deleted {path}")
        except Exception as e:
            print(f"Error deleting {path}: {e}")
    
    thread = threading.Thread(target=delayed_delete)
    thread.start()

@app.route('/api/download')
def download_video():
    url = request.args.get('url')
    height = request.args.get('itag') # We mapped itag to height in /api/info
    
    if not url or not height:
        return "URL and itag (height) are required", 400

    # Ensure output directory exists
    output_dir = 'tmp_downloads'
    os.makedirs(output_dir, exist_ok=True)
    
    # yt-dlp option: download the requested height video + best audio
    format_string = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'

    ydl_opts = {
        'format': format_string,
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'ffmpeg_location': imageio_ffmpeg.get_ffmpeg_exe(),
        'quiet': True,
        'no_warnings': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
            # if we merge using ffmpeg, it might change the extension
            base, ext = os.path.splitext(downloaded_file)
            if not downloaded_file.endswith('.mp4') and os.path.exists(base + '.mp4'):
                downloaded_file = base + '.mp4'

        if not os.path.exists(downloaded_file):
            return "Download failed to create file", 500

        # Schedule deletion of the file so we don't leak disk space
        delete_file_after_delay(downloaded_file, delay=60) # delete after 60s
        
        return send_file(downloaded_file, as_attachment=True)

    except Exception as e:
        print(f"Error downloading: {e}")
        return "Failed to download video", 500

if __name__ == '__main__':
    app.run(port=3000, debug=True)
