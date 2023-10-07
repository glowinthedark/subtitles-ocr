#!/usr/bin/env python3

from pathlib import Path
import subprocess
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor


lock = threading.Lock()


def ocr_file(image):
    bucket_key = image.stem.replace("snap_", '')

    try:
        lock.acquire()
        # check if the file name is already in the dictionary, and skip it if so
        if bucket_key in ocr_dict:
            return
        lock.release()

        # run the ocr command on the file, and capture the output from stdout
        # !! mac m1/m2 only: use the version from https://github.com/glowinthedark/macOCR/releases
        proc = subprocess.run(["/usr/local/bin/OCR", "zh", "false", "false", image.absolute()],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)

        recognized_text = proc.stdout.decode()
        print(bucket_key, recognized_text)
        ocr_dict[bucket_key] = recognized_text
        err = proc.stderr.decode()

        if err:
            print("😱", err)
        else:
            lock.acquire()
            with open(results_file, "w") as f:
                json.dump(ocr_dict, f, ensure_ascii=False, indent=1)
    finally:
        lock.release()


if __name__ == '__main__':

    folder_name = sys.argv[1]
    results_file = sys.argv[2]

    # load the existing dictionary from json file, or create an empty one
    res_file = Path(results_file)
    if res_file.exists():
        ocr_dict = json.load(res_file.open(encoding='utf-8'))
    else:
        ocr_dict = {}

    ##### TODO: adjust the threadpool size to your liking depending on your system capacity
    with ThreadPoolExecutor(max_workers=50) as executor:
        img: Path
        for img in Path(folder_name).glob("*.png"):
            executor.submit(ocr_file, img)
