# DiskJockey - 音乐标签自动识别和更新工具

## 项目概述

DiskJockey 是一个自动识别和更新音频文件标签的工具，支持 MP3、FLAC、M4A 和 WMA 格式。它使用 AcoustID API 通过音频指纹技术来识别歌曲并自动更新文件的元数据标签。

## 主要特性

- **多格式支持**: 支持 MP3、FLAC、M4A 和 WMA 音频格式
- **音频指纹识别**: 使用 AcoustID 和 Chromaprint 进行精确的音频匹配
- **批量处理**: 可以批量处理整个音乐目录
- **智能重命名**: 根据标签信息自动重命名文件
- **标签对比**: 显示现有标签与建议标签的对比
- **置信度验证**: 只更新高置信度的匹配结果
- **额外验证机制**: 包括分数差验证和标题相似度检查

## 安装要求

- Python 3.6+
- AcoustID API 密钥 (免费获取)
- Chromaprint 库及 fpcalc 工具

### 安装步骤

1. 克隆或下载项目代码
2. 安装 Python 依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 安装 fpcalc 工具：
   - Windows: 从 https://acoustid.org/chromaprint 下载预编译版本
   - macOS: `brew install chromaprint`
   - Linux: `sudo apt-get install libchromaprint-dev`

## 配置选项

DiskJockey 支持以下环境变量配置：

- `ACOUSTID_API_KEY`: AcoustID API 密钥（通过环境变量或 .env 文件设置）
- `MUSIC_DIR`: 音乐文件目录路径（默认值: /music）
- `CONFIDENCE_THRESHOLD`: 置信度阈值，只有匹配分数高于此值的结果才会被应用（默认值: 0.85）
- `ADDITIONAL_VALIDATION`: 启用额外验证机制（默认值: True）
- `MIN_SCORE_GAP`: 最佳匹配与次佳匹配之间的最小分数差（默认值: 0.1）
- `DEBUG_MODE`: 调试模式，输出详细信息（默认值: False）
- `RENAME_FILES`: 是否自动重命名文件（默认值: True）
- `FILE_NAME_FORMAT`: 文件名格式（默认值: {artist} - {title}）
- `SHOW_MULTIPLE_MATCHES`: 是否显示多个匹配候选（默认值: True）
- `REQUIRE_CONFIRMATION`: 是否要求人工确认（默认值: False）
- `SKIP_EXISTING_TAGS`: 是否跳过已有标签的文件（默认值: False）
- `SHOW_TAG_COMPARISON`: 是否显示新旧标签对比（默认值: True）
- `LOW_CONFIDENCE_THRESHOLD`: 低置信度阈值，低于此值的匹配将被标记为需要检查（默认值: 0.7）

## Docker 部署

### Docker Compose 配置

```yaml
version: '3.8'

services:
  diskjockey:
    build: .
    container_name: diskjockey
    environment:
      - ACOUSTID_API_KEY=${ACOUSTID_API_KEY}  # 请通过环境变量或 .env 文件设置
      - MUSIC_DIR=/music  # 容器内音乐目录路径
      - CONFIDENCE_THRESHOLD=0.85  # 置信度阈值，提高以减少错误匹配
      - ADDITIONAL_VALIDATION=true  # 启用额外验证机制
      - MIN_SCORE_GAP=0.1  # 最佳匹配与次佳匹配之间的最小分数差
      - DEBUG_MODE=false  # 调试模式，设为 false 以减少输出
      - RENAME_FILES=true  # 是否自动重命名文件
      - FILE_NAME_FORMAT={artist} - {title}  # 文件名格式
      - SHOW_MULTIPLE_MATCHES=true  # 是否显示多个匹配候选
      - REQUIRE_CONFIRMATION=false  # 是否要求人工确认（Docker环境通常设为false）
      - SKIP_EXISTING_TAGS=false  # 是否跳过已有标签的文件
      - SHOW_TAG_COMPARISON=true  # 是否显示新旧标签对比
      - LOW_CONFIDENCE_THRESHOLD=0.7  # 低置信度阈值
    volumes:
      - "${MUSIC_HOST_PATH:-/path/to/your/music}:/music:rw"  # 请替换为你的本地音乐文件夹路径
    # 如果需要运行完成后自动退出，请取消下面的注释
    # command: ["python", "diskjockey.py"]
```

## 匹配验证机制

DiskJockey 实现了多层验证机制以确保标签匹配的准确性：

1. **置信度阈值**: 只有匹配分数高于 CONFIDENCE_THRESHOLD 的结果才会被考虑
2. **分数差验证**: 检查最佳匹配与次佳匹配之间的分数差，如果差值小于 MIN_SCORE_GAP，会发出警告
3. **标题相似度检查**: 使用 difflib.SequenceMatcher 检查建议标题与现有标题的相似度，如果相似度低于30%，会发出警告
4. **处理结果报告**: 处理完成后生成详细的报告，包含成功、失败、低置信度和需要手动检查的文件列表

## 使用说明

运行 DiskJockey 后，它会自动扫描指定目录中的所有音频文件，并尝试识别每首歌曲。对于每个识别到的歌曲，它会显示现有标签和建议标签的对比，然后根据配置自动更新标签和重命名文件。

处理完成后，DiskJockey 会生成一份详细的处理结果报告，包括：
- 成功处理的文件数量
- 处理失败的文件列表
- 低置信度匹配的文件列表
- 需要手动检查的文件列表

## 注意事项

- 请务必使用自己的 AcoustID API 密钥以获得更稳定的服务
- 建议在运行前备份音乐文件
