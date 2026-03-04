# Video Chapter Splitter

基于字幕语义自动识别章节边界，精准切割视频为独立片段的 Claude Code Skill。

[English](#english) | [中文](#中文)

---

## 中文

### 功能

- **字幕提取**：使用 Whisper 本地识别，生成带时间戳的字幕
- **语义分析**：AI 理解内容，自动识别章节边界（如"第三个案例"、"接下来"）
- **精准切割**：FFmpeg 按语义章节切割，非固定时长

### 工作原理

```
原始视频 → Whisper提取字幕 → AI分析语义 → 识别章节边界 → FFmpeg切割
              ↓                      ↓
         带时间戳的文本        章节标题+起止时间
```

### 安装依赖

```bash
# Python 3.8+
pip install openai-whisper

# FFmpeg（系统安装）
# Windows: winget install Gyan.FFmpeg
# Mac: brew install ffmpeg
# Linux: apt install ffmpeg
```

### 使用方法

```bash
# 第一步：提取字幕
python video_chapter_splitter.py "视频.mp4" --extract-only

# 第二步：查看生成的 xxx_subtitles.md，创建 xxx_chapters.json
# 格式示例见下方

# 第三步：按章节切割
python video_chapter_splitter.py "视频.mp4" --split-only
```

### chapters.json 格式

```json
{
  "chapters": [
    {
      "title": "01_开篇介绍",
      "start_time": "00:00",
      "end_time": "00:23",
      "summary": "介绍系统架构"
    },
    {
      "title": "02_案例演示",
      "start_time": "00:23",
      "end_time": "02:15",
      "summary": "具体功能展示"
    }
  ]
}
```

### 技术亮点

**FFmpeg 切割精度优化**

使用 output seeking 模式（`-ss` 在 `-i` 后），而非默认的 input seeking，实现帧级精度：

```bash
# 不推荐：快但不准，可能漂移 5-10 秒
ffmpeg -ss 00:01:00 -i input.mp4 ...

# 推荐：稍慢但精准到帧
ffmpeg -i input.mp4 -ss 00:01:00 ...
```

---

## English

### Features

- **Subtitle Extraction**: Local Whisper recognition, generates timestamped subtitles
- **Semantic Analysis**: AI understands content, auto-detects chapter boundaries
- **Precise Cutting**: FFmpeg cuts by semantic chapters, not fixed duration

### How it works

```
Raw Video → Whisper extracts subtitles → AI analyzes → Detects boundaries → FFmpeg cuts
                 ↓                           ↓
         Timestamped text              Chapter titles + timestamps
```

### Installation

```bash
pip install openai-whisper
# Install FFmpeg system-wide
```

### Usage

```bash
# Step 1: Extract subtitles
python video_chapter_splitter.py "video.mp4" --extract-only

# Step 2: Review xxx_subtitles.md, create xxx_chapters.json

# Step 3: Split by chapters
python video_chapter_splitter.py "video.mp4" --split-only
```

---

## 作者

Created with Claude Code in 5 minutes.

博客文章：[5 分钟，我用 Claude Code 造了一个视频语义切割工具](#)

## License

MIT License
