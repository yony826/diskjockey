# WMA 和 M4A 格式支持说明

## ✅ 已添加的支持

代码现在支持以下音频格式：

1. **MP3** - 使用 `mutagen.easyid3.EasyID3`
2. **FLAC** - 使用 `mutagen.flac.FLAC`
3. **M4A** - 使用 `mutagen.mp4.MP4（新增）`
4. **WMA** - 使用 `mutagen.asf.ASF（新增）`

## 📝 代码修改说明

### 1. 导入模块

添加了 WMA 和 M4A 的导入：

```python
from mutagen.asf import ASF  # WMA 格式支持
from mutagen.mp4 import MP4  # M4A 格式支持
```

### 2. 文件扫描

更新了文件扫描逻辑，现在会识别 `.wma` 文件：

```python
if file.lower().endswith(('.mp3', '.flac', '.m4a', '.wma')):
```

### 3. 标签更新

在 `update_tags` 函数中添加了 WMA 和 M4A 的处理：

#### M4A 格式处理

```python
elif file_path.endswith('.m4a'):
    audio = MP4(file_path)
    audio['\xa9nam'] = title      # 标题
    audio['\xa9ART'] = artist      # 艺术家
    audio['\xa9alb'] = album       # 专辑
    audio['\xa9day'] = str(year)   # 年份
    audio['\xa9gen'] = genre       # 流派
    audio['trkn'] = [(int(tracknumber), 0)]  # 曲目号
    audio.save()
```

#### WMA 格式处理

```python
elif file_path.endswith('.wma'):
    audio = ASF(file_path)
    audio['Title'] = title
    audio['Author'] = artist
    audio['WM/AlbumTitle'] = album
    audio['WM/Year'] = str(year)
    audio['WM/Genre'] = genre
    audio['WM/TrackNumber'] = str(tracknumber)
    audio.save()
```

## 🔍 音频识别支持

### WMA 格式的音频识别

**重要说明：**

- **标签写入**：✅ 完全支持（使用 mutagen.asf.ASF）
- **音频识别**：取决于系统环境

`pyacoustid` 使用 `audioread` 库来解码音频文件以生成指纹。`audioread` 对 WMA 的支持取决于系统上安装的后端：

1. **Windows**：通常支持 WMA（通过 Windows Media Foundation）
2. **Linux/群晖**：需要安装支持 WMA 的解码器
   - 推荐安装 FFmpeg：`sudo apt-get install ffmpeg`
   - FFmpeg 支持 WMA 格式的解码

### M4A 格式的音频识别

- **标签写入**：✅ 完全支持（使用 mutagen.mp4.MP4）
- **音频识别**：✅ 通常支持（大多数系统都支持 M4A/MP4 解码）

## 🧪 测试方法

### 测试 WMA 格式

1. **准备测试文件**：
   - 准备一个 WMA 格式的音乐文件

2. **运行代码**：
   ```bash
   python diskjockey.py
   ```

3. **检查结果**：
   - 如果系统支持 WMA 解码，会看到正常的识别和标签更新
   - 如果不支持，可能会在音频识别阶段报错，但标签写入功能仍然可用

### 测试 M4A 格式

M4A 格式通常在所有系统上都能正常工作。

## ⚠️ 注意事项

### WMA 格式的特殊性

1. **解码器依赖**：
   - Windows：通常内置支持
   - Linux/群晖：需要安装 FFmpeg 或其他支持 WMA 的解码器

2. **WMA 变体**：
   - WMA 有多种变体（WMA、WMA Pro、WMA Lossless）
   - 某些变体可能需要特定的解码器

3. **群晖 NAS 部署**：
   - 在 Dockerfile 中已包含 FFmpeg 的安装（通过 `libchromaprint-dev`）
   - 如果需要完整的 WMA 支持，可能需要额外安装 FFmpeg：
     ```dockerfile
     RUN apt-get update && apt-get install -y \
         libchromaprint-dev \
         fpcalc \
         ffmpeg \
         && rm -rf /var/lib/apt/lists/*
     ```

### 标签字段说明

- **WMA 格式**：使用 Windows Media 标签格式（如 `WM/AlbumTitle`）
- **M4A 格式**：使用 iTunes/MP4 标签格式（如 `\xa9nam` 表示标题）

## 🔧 故障排除

### 如果 WMA 文件无法识别

1. **检查解码器**：
   ```bash
   # 在 Linux/群晖上
   ffmpeg -codecs | grep wma
   ```

2. **安装 FFmpeg**（如果未安装）：
   ```bash
   sudo apt-get install ffmpeg
   ```

3. **测试音频解码**：
   ```python
   import audioread
   with audioread.audio_open('test.wma') as f:
       print(f"采样率: {f.samplerate}, 声道: {f.channels}")
   ```

### 如果标签无法写入

1. **检查文件权限**：确保有写入权限
2. **检查文件是否被占用**：确保文件没有被其他程序打开
3. **查看错误信息**：代码会输出详细的错误信息

## 📊 支持情况总结

| 格式 | 文件扫描 | 音频识别 | 标签写入 | 备注 |
|------|---------|---------|---------|------|
| MP3  | ✅ | ✅ | ✅ | 完全支持 |
| FLAC | ✅ | ✅ | ✅ | 完全支持 |
| M4A  | ✅ | ✅ | ✅ | 完全支持 |
| WMA  | ✅ | ⚠️ | ✅ | 识别需要解码器支持 |

## 🎯 建议

1. **对于 WMA 文件**：
   - 如果主要用于标签更新，代码已完全支持
   - 如果需要音频识别，确保系统安装了 FFmpeg

2. **对于群晖部署**：
   - Docker 镜像已包含必要的解码器
   - 如果遇到问题，可以在 Dockerfile 中显式添加 FFmpeg

3. **测试建议**：
   - 先用少量文件测试
   - 确认标签写入正常后再批量处理

---

**更新日期**：已添加 WMA 和 M4A 格式支持
**测试状态**：代码已更新，建议进行实际测试验证

