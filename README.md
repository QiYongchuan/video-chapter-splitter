# Video Chapter Splitter v2.0

基于字幕语义自动识别章节边界，精准切割视频为独立片段的 Claude Code Skill。

[English](#english) | [中文](#中文)

---

## 中文

### v2.0 更新

- **先提取音频再转录，速度提升 10x+**：直接丢视频给 Whisper 在 CPU 下极慢（1.5GB 视频预计 10+ 小时），提取音频后只需 5 分钟
- **默认使用 small 模型**：CPU 下性价比最高，中文识别准确率够用
- **修复 Windows GBK 编码问题**：移除所有 emoji，纯 ASCII 输出
- **文件名安全处理**：自动清理特殊字符，避免跨平台问题
- **自动清理中间文件**：提取的音频文件默认自动删除

### 功能

- **音频提取**：FFmpeg 提取 16kHz mono WAV（Whisper 最优格式），1.5GB 视频 3 秒搞定
- **字幕提取**：Whisper 本地转录音频，生成带时间戳的字幕
- **语义分析**：AI 理解内容，按知识点/问答自动识别章节边界
- **精准切割**：FFmpeg 按语义章节切割，非固定时长

### 工作原理

```
视频文件 (1.5GB)
  ↓ FFmpeg 提取音频 (~3秒)
16kHz mono WAV (~180MB)
  ↓ Whisper 本地转录 (~5分钟, CPU small模型)
字幕文本（带精确时间戳）
  ↓ Claude 语义分析 (~72K token)
章节边界 JSON
  ↓ FFmpeg 精准切割 (~10分钟)
独立视频片段
```

### 成本（实测数据）

以 1.5GB / 1小时38分钟直播课为例：

| 环节 | Token | 时间 | 费用 |
|------|-------|------|------|
| FFmpeg 提取音频 | 0 | 3秒 | 免费 |
| Whisper 转录 (small/CPU) | 0 | ~5分钟 | 免费 |
| Claude 语义分析 | ~72K | ~3分钟 | ~$1.2 |
| FFmpeg 切割 | 0 | ~10分钟 | 免费 |

**每小时视频约 67K token，约 $0.74（¥5）**

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
# 第一步：提取字幕（自动先分离音频再转录）
python video_chapter_splitter.py "视频.mp4" --extract-only

# 第二步：查看生成的 xxx_subtitles.md，创建 xxx_chapters.json
# 或让 Claude 分析字幕自动生成章节 JSON

# 第三步：按章节切割
python video_chapter_splitter.py "视频.mp4" --split-only
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--model` | small | Whisper 模型 (CPU 推荐 small, GPU 推荐 medium) |
| `--extract-only` | - | 只提取字幕 |
| `--split-only` | - | 只按 chapters.json 切割 |
| `--keep-audio` | false | 保留中间音频文件 |
| `--output-dir` | 视频名_chapters | 自定义输出目录 |

### chapters.json 格式

```json
{
  "chapters": [
    {
      "title": "01_开篇介绍",
      "start_time": "00:00:00",
      "end_time": "00:05:10",
      "summary": "介绍系统架构",
      "type": "knowledge"
    },
    {
      "title": "02_问答环节",
      "start_time": "00:05:10",
      "end_time": "00:12:00",
      "summary": "学员提问与解答",
      "type": "qa"
    }
  ]
}
```

### 技术亮点

**音频预提取优化**

Whisper 只处理音频，但直接传视频时内部解码效率极低。预先用 FFmpeg 提取 16kHz mono WAV：
- 采样率匹配 Whisper，无需内部重采样
- 单声道减少数据量
- PCM 格式无需解码

**FFmpeg 切割精度**

使用 output seeking 模式（`-ss` 在 `-i` 后），实现帧级精度：

```bash
# 不推荐：快但不准，可能漂移 5-10 秒
ffmpeg -ss 00:01:00 -i input.mp4 ...

# 推荐：稍慢但精准到帧
ffmpeg -i input.mp4 -ss 00:01:00 ...
```

---

## English

### v2.0 Updates

- **Extract audio before transcription, 10x+ faster**: Feeding video directly to Whisper on CPU is extremely slow; extracting audio first reduces processing from 10+ hours to ~5 minutes
- **Default to small model**: Best cost-performance ratio on CPU
- **Fixed Windows GBK encoding issues**: Pure ASCII output
- **Auto-cleanup of intermediate files**

### Features

- **Audio Extraction**: FFmpeg extracts 16kHz mono WAV (Whisper's optimal format), ~3 seconds for 1.5GB video
- **Subtitle Extraction**: Local Whisper transcription with timestamps
- **Semantic Analysis**: AI detects chapter boundaries by knowledge points and Q&A sections
- **Precise Cutting**: FFmpeg cuts by semantic chapters, not fixed duration

### How it works

```
Video (1.5GB)
  ↓ FFmpeg extract audio (~3s)
16kHz mono WAV (~180MB)
  ↓ Whisper transcribe (~5min, CPU small)
Timestamped subtitles
  ↓ Claude semantic analysis (~72K tokens)
Chapter boundaries JSON
  ↓ FFmpeg precise cut (~10min)
Individual video clips
```

### Cost (Real-world data)

For a 1.5GB / 1h38m live stream:

| Step | Tokens | Time | Cost |
|------|--------|------|------|
| FFmpeg extract audio | 0 | 3s | Free |
| Whisper transcribe (small/CPU) | 0 | ~5min | Free |
| Claude semantic analysis | ~72K | ~3min | ~$1.2 |
| FFmpeg split | 0 | ~10min | Free |

**~67K tokens per hour of video, ~$0.74 per hour**

### Installation

```bash
pip install openai-whisper
# Install FFmpeg system-wide
```

### Usage

```bash
# Step 1: Extract subtitles (auto extracts audio first)
python video_chapter_splitter.py "video.mp4" --extract-only

# Step 2: Review xxx_subtitles.md, create xxx_chapters.json

# Step 3: Split by chapters
python video_chapter_splitter.py "video.mp4" --split-only
```

---

## 相关文章

- v1.0: [10 分钟，我用 Claude Code 造了一个视频语义切割工具](https://x.com/nopinduoduo/status/2029112063256346969)
- v2.0: [10 分钟完成 1.5 小时视频语义切割，成本不到 1 元](https://x.com/nopinduoduo/status/2032590321721421945)

## 作者

Created with Claude Code. v1.0 in 5 minutes, v2.0 optimized through real-world usage.

## License

MIT License
