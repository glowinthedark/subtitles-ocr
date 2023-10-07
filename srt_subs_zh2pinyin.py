#!/usr/bin/env python3

# also see https://github.com/tkarabela/pysubs2

# DEPENDENCIES:
# pip install -U srt opencc pypinyin hanzidentifier

# URL: https://gist.github.com/glowinthedark/83daa9531dd8c4cc3963e55c1a4f3b1c
# Add pinyin subtitles to chinese mandarin SRT subtitles;
# optionally also add traditional (-t) or existing simplified;
# or simplified (-s) to existing traditional

# Examples:
# srt_subtitles_append_pinyin.py subtitles.chi.srt -o subtitles.chi.with.pinyin.srt

# convert from custom encoding, ie. big5
# srt_subtitles_append_pinyin.py subtitles.chi.srt -o subtitles.chi.with.pinyin.srt -e big5


# requirements:
# python -m pip install -U srt opencc pypinyin

import argparse
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Generator
from typing import List

import srt                   # https://github.com/cdown/srt
from opencc import OpenCC    # https://github.com/BYVoid/OpenCC
from pypinyin import pinyin  # https://github.com/mozillazg/python-pinyin

try:
    import hanzidentifier
except ImportError:
    print('WARN: cannot do simp/trad normalization! hanzidentifier not installed! -- pip install hanzidentifier')
    hanzidentifier = None


simp2trad = OpenCC('s2twp')
trad2simp = OpenCC('tw2sp')


def to_pinyin(chin):
    return ' '.join([seg[0] for seg in pinyin(chin)])


def put(lst, line):
    if isinstance(lst, list):
        lst.append(line)
    else:
        raise Exception('oh-oh')

# https://stackoverflow.com/questions/30926840/how-to-check-change-between-two-values-in-percent/43034457#43034457
def to_percent(a, b):
    if a == 0 and b == 0:
        return 100.0
    if a == b:
        return 100.0
    try:
        percentage = abs(float(b) / a * 100)
    except ZeroDivisionError:
        percentage = 100
    return percentage


def get_similarity_percent(string1, string2):
    match_size = SequenceMatcher(None, string1, string2).find_longest_match().size

    # assume pinyin is longer
    tot_len = len(string1)
    return to_percent(tot_len, match_size)


