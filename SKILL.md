# 视频语义章节切割工具

根据字幕语义自动识别章节边界，精准切割视频为独立片段。

## 何时使用

- 长视频需要按内容章节切割成 demo/教学片段
- 网课/演讲需要提取独立案例
- 内容创作者需要批量生成短视频素材
- 任何需要"按语义理解"而非"按时间等分"切割视频的场景

## 工作原理

```
视频文件
  ↓ Whisper 本地识别
字幕文本（带精确时间戳）
  ↓ Claude 语义分析 / 人工标注
章节边界 JSON
  ↓ FFmpeg 精准切割
独立视频片段
```

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

输出：
- `xxx_subtitles.md` - 可读字幕文本
- `xxx_segments.json` - 精确时间戳数据

### 第二步：创建章节配置

查看字幕文件，或让 Claude 分析，创建 `xxx_chapters.json`：

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

### 第三步：切割视频

```bash
python video_chapter_splitter.py "你的视频.mp4" --split-only
```

输出：`xxx_chapters/` 目录下的独立视频文件

## 关键技术细节

### FFmpeg 切割精度优化

**问题**：默认 input seeking（`-ss` 在 `-i` 前）速度快但精度低，可能漂移 5-10 秒

**解决**：改用 output seeking（`-ss` 在 `-i` 后），精度更高

```python
# 不推荐：快但不准
cmd = ["ffmpeg", "-ss", "00:01:00", "-i", "input.mp4", ...]

# 推荐：稍慢但精准
cmd = ["ffmpeg", "-i", "input.mp4", "-ss", "00:01:00", ...]
```

### 章节边界识别策略

| 方法 | 准确度 | 适用场景 |
|------|--------|----------|
| AI 语义分析 | 高 | 演讲者明确说"第一个案例"、"接下来"等 |
| 人工标注 | 最高 | 对精度要求极高的最终输出 |
| 固定间隔 | 低 | 仅需均匀分割 |

### Whisper 模型选择

| 模型 | 速度 | 准确率 | 显存需求 |
|------|------|--------|----------|
| tiny | 最快 | 一般 | ~1GB |
| base | 快 | 较好 | ~1GB |
| small | 中等 | 好 | ~2GB |
| medium | 较慢 | 很好 | ~5GB |
| large | 最慢 | 最好 | ~10GB |

中文内容建议 `medium`，速度与准确率平衡较好。

## 与现有方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **本工具** | 语义理解精准、本地运行、免费 | 需手动确认章节 | 内容创作者、精准切割需求 |
| 剪映自动分割 | 简单、有界面 | 按画面/音量分割，不理解内容 | 快速粗剪 |
| Python moviepy | 纯 Python | 编码问题多、慢 | 简单脚本 |
| FFmpeg 直接切 | 最快 | 需手动算时间 | 已知时间戳 |
| 在线工具 | 无需安装 | 隐私风险、限制大小 | 临时使用 |

## 为什么不用现成的 Skills？

搜索技能市场发现：
- `video-clipper`：专注时间戳切割，无字幕语义分析
- `video-processing-editing`：FFmpeg 教程，无自动化流程
- `ffmpeg-video-editor`：基础 FFmpeg 封装

**核心差异**：本工具提供完整的"字幕→语义→切割"工作流，而非单一功能。

## 极速创建个性化工具的理念

这个 skill 体现了 Claude Code 的核心价值：

**从"找工具"到"造工具"**

传统工作流：
1. 搜索有没有现成软件
2. 下载、学习、适应它的逻辑
3. 妥协或放弃

Claude Code 工作流：
1. 描述你想要什么
2. 5分钟搭建专属工具
3. 完全按你的需求工作

**这不是编程，是"描述即创造"**。

## 故障排除

### Windows 编码错误

症状：`UnicodeEncodeError: 'gbk' codec can't encode`

解决：脚本已移除所有 emoji，使用纯 ASCII 输出

### FFmpeg 切割点不准

症状：视频开头/结尾多了几秒无关内容

解决：改用 `--split-only` 模式，手动微调 `chapters.json` 的时间戳

### Whisper 识别慢

症状：提取字幕耗时很长

解决：换小模型 `--model small`，或降低视频分辨率预处理

## 进阶用法

### 批量处理多个视频

```bash
for video in *.mp4; do
    python video_chapter_splitter.py "$video" --extract-only
done
```

### 结合 Claude 自动分析章节

提取字幕后，直接粘贴字幕内容给 Claude：

> "以下是视频字幕，请识别章节边界，格式为 JSON..."

Claude 会返回可直接使用的 chapters.json 内容。

## 文件位置

脚本路径：`C:/Users/xxx/video_chapter_splitter.py`   ===> 根据用户的情况创建

建议添加到系统 PATH，或创建 alias：

```bash
alias vcs='python C:/xx/xxx/video_chapter_splitter.py'
```
