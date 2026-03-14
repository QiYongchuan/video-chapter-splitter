#!/usr/bin/env python3
"""
视频章节自动切割工具 v2.0
根据字幕语义识别章节并切割视频

优化: 先提取音频再转录，速度提升 10x+

用法:
    # 第一步：提取字幕（自动先分离音频）
    python video_chapter_splitter.py <视频文件路径> --extract-only

    # 第二步：人工/AI分析章节后，按JSON切割
    python video_chapter_splitter.py <视频文件路径> --split-only
"""

import os
import sys
import json
import subprocess
import argparse
import time
import re
from pathlib import Path
from typing import List, Dict


def extract_audio(video_path: str, output_path: str = None) -> str:
    """
    用 FFmpeg 从视频中提取音频为 16kHz mono WAV（Whisper 最优格式）
    1.5GB 视频 -> ~180MB 音频，耗时约 3-5 秒
    """
    video_path = Path(video_path)
    if output_path is None:
        output_path = str(video_path.parent / f"{video_path.stem}_audio.wav")

    print(f"[音频] 正在从视频提取音频...")
    start = time.time()

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_path
    ]

    try:
        subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[错误] 音频提取失败: {e}")
        sys.exit(1)

    elapsed = time.time() - start
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"[音频] 完成! {size_mb:.1f} MB, 耗时 {elapsed:.1f} 秒")
    return output_path


def extract_subtitles(audio_path: str, model_size: str = "small") -> List[Dict]:
    """
    使用 Whisper 从音频文件提取字幕（不再直接处理视频）
    """
    import whisper

    print(f"[转录] 正在加载 Whisper {model_size} 模型...")
    model = whisper.load_model(model_size)

    print(f"[转录] 开始转录音频: {audio_path}")
    start = time.time()
    result = model.transcribe(audio_path, language="zh", verbose=False)
    elapsed = time.time() - start

    segments = []
    for seg in result["segments"]:
        segments.append({
            "id": seg["id"],
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip()
        })

    print(f"[转录] 完成! 共 {len(segments)} 个片段, 耗时 {elapsed:.0f} 秒")
    return segments


def export_subtitles_for_analysis(segments: List[Dict], output_path: str):
    """导出字幕文本供 Claude 语义分析"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# 视频字幕内容\n\n")
        for seg in segments:
            start_time = format_time_hms(seg["start"])
            end_time = format_time_hms(seg["end"])
            f.write(f"## [{start_time} - {end_time}]\n")
            f.write(f"{seg['text']}\n\n")
    print(f"[保存] 字幕文本: {output_path}")


def load_chapters_from_json(json_path: str) -> List[Dict]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("chapters", [])


def parse_time(time_str: str) -> float:
    """将时间字符串转换为秒数，支持 MM:SS 和 HH:MM:SS"""
    parts = time_str.strip().split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    else:
        raise ValueError(f"无法解析时间: {time_str}")


def format_time_hms(seconds: float) -> str:
    """将秒数格式化为 HH:MM:SS"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def sanitize_filename(name: str) -> str:
    """清理文件名，移除不安全字符，保留中英文和数字"""
    name = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    name = re.sub(r'[<>:"|?*]', '', name)
    return name[:40]


def split_video(video_path: str, chapters: List[Dict], output_dir: str = None):
    """使用 FFmpeg 精准切割视频"""
    video_path = Path(video_path)
    if output_dir is None:
        output_dir = video_path.parent / f"{video_path.stem}_chapters"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(exist_ok=True)
    print(f"\n[切割] 开始切割视频, 输出到: {output_dir}")

    success_count = 0
    for i, chapter in enumerate(chapters, 1):
        title = sanitize_filename(chapter["title"])
        start_time = parse_time(chapter["start_time"])
        end_time = parse_time(chapter["end_time"])
        duration = end_time - start_time

        output_file = output_dir / f"{i:02d}_{title}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-ss", str(start_time),
            "-t", str(duration),
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-avoid_negative_ts", "make_zero",
            "-movflags", "+faststart",
            str(output_file)
        ]

        print(f"\n  [{i}/{len(chapters)}] {chapter['title']}")
        print(f"      {chapter['start_time']} -> {chapter['end_time']}")

        try:
            subprocess.run(cmd, capture_output=True, check=True)
            size_mb = output_file.stat().st_size / 1024 / 1024
            print(f"      [OK] {output_file.name} ({size_mb:.1f} MB)")
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"      [FAIL] {e}")

    print(f"\n[完成] 成功切割 {success_count}/{len(chapters)} 个片段")
    print(f"[输出] {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="视频语义章节切割工具 v2.0")
    parser.add_argument("video", help="视频文件路径")
    parser.add_argument("--model", default="small",
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper 模型 (默认: small, CPU 推荐; GPU 可用 medium)")
    parser.add_argument("--output-dir", help="输出目录 (默认: 视频名_chapters)")
    parser.add_argument("--extract-only", action="store_true",
                        help="只提取字幕，不切割")
    parser.add_argument("--split-only", action="store_true",
                        help="只按 chapters.json 切割")
    parser.add_argument("--keep-audio", action="store_true",
                        help="保留提取的中间音频文件")

    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"[错误] 文件不存在: {args.video}")
        sys.exit(1)

    video_path = Path(args.video)

    if args.split_only:
        chapter_file = video_path.parent / f"{video_path.stem}_chapters.json"
        if not chapter_file.exists():
            print(f"[错误] 找不到章节文件: {chapter_file}")
            print("  请先运行 --extract-only 提取字幕并创建章节文件")
            sys.exit(1)

        chapters = load_chapters_from_json(chapter_file)
        print(f"[加载] {chapter_file} -> {len(chapters)} 个章节")
        split_video(args.video, chapters, args.output_dir)
        return

    # Step 1: 提取音频
    audio_path = extract_audio(args.video)

    # Step 2: Whisper 转录音频
    segments = extract_subtitles(audio_path, args.model)

    # Step 3: 保存字幕
    subtitle_file = video_path.parent / f"{video_path.stem}_subtitles.md"
    export_subtitles_for_analysis(segments, subtitle_file)

    segments_file = video_path.parent / f"{video_path.stem}_segments.json"
    with open(segments_file, "w", encoding="utf-8") as f:
        json.dump({"segments": segments}, f, ensure_ascii=False, indent=2)
    print(f"[保存] 时间戳数据: {segments_file}")

    # 清理中间音频文件
    if not args.keep_audio:
        os.remove(audio_path)
        print(f"[清理] 已删除中间音频文件")

    if args.extract_only:
        print("\n[完成] 字幕提取完成")
        print(f"\n  下一步:")
        print(f"  1. 查看字幕: {subtitle_file}")
        print(f"  2. 创建章节: {video_path.stem}_chapters.json")
        print(f"  3. 切割: python video_chapter_splitter.py '{args.video}' --split-only")
        return

    print("\n[提示] 请指定模式: --extract-only 或 --split-only")


if __name__ == "__main__":
    main()
