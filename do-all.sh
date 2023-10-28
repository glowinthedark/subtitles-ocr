#!/bin/bash

# REQUIREMENTS:
# python srt module: install with `pip3 install srt`
# custom fork of macOCR: https://github.com/glowinthedark/macOCR
#
# USAGE:
# ./do-all.sh video.mp4

read -p "Generate cropped video $1_video-cropped.mp4? (Y/N).." answer
case ${answer:0:1} in
    y|Y )
        ################### TODO: adjust crop area for input video #########################
        ffmpeg -i "$1" -filter:v "crop=1738:115:100:965" -c:a copy "$1_video-cropped.mp4"
    ;;
    * )
        echo Skipping...
    ;;
esac

# STEP 2: extract key frames to png images with detection threshold

# generate 1 snapshot per second
read -p "Generate snapshots (y/n)?.." answer
case ${answer:0:1} in
    y|Y )
        rm -rfv "$1_img"
        mkdir -p "$1_img"
        ffmpeg -i "$1_video-cropped.mp4" -start_number 1 -vf "fps=1" -q:v 2 "$1_img/snap_%04d.png"
    ;;    * )
        echo Skipping...
    ;;
esac

read -p "Start OCR (y/n)?.." answer
case ${answer:0:1} in
    y|Y )
        rm -rf -v "$1_results.json"
        python3 do-ocr.py "$1_img" "$1_results.json"
    ;;
    * )
        echo Skipping...
    ;;
esac


read -p "Generate SRT (y/n)?.." answer
case ${answer:0:1} in
    y|Y )
        rm "$1.ocr.srt"
        python3 gensrt.py "$1_results.json" "$1.ocr.srt"
    ;;
    * )
        echo Skipping...
    ;;
esac

read -p "SRT normalize and deduplicate inplace (y/n)?.." answer
case ${answer:0:1} in
    y|Y )
      srt-normalise -i "$1.ocr.srt" --inplace --debug
    ;;
    * )
        echo Skipping...
    ;;
esac

# TODO: install required DEPENDENCIES with `pip install -U srt opencc pypinyin hanzidentifier` 
read -p "Generate pinyin SRT (y/n)?.." answer
case ${answer:0:1} in
    y|Y )
        python3 srt_subs_zh2pinyin.py "$1.ocr.srt" --force-normalize-input-to-simplified -t -o "$1.ocr.pinyin.srt"
    ;;
    * )
        echo Skipping...
    ;;
esac

# TODO: get your free/paid API key at https://www.deepl.com/docs-api/api-access
read -p "Deepl translate zh:en $1.ocr.srt (y/n)?.." answer
case ${answer:0:1} in
    y|Y )
        python3 deepl.py zh:en "$1.ocr.srt"
    ;;
    * )
        echo Skipping...
    ;;
esac


read -p "SRT merge (y/n)?.." answer
case ${answer:0:1} in
    y|Y )
        python3 srt_merge.py "$1.ocr.pinyin.srt" "$1.ocr.en.srt"
    ;;
    * )
        echo Skipping...
    ;;
esac

exit 0

