# DiskJockey 群晖 NAS Docker 部署指南

## 目录
1. [准备工作](#准备工作)
2. [文件准备](#文件准备)
3. [部署步骤](#部署步骤)
4. [配置说明](#配置说明)
5. [使用方法](#使用方法)
6. [常见问题](#常见问题)

---

## 准备工作

### 1. 确保群晖已安装 Docker

1. 登录群晖 DSM
2. 打开 **套件中心**
3. 搜索并安装 **Docker**
4. 等待安装完成

### 2. 准备项目文件

将以下文件上传到群晖的某个目录（例如：`/volume1/docker/diskjockey/`）：

- `diskjockey_nas.py` - 适配群晖的代码文件
- `Dockerfile` - Docker 构建文件
- `docker-compose.yml` - Docker Compose 配置
- `requirements.txt` - Python 依赖列表
- `.dockerignore` - Docker 忽略文件

### 3. 确定音乐目录路径

在群晖上找到你的音乐文件存放位置，常见路径：
- `/volume1/music`（示例路径）
- `/volume1/music`
- `/volume1/共享文件夹名/音乐`
- `/volume1/audio`

**如何查找路径：**
1. 在 File Station 中右键点击音乐文件夹
2. 选择"属性"
3. 查看"位置"信息

**注意：** 如果路径包含空格或中文字符，在 `docker-compose.yml` 中需要用引号括起来。

---

## 文件准备

### 方法一：通过 File Station 上传

1. 在 DSM 中打开 **File Station**
2. 导航到目标目录（如 `/volume1/docker/`）
3. 创建新文件夹 `diskjockey`
4. 将项目文件上传到此文件夹

### 方法二：通过 SCP/SFTP 上传

使用 SCP 客户端（如 WinSCP、FileZilla）连接群晖：

```bash
# 示例：使用 scp 命令
scp -r diskjockey/ admin@群晖IP:/volume1/docker/
```

---

## 部署步骤

### 步骤 1：通过 SSH 连接到群晖

1. 在 DSM 中启用 SSH：
   - **控制面板** → **终端机和 SNMP** → 勾选 **启用 SSH 服务**
   - 设置端口（默认 22）

2. 使用 SSH 客户端连接：
   ```bash
   ssh admin@群晖IP地址
   ```

3. 切换到项目目录：
   ```bash
   cd /volume1/docker/diskjockey
   ```

### 步骤 2：修改配置文件

编辑 `docker-compose.yml` 文件，修改音乐目录路径：

```bash
# 使用 nano 编辑器
nano docker-compose.yml
```

找到以下部分并修改：

```yaml
volumes:
  # 将路径改为你的实际音乐目录路径
  # 注意：如果路径包含空格或中文字符，需要用引号括起来
  - "/volume1/music:/music"
```

**当前配置示例：**
- 群晖路径：`/volume1/music`
- 容器内路径：`/music`

**重要：**
- 左侧是群晖的实际路径
- 右侧 `/music` 是容器内的挂载点，一般不需要修改
- 如果路径包含中文或空格，确保正确转义

### 步骤 2.5：配置 Docker 镜像加速器（可选，推荐）

如果遇到无法从 Docker Hub 拉取镜像的问题（网络超时），可以配置镜像加速器：

#### 方法 1：通过群晖 DSM 图形界面配置（推荐）

1. 打开 **Docker** 套件
2. 点击 **注册表** → **设置**
3. 在 **Docker Hub** 或 **注册表镜像** 中添加镜像加速器地址
4. 常用的镜像加速器：
   - 阿里云：`https://your-id.mirror.aliyuncs.com`（需要登录阿里云获取专属地址）
   - 腾讯云：`https://mirror.ccs.tencentyun.com`
   - 网易：`https://hub-mirror.c.163.com`
   - 中科大：`https://docker.mirrors.ustc.edu.cn`
   - Docker 中国：`https://registry.docker-cn.com`

#### 方法 2：通过 SSH 配置 daemon.json

```bash
# 创建或编辑 Docker daemon 配置文件
sudo nano /etc/docker/daemon.json
```

添加以下内容（如果文件已存在，合并 `registry-mirrors` 数组）：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://registry.docker-cn.com"
  ]
}
```

保存后重启 Docker 服务：

```bash
# 重启 Docker 服务
sudo synoservice --restart pkgctl-Docker

# 或者
sudo systemctl restart docker
```

验证配置：

```bash
sudo docker info | grep -A 10 "Registry Mirrors"
```

**注意：** 配置镜像加速器后，需要重新尝试构建镜像。

### 步骤 3：构建和运行容器

#### 方法 A：使用 Docker Compose（推荐）

```bash
# 构建镜像（如果遇到权限问题，在命令前添加 sudo）
sudo docker-compose build

# 启动容器
sudo docker-compose up -d

# 查看日志
sudo docker-compose logs -f
```

**注意：** 在群晖 NAS 上，通常需要使用 `sudo` 来执行 Docker 命令。如果当前用户是 root，则不需要 sudo。

#### 方法 B：使用 Docker 命令

```bash
# 构建镜像（如果遇到权限问题，在命令前添加 sudo）
sudo docker build -t diskjockey .

# 运行容器
# 注意：如果路径包含空格或中文字符，需要用引号括起来
sudo docker run -d \
  --name diskjockey \
  -v "/volume1/music:/music" \
  -e MUSIC_DIR=/music \
  -e ACOUSTID_API_KEY=${ACOUSTID_API_KEY} \
  -e CONFIDENCE_THRESHOLD=0.7 \
  -e RENAME_FILES=True \
  diskjockey
```

### 步骤 4：验证运行

```bash
# 查看容器状态（如果遇到权限问题，在命令前添加 sudo）
sudo docker ps

# 查看容器日志
sudo docker logs diskjockey

# 实时查看日志
sudo docker logs -f diskjockey
```

如果看到类似以下输出，说明运行成功：

```
============================================================
DiskJockey - 音乐标签自动识别和更新工具
============================================================
配置信息:
  音乐目录: /music
  置信度阈值: 0.7
  自动重命名: True
  文件名格式: {artist} - {title}
  调试模式: False
============================================================
--- DiskJockey 开始工作 ---
扫描目录: /music
...
```

---

## 配置说明

### 环境变量配置

在 `docker-compose.yml` 中可以配置以下环境变量：

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `MUSIC_DIR` | 音乐目录（容器内路径） | `/music` | `/music` |
| `ACOUSTID_API_KEY` | AcoustID API 密钥 | `${ACOUSTID_API_KEY}` | `你的API密钥` |
| `CONFIDENCE_THRESHOLD` | 置信度阈值 | `0.7` | `0.8` |
| `RENAME_FILES` | 是否重命名文件 | `True` | `True` 或 `False` |
| `FILE_NAME_FORMAT` | 文件名格式 | `{artist} - {title}` | `{title}` 或 `{title} - {artist}` |
| `DEBUG_MODE` | 调试模式 | `False` | `True` 或 `False` |

### 文件名格式选项

- `{title}` - 只使用歌曲标题
- `{artist} - {title}` - 艺术家 - 标题（默认）
- `{title} - {artist}` - 标题 - 艺术家

### 修改配置

1. 编辑 `docker-compose.yml`
2. 修改相应的环境变量
3. 重启容器：
   ```bash
   docker-compose restart
   ```

---

## 使用方法

### 一次性运行

容器启动后会自动运行一次，处理完所有文件后容器会停止。

### 定时运行（推荐）

#### 方法 1：使用群晖任务计划器

1. 在 DSM 中打开 **控制面板** → **任务计划器**
2. 点击 **新增** → **计划的任务** → **用户定义的脚本**
3. 设置任务：
   - **任务名称**：DiskJockey
   - **用户**：root
   - **运行命令**：
     ```bash
     cd /volume1/docker/diskjockey && docker-compose restart diskjockey
     ```
4. 设置计划（例如：每天凌晨 2 点运行）
5. 保存并启用任务

#### 方法 2：使用 Cron（SSH）

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天凌晨 2 点运行）
0 2 * * * cd /volume1/docker/diskjockey && docker-compose restart diskjockey
```

#### 方法 3：修改 Docker Compose 为持续运行

如果需要容器持续运行并定期执行，可以创建一个包装脚本：

创建 `run.sh`：
```bash
#!/bin/bash
while true; do
    python /app/diskjockey_nas.py
    # 等待 24 小时后再次运行
    sleep 86400
done
```

修改 `Dockerfile` 的 CMD：
```dockerfile
COPY run.sh .
RUN chmod +x run.sh
CMD ["./run.sh"]
```

### 手动运行

```bash
# 进入项目目录
cd /volume1/docker/diskjockey

# 重启容器（会重新运行脚本）
docker-compose restart

# 或者直接执行
docker-compose run --rm diskjockey
```

---

## 常见问题

### 1. 容器无法启动

**检查日志：**
```bash
docker logs diskjockey
```

**常见原因：**
- 音乐目录路径不正确
- 权限问题
- Docker 服务未启动

**解决方法：**
- 检查 `docker-compose.yml` 中的路径是否正确
- 确保 Docker 服务正在运行
- 检查文件权限

### 2. 找不到音乐文件

**检查：**
```bash
# 进入容器检查
docker exec -it diskjockey ls -la /music

# 检查群晖路径是否存在
ls -la "/volume1/music"
```

**解决方法：**
- 确认 `docker-compose.yml` 中的 volumes 配置正确
- 检查群晖路径是否存在（注意路径中的空格和中文字符）
- 确保路径有读取权限
- 如果路径包含空格或中文字符，确保使用引号括起来

### 3. fpcalc 未找到

**检查：**
```bash
docker exec -it diskjockey fpcalc --version
```

**解决方法：**
- 重新构建镜像：`docker-compose build --no-cache`
- 检查 Dockerfile 中的安装命令是否正确

### 4. Docker 权限错误（permission denied）

**错误信息：**
```
Got permission denied while trying to connect to the Docker daemon socket
```

**原因：**
- 当前用户没有权限访问 Docker daemon socket
- 用户不在 docker 组中
- 需要使用 root 权限或 sudo

**解决方法：**

#### 方法 1：使用 sudo（推荐）

在所有 Docker 命令前添加 `sudo`：

```bash
# 构建镜像
sudo docker-compose build

# 启动容器
sudo docker-compose up -d

# 查看日志
sudo docker-compose logs -f

# 查看容器状态
sudo docker ps
```

#### 方法 2：将用户添加到 docker 组

```bash
# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录 SSH 会话使更改生效
# 或者执行以下命令刷新组权限
newgrp docker

# 验证是否成功
docker ps
```

**注意：** 在群晖 NAS 上，通常建议使用 `sudo` 或直接使用 `root` 用户。

#### 方法 3：使用 root 用户

```bash
# 切换到 root 用户
sudo su -

# 然后执行 Docker 命令（不需要 sudo）
docker-compose build
docker-compose up -d
```

#### 方法 4：通过群晖 DSM 图形界面

如果 SSH 权限有问题，可以通过 DSM 的 Docker 图形界面操作：

1. 打开 **Docker** 套件
2. 使用 **镜像** → **新增** → **从文件添加** 来构建镜像
3. 使用 **容器** → **新增** 来创建和运行容器

### 5. Docker 镜像拉取失败（网络超时）

**错误信息：**
```
failed to solve: rpc error: code = Unknown desc = failed to solve with frontend dockerfile.v0: 
failed to create LLB definition: failed to do request: Head "https://registry-1.docker.io/v2/...": 
dial tcp ...:443: i/o timeout
```

或

```
Get "https://registry-1.docker.io/v2/": dial tcp ...:443: i/o timeout
```

**原因：**
- 无法访问 Docker Hub（网络问题、防火墙、或在中国大陆需要镜像源）
- Docker Hub 访问速度慢或超时

**解决方法：**

#### 方法 1：配置 Docker 镜像加速器（推荐）

**通过群晖 DSM：**
1. 打开 **Docker** 套件
2. 点击 **注册表** → **设置**
3. 添加镜像加速器地址（见上方"步骤 2.5"）

**通过 SSH：**
```bash
# 创建或编辑配置文件
sudo nano /etc/docker/daemon.json

# 添加以下内容
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}

# 重启 Docker 服务
sudo synoservice --restart pkgctl-Docker
```

#### 方法 2：使用代理

如果群晖 NAS 配置了代理，确保 Docker 可以使用代理：

```bash
# 设置代理环境变量（临时）
export HTTP_PROXY=http://proxy-server:port
export HTTPS_PROXY=http://proxy-server:port

# 然后执行构建命令
sudo docker-compose build
```

#### 方法 3：手动下载镜像

如果镜像加速器也无法使用，可以尝试：

```bash
# 手动拉取基础镜像（使用镜像加速器或代理）
sudo docker pull python:3.11-slim

# 然后再构建
sudo docker-compose build
```

#### 方法 4：使用国内镜像源构建

修改 `Dockerfile`，使用国内镜像源：

```dockerfile
# 在 Dockerfile 开头添加（使用阿里云镜像源）
FROM registry.cn-hangzhou.aliyuncs.com/library/python:3.11-slim

# 或者在 apt-get 命令中使用国内镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list
```

**注意：** 使用国内镜像源时，确保镜像源地址正确且可访问。

### 6. 文件权限错误

如果遇到文件写入权限问题：

```bash
# 检查文件权限
ls -la "/volume1/music"

# 修改权限（谨慎使用）
chmod -R 755 "/volume1/music"
```

或者修改容器运行用户（在 Dockerfile 中添加）：
```dockerfile
RUN useradd -m -u 1000 diskjockey
USER diskjockey
```

### 7. 中文文件名乱码

确保：
- 系统使用 UTF-8 编码
- Docker 容器环境变量设置正确
- 文件系统支持 UTF-8

### 8. 查看详细日志

启用调试模式：
```yaml
environment:
  - DEBUG_MODE=True
```

然后查看日志：
```bash
docker-compose logs -f
```

### 9. 停止和删除容器

```bash
# 停止容器
docker-compose stop

# 删除容器
docker-compose down

# 删除容器和镜像
docker-compose down --rmi all
```

---

## 性能优化建议

1. **批量处理**：如果音乐文件很多，建议在低峰期运行
2. **资源限制**：在 `docker-compose.yml` 中设置 CPU 和内存限制
3. **增量处理**：可以修改代码，跳过已处理的文件（通过检查标签）

---

## 安全建议

1. **API 密钥**：如果使用自己的 API 密钥，不要提交到公共仓库
2. **文件备份**：首次运行前，建议备份音乐文件
3. **权限控制**：使用最小权限原则运行容器

---

## 更新代码

如果需要更新代码：

```bash
# 1. 上传新文件到群晖
# 2. 重新构建镜像
docker-compose build

# 3. 重启容器
docker-compose up -d
```

---

## 技术支持

如果遇到问题：
1. 查看容器日志：`docker logs diskjockey`
2. 启用调试模式查看详细信息
3. 检查文件权限和路径配置

---

## 附录

### 常用 Docker 命令

```bash
# 查看运行中的容器
docker ps

# 查看所有容器
docker ps -a

# 查看镜像
docker images

# 进入容器
docker exec -it diskjockey /bin/bash

# 查看容器资源使用
docker stats diskjockey
```

### 群晖路径说明

- `/volume1/` - 第一个存储卷
- `/volume2/` - 第二个存储卷（如果有）
- 共享文件夹通常在 `/volume1/共享文件夹名/`
- **默认配置路径**：`/volume1/music`
- **注意**：路径中包含空格和中文字符时，在配置文件中需要用引号括起来

---

**祝使用愉快！