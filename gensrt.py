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

    subtitles = []
    start_time = datetime.timedelta()

    sorted_int_keys = sorted([int(k) for k in ocr_dict.keys()])

    current_sub: srt.Subtitle = None

    for frame_number in sorted(ocr_dict.keys()):

        start_time: datetime.timedelta = datetime.timedelta(milliseconds=int(1000 * (float(frame_number) / 4 )))
        end_time = start_time + datetime.timedelta(milliseconds=500)
        body: str = ocr_dict.get(str(frame_number)).strip()

        if body:
            start_time: datetime.timedelta = datetime.timedelta(seconds=frame_number)
            end_time = start_time + datetime.timedelta(milliseconds=1000)

            sub = srt.Subtitle(None, start_time, end_time, body)

            if not current_sub:
                current_sub = sub
                continue

            # if it's duplicate content then add 1 second to current sub
            if current_sub.content == body:
                current_sub.end = current_sub.end + datetime.timedelta(milliseconds=1000)
            else:
                subtitles.append(current_sub)
                print(current_sub.to_srt())
                current_sub = sub

        else:
            if current_sub:
                subtitles.append(current_sub)
                print(current_sub.to_srt())
                current_sub = None

    return subtitles

json_input = sys.argv[1]
srt_output=sys.argv[2]

subtitles = generate_srt(json_input_file=json_input)

print('JSON input:', json_input)
print('SRT output:', srt_output)
Path(srt_output).write_text(srt.compose(subtitles), encoding='utf-8')
