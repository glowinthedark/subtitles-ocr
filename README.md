## Hard-burned subtitles OCR to SRT extractor

- Apple Silicon M1/M2 toolchain for extracting .SRT subtitles from movies with embedded hard-burned subtitles
- the OCR step is using a [modified version of macOCR](https://github.com/glowinthedark/macOCR) (forked from https://github.com/xulihang/macOCR); the macos Apple Silicon ARM64 binary is included in the repo as [OCR](OCR)

The workflow sequence:

1. Generate cropped video with `ffmpeg` (you'll have to adjust the crop area for your video size)
2. Generate PNG snapshots (using `ffmpeg ... fps=1` — 1 snapshot per second)
3. Optical Character Recognition using macOCR (Apple Silicon only) outputs JSON file.
4. Convert JSON to SRT + normalize and deduplicate using https://github.com/cdown/srt.
5. optional: Generate Chinese pinyin and traditional/simplified versions.
6. optional: Translate with deepl.
7. optional: Merge translation into the final SRT containing Hanzi Simplified + Hanzi Traditional + Pinyin + English.

# NOTE

- this collection of scripts is work in progress and will require tweaking for each specific scenario (the corresponding places that need editing are marked with TODO comments in the code); use this at your own risk
