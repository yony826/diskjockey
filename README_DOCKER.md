# DiskJockey Docker 部署快速指南

## 快速开始

### 1. 准备文件

确保以下文件在同一目录：
- `diskjockey_nas.py`
- `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`

### 2. 修改配置

编辑 `docker-compose.yml`，修改音乐目录路径：

```yaml
volumes:
  - ${MUSIC_HOST_PATH:-/path/to/your/music}:/music  # 改为你的实际路径
```

### 3. 部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 定时运行

在群晖任务计划器中添加任务，每天运行：
```bash
cd /volume1/docker/diskjockey && docker-compose restart diskjockey
```

## 配置参数

在 `docker-compose.yml` 的 `environment` 部分修改：

- `MUSIC_DIR` - 音乐目录（容器内路径，默认 `/music`）
- `CONFIDENCE_THRESHOLD` - 置信度阈值（0.7 = 70%）
- `RENAME_FILES` - 是否重命名文件（True/False）
- `FILE_NAME_FORMAT` - 文件名格式

详细说明请查看 `群晖NAS部署说明.md`

