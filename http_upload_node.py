import requests
import numpy as np
from PIL import Image
import io
import os
import uuid

class HttpUploadAny:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "upload_url": ("STRING", {"default": "http://localhost:8188/api/v1/upload_file"}),
            },
            "optional": {
                "image":     ("IMAGE",),       # image tensor se connect karo
                "file_path": ("STRING", {"forceInput": True}),  # video/audio path se connect karo
                "audio":     ("AUDIO",),       # audio tensor se connect karo
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("url",)
    FUNCTION = "upload"
    CATEGORY = "utils/upload"
    OUTPUT_NODE = True

    def upload(self, upload_url, image=None, file_path=None, audio=None):

        files = None

        # IMAGE tensor (image generation se)
        if image is not None:
            img_array = (image[0].cpu().numpy() * 255).astype(np.uint8)
            pil_img = Image.fromarray(img_array)
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            buf.seek(0)
            filename = f"{uuid.uuid4().hex}.png"
            files = {"file": (filename, buf, "image/png")}

        # File path (video/audio save node se)
        elif file_path and os.path.exists(file_path):
            ext = file_path.lower().split(".")[-1]
            mime_map = {
                "mp4": "video/mp4", "webm": "video/webm",
                "mov": "video/quicktime", "gif": "image/gif",
                "mp3": "audio/mpeg", "wav": "audio/wav",
                "flac": "audio/flac", "ogg": "audio/ogg",
                "png": "image/png", "jpg": "image/jpeg",
                "webp": "image/webp",
            }
            mime = mime_map.get(ext, "application/octet-stream")
            f = open(file_path, "rb")
            files = {"file": (os.path.basename(file_path), f, mime)}

        # AUDIO tensor
        elif audio is not None:
            import torchaudio
            buf = io.BytesIO()
            waveform = audio["waveform"].squeeze(0)
            sample_rate = audio["sample_rate"]
            torchaudio.save(buf, waveform, sample_rate, format="wav")
            buf.seek(0)
            filename = f"{uuid.uuid4().hex}.wav"
            files = {"file": (filename, buf, "audio/wav")}

        else:
            print("[HttpUpload] ❌ Kuch connect nahi kiya")
            return ("",)

        response = requests.post(upload_url, files=files)

        if response.status_code == 200:
            url = response.json().get("url", "")
            print(f"[HttpUpload] ✅ {url}")
            return (url,)
        else:
            print(f"[HttpUpload] ❌ {response.status_code}: {response.text}")
            return ("",)


NODE_CLASS_MAPPINGS = {"HttpUploadAny": HttpUploadAny}
NODE_DISPLAY_NAME_MAPPINGS = {"HttpUploadAny": "HTTP Upload (Any File)"}
