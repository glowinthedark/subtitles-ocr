## Chinese hard-burned subtitles OCR extractor

- Apple Silicon M1/M2 toolchain for extracting .SRT subtitles from Chinese movies with embedded hard-burned subtitles
- the OCR step is using a [modified version of macOCR](https://github.com/glowinthedark/macOCR) (forked from https://github.com/xulihang/macOCR)

The workflow sequence:

1. Generate cropped video (need to adjust crop area for your video size)
2. Generate PNG snapshots (`fps=4` is used)
3. Optical Character Recognition using macOCR (Apple Silicon only) outputs JSON file.
4. Convert JSON to SRT + normalize and deduplicate using https://github.com/cdown/srt.
5. Generate Chinese pinyin and traditional/simplified versions.
6. Translate with deepl.
7. Merge translation into the final SRT containing Hanzi Simplified + Hanzi Traditional + Pinyin + English.

# NOTE

- this is work in progress and not suitable for usage as-is; you'll need to adapt to your specific scenario
