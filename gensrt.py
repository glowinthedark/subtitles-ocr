#!/usr/bin/env python3

import datetime
import json
import sys
from pathlib import Path

import srt

def generate_srt(json_input_file=None):
    # get the list of image files in the img folder, sorted by their names

    with open(json_input_file, "r") as f:
        ocr_dict: dict = json.load(f)

    # the subtitle index, and a start time to keep track of the subtitle start time
    subtitles = []
    counter = 1
    start_time = datetime.timedelta()

    for frame_number in sorted(ocr_dict.keys()):

        frame_rate = 43 ######### TODO ########  change the video frame rate
        start_time: datetime.timedelta = datetime.timedelta(milliseconds=int(1000 * (float(frame_number) / 4 )))
        end_time = start_time + datetime.timedelta(milliseconds=500)
        body: str = ocr_dict.get(frame_number).strip()

        if body:
            subtitles.append(srt.Subtitle(None, start_time, end_time, body))
            print(counter, start_time, end_time, body)
            counter += 1
    return subtitles

json_input = sys.argv[1]
srt_output=sys.argv[2]

subtitles = generate_srt(json_input_file=json_input)

print('JSON input:', json_input)
print('SRT output:', srt_output)
Path(srt_output).write_text(srt.compose(subtitles), encoding='utf-8')
