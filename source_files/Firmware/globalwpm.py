import time, threading
from collections import deque
import hid
from pynput import keyboard

VID, PID = 0xFEED, 0x0000
USAGE_PAGE, USAGE = 0xFF60, 0x61
WINDOW = 5.0

presses = deque()
lock = threading.Lock()
held = set()

def on_press(key):
    if key in held:              # ignore OS key-repeat
        return
    held.add(key)
    with lock:
        presses.append(time.time())

def on_release(key):
    held.discard(key)

def find_device():
    for d in hid.enumerate(VID, PID):
        if d["usage_page"] == USAGE_PAGE and d["usage"] == USAGE:
            dev = hid.device()
            dev.open_path(d["path"])
            return dev
    return None

def current_wpm():
    now = time.time()
    with lock:
        while presses and now - presses[0] > WINDOW:
            presses.popleft()
        n = len(presses)
    return min(255, int(n / 5 * (60 / WINDOW)))

keyboard.Listener(on_press=on_press, on_release=on_release).start()

dev = None
while True:
    try:
        if dev is None:
            dev = find_device()
        if dev:
            dev.write([0x00, 0xAA, current_wpm()] + [0] * 30)  # 0x00 = report ID
    except Exception:
        dev = None
    time.sleep(0.25)