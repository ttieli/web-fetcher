import datetime
import logging
import re
import urllib.parse
import urllib.request
import ssl
from pathlib import Path


# SSL context for unverified connections
ssl_context_unverified = ssl.create_default_context()
ssl_context_unverified.check_hostname = False
ssl_context_unverified.verify_mode = ssl.CERT_NONE


def sanitize_filename(name: str) -> str:
    invalid = set('/\\:*?"<>|\n\r\t')
    name = ''.join(ch if ch not in invalid else ' ' for ch in name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:160]


class SimpleDownloader:
    def __init__(self):
        self.downloadable_extensions = {
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf',
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'tiff', 'ico',
            'mp3', 'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'wav', 'ogg',
            'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'dmg', 'iso', 'exe', 'msi', 'deb', 'rpm',
            'xml', 'json', 'csv', 'sql', 'log', 'conf', 'cfg', 'ini', 'yaml', 'yml'
        }
    
    def try_download(self, url, ua, timeout, outdir):
        # Check if this is a downloadable file based on URL extension
        parsed_url = urllib.parse.urlparse(url)
        file_extension = parsed_url.path.lower().split('.')[-1] if '.' in parsed_url.path else ''
        
        if file_extension in self.downloadable_extensions:
            logging.info(f"Detected downloadable file with extension: {file_extension}")
            
            # Extract filename from URL
            filename = parsed_url.path.split('/')[-1] if parsed_url.path else f"download.{file_extension}"
            if not filename or filename == f".{file_extension}":
                # Generate filename from domain and timestamp if path is empty
                domain = parsed_url.hostname or 'unknown'
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{domain}_{timestamp}.{file_extension}"
            
            # Sanitize filename for filesystem
            filename = sanitize_filename(filename)
            
            # Ensure unique filename to avoid conflicts
            outdir = Path(outdir)
            outdir.mkdir(parents=True, exist_ok=True)
            base_path = outdir / filename
            final_path = base_path
            
            counter = 1
            while final_path.exists():
                name_part, ext_part = filename.rsplit('.', 1) if '.' in filename else (filename, '')
                if ext_part:
                    final_path = outdir / f"{name_part}_{counter}.{ext_part}"
                else:
                    final_path = outdir / f"{filename}_{counter}"
                counter += 1
            
            try:
                # Download binary file directly
                logging.info(f"Downloading file to: {final_path}")
                
                # Re-fetch the content as binary data
                req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Language": "zh-CN,zh;q=0.9"})
                with urllib.request.urlopen(req, timeout=timeout, context=ssl_context_unverified) as response:
                    # Write binary data to file
                    with open(final_path, 'wb') as f:
                        while True:
                            chunk = response.read(8192)  # Read in 8KB chunks
                            if not chunk:
                                break
                            f.write(chunk)
                
                file_size = final_path.stat().st_size
                logging.info(f"File downloaded successfully: {final_path} ({file_size} bytes)")
                print(str(final_path))
                return True  # Downloaded successfully, skip HTML processing
                
            except Exception as e:
                logging.error(f"Failed to download file: {e}")
                # Continue with normal HTML processing if download fails
                logging.info("Falling back to HTML processing")
        
        return False  # Not a downloadable file or download failed