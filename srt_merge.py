#!/usr/bin/env python3

import argparse
import sys
from datetime import timedelta
from pathlib import Path

# pip3 install srt
import srt

# if the difference between sub1 an sub2 slots are more than this value
# then sub2 will NOT be merged into the same sub1 time slot, but have its own slot
MAX_NEAREST_SECONDS = 3


def nearest(items, pivot):
    # https://stackoverflow.com/questions/32237862/find-the-closest-date-to-a-given-date/32237949#32237949
    return min(items, key=lambda x: abs(x.start - pivot))


def merge_files(args):
    srt1_path = Path(args.srt1)
    srt2_path = Path(args.srt2)
    num_mismatched_slots = 0
    unmatched_subs2 = []

    with srt1_path.open(encoding=args.encoding1) as fi1:
        subs1 = {s.index: s for s in srt.parse(fi1)}
        subs1_orig_length = len(subs1.keys())

    with srt2_path.open(encoding=args.encoding2) as fi2:
        subs2 = {s.index: s for s in srt.parse(fi2)}

    # iterate all subs in srt2 and find the closest EXISTING slot in srt1
    sub2: srt.Subtitle
    idx: int
    for idx, sub2 in subs2.items():
        start_sub2: timedelta = sub2.start

        # get the nearest sub by time
        sub1_nearest_slot: srt.Subtitle = nearest(subs1.values(), start_sub2)

        # only allow a MAX deviation between two slots in order to merge, otherwise add new slot
        diff_seconds = int(abs(sub1_nearest_slot.start.total_seconds() - sub2.start.total_seconds()))

        if sub1_nearest_slot.content.strip() == sub2.content.strip() or sub2.content.strip() in sub1_nearest_slot.content:
            print(f'''B already in A: SKIP merging!
                 A: {sub1_nearest_slot.content}
                 B: {sub2.content}      
    ''')
            continue

        if args.nearest_slot and diff_seconds < MAX_NEAREST_SECONDS:
            sub1_nearest_slot.content = f'{sub1_nearest_slot.content}<br>{sub2.content}'
            subs1[sub1_nearest_slot.index] = sub1_nearest_slot
        else:
            num_mismatched_slots += 1
            unmatched_subs2.append(sub2)
            sys.stderr.write(f'''🚨 Frames are too far apart to merge❗️❗️❗️
INDEX: {idx}
SUB #1 (NEAREST SLOT): {sub1_nearest_slot.to_srt()}
SUB #2: {sub2.to_srt()}
DIFF SECONDS: {diff_seconds}

''')

    if not args.output_file:
        generated_srt = srt1_path.parent / f'{srt1_path.stem}_MERGED_{srt1_path.suffix}'
    else:
        generated_srt = Path(args.output_file)

    with generated_srt.open(mode='w', encoding='utf-8') as fout:

        all_subs_including_unmatched = list(subs1.values()) + unmatched_subs2
        subs1_modified_length = len(all_subs_including_unmatched)
        fout.write(srt.compose(all_subs_including_unmatched))
        print(f'Generated file: {generated_srt.absolute()}')

    sys.stderr.write(f"{'SRT #A':<22}{args.srt1}\n")
    sys.stderr.write(f"{'SRT #B':<22}{args.srt2}\n")
    sys.stderr.write(f"{'Total slots #A BEFORE':<22}{subs1_orig_length}\n")
    sys.stderr.write(f"{'Total slots #A AFTER':<22}{subs1_modified_length}\n")
    sys.stderr.write(f"{'Total slots #B':<22}{len(subs2.keys())}\n")
    sys.stderr.write(f"{'Mismatched slots':<22}{num_mismatched_slots} (slots in #B with more than {MAX_NEAREST_SECONDS}s drift from #A)\n")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='merge SRT subtitles',
                                     usage="""
    Merge SRT subtitles:                                     
    \t{0} first.srt second.srt -o merged.srt
 """.format(Path(sys.argv[0]).name))

    parser.add_argument('srt1',
                        help='SRT-file-1')
    parser.add_argument('srt2',
                        help='SRT-file-2')
    parser.add_argument('--output-file', '-o',
                        default=None,
                        help='Output filename')
    parser.add_argument('--nearest-slot', '-n',
                        type=lambda x: (str(x).lower() in ['true', '1', 'yes', 'y']),
                        default=True,
                        help='Append B to nearest slot in A')
    parser.add_argument('--encoding1', '-e1',
                        default='utf-8',
                        help='Input file #1 encoding')
    parser.add_argument('--encoding2', '-e2',
                        default='utf-8',
                        help='Input file #2 encoding')
    args = parser.parse_args(sys.argv[1:])

    print(args)

    merge_files(args)