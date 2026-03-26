import requests
import numpy as np
from PIL import Image
import io
import os
import uuid

MIME_MAP = {
    "mp4": "video/mp4", "webm": "video/webm",
    "mov": "video/quicktime", "gif": "image/gif",
    "mp3": "audio/mpeg", "wav": "audio/wav",
    "flac": "audio/flac", "ogg": "audio/ogg",
    "png": "image/png", "jpg": "image/jpeg",
    "jpeg": "image/jpeg", "webp": "image/webp",
}

class HttpUploadAny:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "destination": (["http", "s3"],),
                "filename":    ("STRING", {"default": ""}),         # blank = auto UUID
                "img_format":  (["PNG", "JPEG", "WEBP"],),          # image format
                "img_quality": ("INT", {"default": 95, "min": 1, "max": 100}),  # jpg/webp quality
            },
            "optional": {
                # Media inputs
                "image":      ("IMAGE",),
                "file_path":  ("STRING", {"forceInput": True}),
                "audio":      ("AUDIO",),

                # HTTP options
                "upload_url": ("STRING", {"default": "http://localhost:8188/api/v1/upload_file"}),

                # S3 options (blank = use env vars)
                "s3_bucket":       ("STRING", {"default": ""}),
                "s3_key_prefix":   ("STRING", {"default": "outputs/"}),
                "s3_endpoint_url": ("STRING", {"default": ""}),   # MinIO / R2 ke liye
                "s3_access_key":   ("STRING", {"default": ""}),
                "s3_secret_key":   ("STRING", {"default": ""}),
                "s3_region":       ("STRING", {"default": "auto"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("url",)
    FUNCTION = "upload"
    CATEGORY = "utils/upload"
    OUTPUT_NODE = True

    # ─── Media → (bytes, ext, mime) ───────────────────────────────────────────

    def _prepare(self, filename, img_format, img_quality, image, file_path, audio):
        fmt = img_format.upper()
        ext_map = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}

        if image is not None:
            ext  = ext_map.get(fmt, "png")
            mime = MIME_MAP[ext]
            fname = self._fname(filename, ext)
            img_array = (image[0].cpu().numpy() * 255).astype(np.uint8)
            pil_img = Image.fromarray(img_array)
            buf = io.BytesIO()
            pil_img.save(buf, format=fmt, quality=img_quality)
            buf.seek(0)
            return buf, fname, mime

        elif file_path and os.path.exists(file_path):
            ext  = file_path.lower().rsplit(".", 1)[-1]
            mime = MIME_MAP.get(ext, "application/octet-stream")
            fname = self._fname(filename, ext) if filename.strip() else os.path.basename(file_path)
            return open(file_path, "rb"), fname, mime

        elif audio is not None:
            import torchaudio
            buf = io.BytesIO()
            waveform = audio["waveform"].squeeze(0)
            torchaudio.save(buf, waveform, audio["sample_rate"], format="wav")
            buf.seek(0)
            fname = self._fname(filename, "wav")
            return buf, fname, "audio/wav"

        return None, None, None

    def _fname(self, filename, ext):
        name = filename.strip()
        if not name:
            return f"{uuid.uuid4().hex}.{ext}"
        if "." not in name:
            name = f"{name}.{ext}"
        return name

    # ─── Upload ───────────────────────────────────────────────────────────────

    def upload(self, destination, filename="", img_format="PNG", img_quality=95,
               image=None, file_path=None, audio=None,
               upload_url="", s3_bucket="", s3_key_prefix="outputs/",
               s3_endpoint_url="", s3_access_key="", s3_secret_key="", s3_region="auto"):

        data, fname, mime = self._prepare(filename, img_format, img_quality, image, file_path, audio)

        if data is None:
            print("[HttpUpload] ❌ Kuch connect nahi kiya")
            return ("",)

        # ── S3 ──────────────────────────────────────────────────────────────
        if destination == "s3":
            try:
                import boto3
            except ImportError:
                print("[HttpUpload] ❌ boto3 install karo: pip install boto3")
                return ("",)

            kwargs = {}
            if s3_access_key.strip() and s3_secret_key.strip():
                kwargs["aws_access_key_id"]     = s3_access_key
                kwargs["aws_secret_access_key"] = s3_secret_key
            if s3_endpoint_url.strip():
                kwargs["endpoint_url"] = s3_endpoint_url
            if s3_region.strip():
                kwargs["region_name"] = s3_region

            s3     = boto3.client("s3", **kwargs)
            bucket = s3_bucket.strip() or os.environ.get("S3_BUCKET", "")
            key    = f"{s3_key_prefix.rstrip('/')}/{fname}"

            s3.upload_fileobj(data, bucket, key, ExtraArgs={"ContentType": mime})

            base = s3_endpoint_url.rstrip("/") if s3_endpoint_url.strip() else f"https://{bucket}.s3.amazonaws.com"
            url  = f"{base}/{key}"
            print(f"[HttpUpload] ✅ S3 → {url}")
            return (url,)

        # ── HTTP ─────────────────────────────────────────────────────────────
        url_target = upload_url.strip() or "http://localhost:8188/api/v1/upload_file"
        response = requests.post(url_target, files={"file": (fname, data, mime)})

        if response.status_code == 200:
            url = response.json().get("url", "")
            print(f"[HttpUpload] ✅ HTTP → {url}")
            return (url,)
        else:
            print(f"[HttpUpload] ❌ {response.status_code}: {response.text}")
            return ("",)


NODE_CLASS_MAPPINGS      = {"HttpUploadAny": HttpUploadAny}
NODE_DISPLAY_NAME_MAPPINGS = {"HttpUploadAny": "HTTP Upload (Any File)"}
