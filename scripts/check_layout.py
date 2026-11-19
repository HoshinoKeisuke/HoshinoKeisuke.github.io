"""Check the generated pages using the runner's ChromeDriver and save PNG previews."""

import base64
import json
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


def driver(method, path, data=None):
    request = Request("http://127.0.0.1:9515" + path, method=method)
    request.add_header("Content-Type", "application/json")
    payload = None if data is None else json.dumps(data).encode()
    with urlopen(request, payload, timeout=40) as response:
        return json.load(response)["value"]


def screenshots(output):
    output.mkdir(parents=True, exist_ok=True)
    for attempt in range(20):
        try:
            if driver("GET", "/status")["ready"]:
                break
        except URLError:
            pass
        time.sleep(0.25)
    options = {"browserName": "chrome", "goog:chromeOptions": {"args": ["--headless", "--no-sandbox"]}}
    session = "/session/" + driver("POST", "/session", {"capabilities": {"alwaysMatch": options}})["sessionId"]
    try:
        for width, height in ((320, 740), (1280, 850)):
            driver("POST", session + "/goog/cdp/execute", {
                "cmd": "Emulation.setDeviceMetricsOverride",
                "params": {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False},
            })
            for path in ("/", "/papers/", "/talks/"):
                driver("POST", session + "/url", {"url": "http://127.0.0.1:8000" + path})
                state = driver("POST", session + "/execute/async", {"args": [], "script": """
                    const done = arguments[arguments.length - 1];
                    document.fonts.ready.then(() => done({
                      width: document.documentElement.scrollWidth,
                      h1: document.querySelector('main h1')?.textContent,
                      latin: document.fonts.check('24px "EB Garamond"', 'Hoshino'),
                      japanese: document.fonts.check('24px "Shippori Site"', '星野'),
                    }));
                """})
                if not state["h1"] or state["width"] > width or not state["latin"] or not state["japanese"]:
                    raise RuntimeError(f"{path} at {width}px: {state}")
                image = driver("GET", session + "/screenshot")
                filename = f"{path.strip('/') or 'home'}-{width}.png"
                (output / filename).write_bytes(base64.b64decode(image))
    finally:
        driver("DELETE", session)


if __name__ == "__main__":
    screenshots(Path(sys.argv[1]))
