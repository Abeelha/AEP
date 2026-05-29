"""Watch the input/ folder; auto-edit any new image into output/ variants."""
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from . import pipeline, memory

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class _Handler(FileSystemEventHandler):
    def __init__(self, out_dir, n):
        self.out_dir = out_dir; self.n = n; self.seen = set()

    def _handle(self, path):
        if os.path.splitext(path)[1].lower() not in EXTS:
            return
        if path in self.seen:
            return
        self.seen.add(path)
        time.sleep(0.6)  # let the file finish writing
        try:
            meta = pipeline.process(path, self.out_dir, self.n)
            memory.log_batch(meta, ts=int(time.time()))
            memory.rebuild_digest()
            print(f"[AEP] {os.path.basename(path)} -> {len(meta['variants'])} variants "
                  f"({meta['scene']['scene']})  {meta['dest']}")
        except Exception as e:
            print(f"[AEP] FAILED {path}: {e}")

    def on_created(self, event):
        if not event.is_directory:
            self._handle(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._handle(event.dest_path)


def watch(in_dir, out_dir, n=5):
    os.makedirs(in_dir, exist_ok=True); os.makedirs(out_dir, exist_ok=True)
    h = _Handler(out_dir, n)
    obs = Observer(); obs.schedule(h, in_dir, recursive=False); obs.start()
    print(f"[AEP] watching {in_dir}  (drop images here; Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        obs.stop()
    obs.join()
