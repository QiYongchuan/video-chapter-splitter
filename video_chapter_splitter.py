#!/usr/bin/env python3
"""
视频章节自动切割工具
根据字幕语义识别章节并切割视频

用法:
    # 第一步：提取字幕
    python video_chapter_splitter.py <视频文件路径> --extract-only

    # 第二步：人工/AI分析章节后，按JSON切割
    python video_chapter_splitter.py <视频文件路径> --split-only
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import whisper


def extract_subtitles(video_path: str, model_size: str = "medium") -> List[Dict]:
    """
    使用 Whisper 提取字幕，带时间戳
    """
    print(f"[目标] 正在提取字幕: {video_path}")
    print(f"[模型] 使用: {model_size}")

    model = whisper.load_model(model_size)
    result = model.transcribe(video_path, language="zh", verbose=False)

    segments = []
    for seg in result["segments"]:
        segments.append({
            "id": seg["id"],
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip(),
            "words": seg.get("words", [])
        })

    print(f"[完成] 提取完成，共 {len(segments)} 个片段")
    return segments


def export_subtitles_for_analysis(segments: List[Dict], output_path: str):
    """
    导出字幕文本供人工/Claude 分析
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# 视频字幕内容\n\n")
        for seg in segments:
            start_time = format_time(seg["start"])
            end_time = format_time(seg["end"])
            f.write(f"## [{start_time} - {end_time}]\n")
            f.write(f"{seg['text']}\n\n")

    print(f"[完成] 字幕已导出: {output_path}")


def load_chapters_from_json(json_path: str) -> List[Dict]:
    """
    从 JSON 文件加载章节信息
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("chapters", [])


def parse_time(time_str: str) -> float:
    """将时间字符串转换为秒数"""
    parts = time_str.strip().split(":")
    if len(parts) == 2:  # MM:SS
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:  # HH:MM:SS
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    else:
        raise ValueError(f"无法解析时间: {time_str}")


def format_time(seconds: float) -> str:
    """将秒数格式化为 MM:SS"""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def split_video(video_path: str, chapters: List[Dict], output_dir: str = None):
    """
    使用 FFmpeg 切割视频
    """
    video_path = Path(video_path)
    if output_dir is None:
        output_dir = video_path.parent / f"{video_path.stem}_chapters"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(exist_ok=True)

    print(f"\n[切割] 开始切割视频，输出到: {output_dir}")

    for i, chapter in enumerate(chapters, 1):
        title = chapter["title"].replace(" ", "_").replace("/", "_")[:30]
        start_time = parse_time(chapter["start_time"])
        end_time = parse_time(chapter["end_time"])
        duration = end_time - start_time

        output_file = output_dir / f"{i:02d}_{title}.mp4"

        # FFmpeg 命令 - 使用 output seeking 模式，精度更高
        # 先读取输入，再定位到起始时间（避免 input seeking 的精度问题）
        cmd = [
            "ffmpeg",
            "-y",
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
        print(f"      时间: {chapter['start_time']} - {chapter['end_time']}")

        try:
            subprocess.run(cmd, capture_output=True, check=True)
            print(f"      [成功] 已保存: {output_file.name}")
        except subprocess.CalledProcessError as e:
            print(f"      [失败] 切割失败: {e}")

    print(f"\n[完成] 全部完成！共生成 {len(chapters)} 个视频片段")
    print(f"📁 输出目录: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="视频章节自动切割工具")
    parser.add_argument("video", help="视频文件路径")
    parser.add_argument("--model", default="medium", choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper 模型大小 (默认: medium)")
    parser.add_argument("--output-dir", help="输出目录 (默认: 视频名_chapters)")
    parser.add_argument("--extract-only", action="store_true",
                        help="只提取字幕，不分析不切割")
    parser.add_argument("--split-only", action="store_true",
                        help="只按 chapters.json 切割，不提取字幕")

    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"[错误] 文件不存在: {args.video}")
        sys.exit(1)

    video_path = Path(args.video)

    if args.split_only:
        # 只切割模式
        chapter_file = video_path.parent / f"{video_path.stem}_chapters.json"
        if not chapter_file.exists():
            print(f"[错误] 找不到章节文件: {chapter_file}")
            print("   请先运行 --extract-only 提取字幕并创建章节文件")
            sys.exit(1)

        chapters = load_chapters_from_json(chapter_file)
        print(f"[加载] 从 {chapter_file} 加载了 {len(chapters)} 个章节")
        split_video(args.video, chapters, args.output_dir)
        return

    # 1. 提取字幕
    segments = extract_subtitles(args.video, args.model)

    # 保存字幕文本（供 Claude 分析）
    subtitle_file = video_path.parent / f"{video_path.stem}_subtitles.md"
    export_subtitles_for_analysis(segments, subtitle_file)

    # 保存完整字幕数据（带精确时间戳）
    segments_file = video_path.parent / f"{video_path.stem}_segments.json"
    with open(segments_file, "w", encoding="utf-8") as f:
        json.dump({"segments": segments}, f, ensure_ascii=False, indent=2)
    print(f"[保存] 字幕数据已保存: {segments_file}")

    if args.extract_only:
        print("\n[完成] 仅提取模式完成")
        print(f"\n[提示] 下一步：")
        print(f"   1. 查看字幕文件: {subtitle_file}")
        print(f"   2. 创建章节 JSON 文件: {video_path.stem}_chapters.json")
        print(f"      格式: {{'chapters': [{{'title': 'xxx', 'start_time': '00:00', 'end_time': '01:30'}}]}}")
        print(f"   3. 运行: python video_chapter_splitter.py '{args.video}' --split-only")
        return

    print("\n[警告] 未指定模式，默认只提取字幕")
    print("   添加 --extract-only 提取字幕")
    print("   添加 --split-only 按已有章节切割")


if __name__ == "__main__":
    main()
