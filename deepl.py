#!/usr/bin/env python3

# ***TODO***: get your API key at https://www.deepl.com/docs-api/api-access
# ALSO SEE: https://www.deepl.com/docs-api/translate-text/translate-text/

import argparse
import re
import string

import sys
from pathlib import Path
from typing import List

import requests

PATTERN_ENGLISH = re.compile('([a-zA-Z]+)')
PATTERN_PUNCTUATION = re.compile('([_ {re.escape(string.punctuation)}]+)')
NOTR_START = '<notr>'
NOTR_END = '</notr>'

def mark_untranslatable_lines(lines: List, source_lang: str, target_lang: str):
    marked_lines = []
    for line in lines:
        # if line is NOT english or chinese text then mark as untranslatable
        if line and not (has_text(line) or (source_lang.lower() == 'zh' and re.findall(r'[\u4e00-\u9fff]+', line))):
            marked_lines.append(f'{NOTR_START}{line}{NOTR_END}')

        # if line has mixed english+chinese then mark all as untranslatable
        elif source_lang.lower() == 'zh' and target_lang.lower() == 'en' and re.search(pattern=PATTERN_ENGLISH, string=line):
            marked_lines.append(f'{NOTR_START}{line}{NOTR_END}')

        else:
            marked_lines.append(line)

    return marked_lines

def generate_chunks(_lines, chunk_size=20, src_lang=None, trg_lang=None):
    lines = mark_untranslatable_lines(_lines, src_lang, trg_lang)

    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lines), chunk_size):
        yield lines[i:i + chunk_size]


def has_text(s: str):
    return any(c.isalpha() for c in s)


def do_translate(args):

    input_file = Path(args.input_file)

    source_language: str
    target_language: str
    source_language, target_language = args.lang_pair.split(':')

    input_text = input_file.read_text(encoding='utf-8')

    chunks = list(generate_chunks(input_text.split('\n'), chunk_size=args.chunk_size, src_lang=target_language))

    translated_chunks = []

    for chunk in chunks:

        payload = {
            'text': chunk,
            'target_lang': target_language.upper(),
            'tag_handling': 'xml',
            'ignore_tags': 'notr',
            'outline_detection': '0',
            'split_sentences': 'nonewlines',
        }

        if source_language:
            payload['source_lang'] = source_language.upper()

        if args.formality != 'default':
            if args.formality in ('more', 'less', 'prefer_more', 'prefer_less'):
                payload['formality'] = args.formality
            else:
                print(f'WARNING: invalid formality value {args.formality}!')

        # print(f'Sending {len(chunk)} characters for translation...')
        response = requests.post('https://api-free.deepl.com/v2/translate',
                                 headers={
                                     ################################# TODO: USE A VALID API KEY ##################
                                     ################################# SEE: https://www.deepl.com/docs-api/api-access
                                     'Authorization': 'DeepL-Auth-Key 55555555-5555-5555-5555-555555555555:fx'
                                 },
                                 data=payload)

        if response.status_code is not requests.codes.ok:
            print(f'''ERROR
HTTP STATUS: {response.status_code}
RESPONSE: {response.text}
''')
            raise Exception(f'Bad server response while processing {input_file.absolute()}')

        data = response.json()

        for translated_chunk in data['translations']:
            translated = translated_chunk.get('text')
            print(translated)
            translated_chunks.append(translated)

    if args.output_file:
        out = Path(args.output_file)
    else:
        out = input_file.with_suffix(f'.{target_language}{input_file.suffix}')

    chunks_reassembled = '\n'.join(translated_chunks)
    chunks_reassembled = chunks_reassembled.replace(NOTR_START, '').replace(NOTR_END, '')
    out.write_text(chunks_reassembled)
    print(f'Wrote file {out.absolute()}')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='''Deepl translator
Available language codes:
    BG,
    CS,
    DA,
    DE,
    EL,
    EN,
    ES,
    ET,
    FI,
    FR,
    HU,
    ID,
    IT,
    JA,
    LT,
    LV,
    NL,
    PL,
    PT,
    RO,
    RU,
    SK,
    SL,
    SV,
    TR,
    UK,
    ZH
    
API: https://www.deepl.com/docs-api/translate-text/
    ''')

    parser.add_argument('lang_pair',
                        help='<source:target> language codes',
                        action='store')

    parser.add_argument('input_file',
                        help='file to translate',
                        action='store')

    parser.add_argument('--chunk-size',
                        default=100,
                        type=int,
                        action='store',
                        help='lines in a batch for large files')

    parser.add_argument('--preserve-formatting',
                        default="0",
                        help='Sets whether the translation engine should respect the original formatting, even if it would usually correct some aspects. Possible values are: 0 (default), 1',
                        action='store')

    parser.add_argument('--formality',
                        default="default",
                        help="""Sets whether the translated text should lean towards formal or informal language. This feature currently only works for target languages DE (German), FR (French), IT (Italian), ES (Spanish), NL (Dutch), PL (Polish), PT-PT, PT-BR (Portuguese) and RU (Russian). Setting this parameter with a target language that does not support formality will fail, unless one of the prefer_... options are used. Possible options are:

    default (default)
    more - for a more formal language
    less - for a more informal language
    prefer_more - for a more formal language if available, otherwise fallback to default formality
    prefer_less - for a more informal language if available, otherwise fallback to default formality
""",
                        action='store')

    parser.add_argument('--output-file', '-o',
                        metavar='filename',
                        help='Output filename')

    args = parser.parse_args(sys.argv[1:])

    do_translate(args)
