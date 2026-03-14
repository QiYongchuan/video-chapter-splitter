# 视频语义章节切割工具 v2.0

根据字幕语义自动识别章节边界，精准切割视频为独立片段。

## 何时使用

- 长视频需要按内容章节切割成 demo/教学片段
- 网课/演讲需要提取独立案例
- 内容创作者需要批量生成短视频素材
- 任何需要"按语义理解"而非"按时间等分"切割视频的场景

## 工作原理（v2.0 优化）

```
视频文件 (1.5GB)
  ↓ FFmpeg 提取音频 (~3秒)
16kHz mono WAV (~180MB)
  ↓ Whisper 本地转录 (~5分钟, CPU small模型)
字幕文本（带精确时间戳）
  ↓ Claude 语义分析 (subagent, ~72K token)
章节边界 JSON
  ↓ FFmpeg 精准切割 (~10分钟)
独立视频片段
```

**v2.0 关键优化**: 先提取音频再转录，速度提升 10x+。
直接丢视频给 Whisper 会导致 CPU 下极慢（1.5GB 视频预计 10+ 小时），
提取音频后同样的视频只需 5 分钟。

## 依赖安装

```bash
# Python 3.8+
pip install openai-whisper

# FFmpeg（需系统安装）
# Windows: winget install Gyan.FFmpeg
# Mac: brew install ffmpeg
# Linux: apt install ffmpeg
```

## 使用方法

### 第一步：提取字幕

```bash
python video_chapter_splitter.py "你的视频.mp4" --extract-only
```

内部流程：FFmpeg 提取音频 -> Whisper 转录 -> 自动清理中间音频文件

输出：
- `xxx_subtitles.md` - 可读字幕文本
- `xxx_segments.json` - 精确时间戳数据

### 第二步：创建章节配置

让 Claude 分析字幕文件，创建 `xxx_chapters.json`：

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

### 第三步：切割视频

```bash
python video_chapter_splitter.py "你的视频.mp4" --split-only
```

输出：`xxx_chapters/` 目录下的独立视频文件

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--model` | small | Whisper 模型 (CPU 推荐 small, GPU 推荐 medium) |
| `--extract-only` | - | 只提取字幕 |
| `--split-only` | - | 只按 chapters.json 切割 |
| `--keep-audio` | false | 保留中间音频文件 |
| `--output-dir` | 视频名_chapters | 自定义输出目录 |

## Whisper 模型选择

| 模型 | CPU 速度 | 准确率 | 推荐场景 |
|------|----------|--------|----------|
| tiny | 最快 | 一般 | 快速预览 |
| base | 快 | 较好 | 英文内容 |
| **small** | **中等** | **好** | **CPU 中文首选** |
| medium | 较慢 | 很好 | GPU 中文首选 |
| large | 最慢 | 最好 | 高精度需求 |

## 成本估算（实测数据）

以 1.5GB / 1小时38分钟直播课为例：

| 环节 | Token | 时间 | 费用 |
|------|-------|------|------|
| FFmpeg 提取音频 | 0 | 3秒 | 免费 |
| Whisper 转录 (small/CPU) | 0 | ~5分钟 | 免费 |
| Claude 语义分析 | ~72K | ~3分钟 | ~$1.2 |
| FFmpeg 切割 | 0 | ~10分钟 | 免费 |

**每小时视频约 67K token, 约 $0.74 (¥5)**

## 关键技术细节

### 音频提取优化

Whisper 只处理音频，但直接传视频时内部解码效率极低（尤其 CPU）。
预先用 FFmpeg 提取 16kHz mono WAV 是 Whisper 的最优输入格式：
- 采样率匹配，无需内部重采样
- 单声道，减少数据量
- PCM 格式，无需解码

### FFmpeg 切割精度

使用 output seeking（`-ss` 在 `-i` 后），精度高于 input seeking。

### Windows 兼容

- 所有输出使用纯 ASCII，避免 GBK 编码错误
- 文件名自动清理特殊字符
- 中间音频文件默认自动清理

## 故障排除

### Whisper 识别慢
换 small 模型 + 先提取音频（v2.0 默认行为）

### FFmpeg 切割点不准
手动微调 chapters.json 的时间戳，重新 --split-only

### Windows 编码错误
v2.0 已修复，所有输出使用纯 ASCII

## 文件位置

脚本路径：skill 目录下 `video_chapter_splitter.py`