def append_pinyin_subs(args):

    if args.plain:
        plain_lines = []
    else:
        plain_lines = None

    print(args)

    # allow glob patterns
    if '*' in args.srt_file:
        input_files = sorted(Path(args.work_dir).glob(args.srt_file))
    else:
        input_files = [Path(args.srt_file)]

    for input_path in input_files:

        converted_subs = []

        with input_path.open(encoding=args.encoding or 'utf-8') as fi:
            subs: Generator[srt.Subtitle] = srt.parse(fi)
            srt.sort_and_reindex(subs, start_index=1, in_place=True, skip=True)

            sub: srt.Subtitle
            for sub in subs:
                orig_content = sub.content

                if args.force_normalize_input_to_simplified and hanzidentifier and hanzidentifier.is_traditional(orig_content):
                    orig_content = trad2simp.convert(orig_content)

                if args.force_normalize_input_to_traditional and hanzidentifier and hanzidentifier.is_simplified(orig_content):
                    orig_content = simp2trad.convert(orig_content)

                new_content = f'<font color="#ffffff">{orig_content}</font><br>'

                if args.plain:
                    put(plain_lines, orig_content)

                if args.plain and args.plain_timings:
                    put(plain_lines, f'{sub.index}\n{sub.start}')

                # FIX FOR BAD SUBS: if previous_sub.end is GREATER than current_sub.start then make previous_sub.end = current_sub.start
                if 0 < sub.index and len(converted_subs) != 0:
                    # get previous converted sub
                    prev_sub: srt.Subtitle = converted_subs[sub.index - 2]
                    if prev_sub.end > sub.start:
                        prev_sub.end = sub.start

                if args.simp_to_trad:
                    trad_content = simp2trad.convert(orig_content)

                    if trad_content != orig_content:
                        new_content += f'<font color="#d663fd">{trad_content}</font><br>'

                        if args.plain:
                            put(plain_lines, trad_content)

                if args.trad_to_simp:
                    simp_content = trad2simp.convert(orig_content)

                    if simp_content.strip() != orig_content:
                        new_content += f'<font color="#d663fd">{simp_content}</font><br>'

                        if args.plain:
                            put(plain_lines, simp_content)

                if not args.no_pinyin:
                    pinyin_line = to_pinyin(orig_content)

                    # only append if the conversion result is different from original
                    if pinyin_line.strip() != orig_content.strip():
                        if args.max_similarity_percent == 0 or get_similarity_percent(pinyin_line, orig_content) <= args.max_similarity_percent:
                            new_content += f'<font color="#00ffff">{pinyin_line}</font>'

                            if args.plain:
                                put(plain_lines, pinyin_line)

                sub.content = new_content

                if args.plain:
                    put(plain_lines, '\n')

                converted_subs.append(sub)
            print(srt.compose(converted_subs))

        filename_suffix = '.'

        if args.no_pinyin:
            if args.simp_to_trad:
                filename_suffix += 'trad'
            if args.trad_to_simp:
                filename_suffix += 'simp'
        else:
            filename_suffix += 'pinyin'

        if not args.output_file:
            generated_srt_file = input_path.parent / f'{input_path.stem}{filename_suffix}{input_path.suffix}'
        else:
            generated_srt_file = Path(args.output_file)

        with generated_srt_file.open(mode='w', encoding='utf-8') as fout:
            fout.write(srt.compose(converted_subs))
            print(f'Wrote {generated_srt_file.absolute()}')

        if args.plain:
            plain_text_file = input_path.parent / f'{input_path.stem}_PLAIN.txt'
            with plain_text_file.open(mode='w', encoding='utf-8') as tt:
                tt.write('\n'.join(plain_lines))
                print(f'Wrote {plain_text_file.absolute()}')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='SRT subtitles Chinese to pinyin converter',
                                     usage="""
    Generate pinyin for Chinese-language subtitles:                                     
    \t{0} zh-subitles.srt -o zh-subitles-with-pinyin.srt
    
    Append simplified for traditional:
    \t{0} zh-subitles.srt --simp-to-trad -o zh-subitles-with-pinyin-and-simp.srt
    
    Append traditional for simplified:
    \t{0} zh-subitles.srt --trad-to-simp -o zh-subitles-with-pinyin-and-trad.srt
     """.format(Path(sys.argv[0]).name))
    parser.add_argument('srt_file',
                        metavar='srt_file',
                        help='source SRT file(s): single arg; CAN ALSO BE A GLOB PATTERN!')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--simp-to-trad', '-t',
                        action='store_true',
                        default=False)
    group.add_argument('--trad-to-simp', '-s',
                        action='store_true',
                        default=False)
    parser.add_argument('--no-pinyin',
                        action='store_true',
                        default=False)
    parser.add_argument('--output-file', '-o',
                        default=None,
                        help='Output filename')
    parser.add_argument('--work-dir', '-d',
                        default='.',
                        help='Working directory')
    parser.add_argument('--plain', '-p',
                        action='store_true',
                        default=False,
                        help='Output human-readable plain text file with subtitles')
    parser.add_argument('--plain-timings',
                        action='store_true',
                        default=False,
                        help='Include timings with plain text output')
    parser.add_argument('--force-normalize-input-to-simplified',
                        action='store_true',
                        default=False,
                        help='Force input normalization to simplfied')
    parser.add_argument('--force-normalize-input-to-traditional',
                        action='store_true',
                        default=False,
                        help='Force input normalization to traditional')
    parser.add_argument('--encoding', '-e',
                        default=None,
                        help='Input file encoding')
    parser.add_argument('--max-similarity-percent',
                        default=0,
                        type=int,
                        help='Do NOT add pinyin if resulting text is more than N percent similar to the input text. 0 = no similarity check')

    cli_args = parser.parse_args(sys.argv[1:])

    if cli_args.no_pinyin and not any((cli_args.simp_to_trad, cli_args.trad_to_simp)):
        parser.error('--no-pinyin can only be used with one of --simp-to-trad/--trad-to-simp')

    append_pinyin_subs(cli_args)
