import json

first_req = {"t": "c", "d": {"t": "h", "d": {"ts": 1749792839639, "v": "5", "h": "s-usc1b-nss-2163.firebaseio.com", "s": "uQ70KYYRkDJZ8scVzTFlSNAaFMiXE2QH"}}}
first_res = {"t": "d", "d": {"r": 1, "a": "s", "b": {"c": {"sdk.js.6-3-4": 1}}}}
second_res = {"t": "d", "d": {"r": 2, "a": "q", "b": {"p": "/desk12", "q": {"sp": 1749792682791, "i": "updatedDate/time"}, "t": 1, "h": ""}}}

headers = {
    "Origin": "https://mobile.mako.co.il",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,he;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits"
}

# New config options for flash sound
PLAY_FLASH_ON_START = False  # Set to False to disable flash sound at startup
FLASH_VOLUME = 0.08  # 10% volume (0.0 to 1.0)