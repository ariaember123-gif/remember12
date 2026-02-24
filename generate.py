import json
import os
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON body"})
            return

        # Pull FAL_KEY from Vercel environment variables
        fal_key = os.environ.get("FAL_KEY")
        if not fal_key:
            self._respond(500, {"error": "FAL_KEY environment variable not configured on server."})
            return

        prompt = payload.get("prompt", "").strip()
        model = payload.get("model", "fal-ai/flux/schnell").strip()
        image_size = payload.get("image_size", "square_hd")
        steps = payload.get("num_inference_steps", 4)

        if not prompt or not model:
            self._respond(400, {"error": "Missing required fields: prompt, model"})
            return

        fal_url = f"https://fal.run/{model}"
        fal_payload = json.dumps({
            "prompt": prompt,
            "image_size": image_size,
            "num_inference_steps": steps,
            "num_images": 1,
            "enable_safety_checker": True,
        }).encode("utf-8")

        req = urllib.request.Request(
            fal_url,
            data=fal_payload,
            headers={
                "Authorization": f"Key {fal_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._respond(200, data)

        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode("utf-8"))
                msg = err_body.get("detail") or err_body.get("message") or "FAL API error"
            except Exception:
                msg = f"FAL API error: HTTP {e.code}"
            self._respond(e.code, {"error": msg})

        except urllib.error.URLError as e:
            self._respond(502, {"error": f"Could not reach FAL API: {str(e.reason)}"})

        except Exception as e:
            self._respond(500, {"error": f"Server error: {str(e)}"})

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def _respond(self, status: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
