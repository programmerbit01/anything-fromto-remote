# Anything From/To Remote — ComfyUI Custom Node

Upload **any media** (Image / Video / Audio) to any HTTP endpoint directly from ComfyUI.

## Install

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/programmerbit01/anything-fromto-remote
```

Restart ComfyUI.

## Node: HTTP Upload (Any File)

**Category:** `utils/upload`

### Inputs

| Pin | Type | Description |
|---|---|---|
| `image` | IMAGE | Connect from any image generation node |
| `file_path` | STRING | Connect from video save node (VHS etc.) |
| `audio` | AUDIO | Connect from audio node |
| `upload_url` | STRING | Your HTTP endpoint URL |

### Output

| Pin | Type | Description |
|---|---|---|
| `url` | STRING | URL returned from server |

## Usage Examples

```
Image:  [VAE Decode] ──image──► [HTTP Upload (Any File)] ──url──► [Show Text]
Video:  [VHS Save]  ──file_path──► [HTTP Upload (Any File)]
Audio:  [Audio Node] ──audio──► [HTTP Upload (Any File)]
```

Set `upload_url` to your endpoint:
```
http://localhost:8188/api/v1/upload_file
```

## Supported Formats

- **Image:** PNG, JPG, WEBP (from IMAGE tensor)
- **Video:** MP4, WEBM, MOV, GIF (from file path)
- **Audio:** MP3, WAV, FLAC, OGG (from AUDIO tensor or file path)
