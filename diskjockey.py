import os
import sys
import acoustid
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.asf import ASF  # WMA 格式支持
from mutagen.mp4 import MP4  # M4A 格式支持
import difflib

# 设置输出编码，避免 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 如果 fpcalc 不在 PATH 中，可以手动指定路径
# 方式1: 指定 fpcalc.exe 所在的目录（推荐）
FPCALC_DIR = os.getenv('FPCALC_DIR', '')  # 可选：指定 fpcalc.exe 所在的目录
# 方式2: 或者直接指定 fpcalc.exe 的完整路径
# FPCALC_PATH = os.getenv('FPCALC_PATH', '')  # 可选：直接指定 fpcalc.exe 的完整路径

# 将 fpcalc 所在目录添加到 PATH 环境变量
if FPCALC_DIR and os.path.exists(FPCALC_DIR):
    os.environ['PATH'] = FPCALC_DIR + os.pathsep + os.environ.get('PATH', '')
    print(f"已添加 fpcalc 路径到环境变量: {FPCALC_DIR}")
else:
    # 如果目录不存在，尝试检查是否是路径问题，给出提示
    print(f"警告: 指定的 fpcalc 目录不存在: {FPCALC_DIR}")
    print("请确认路径是否正确，或手动修改 FPCALC_DIR 变量")

# 配置 - 从环境变量读取，如果不存在则使用默认值
API_KEY = os.getenv('ACOUSTID_API_KEY', 'YOUR_API_KEY_HERE')
MUSIC_DIR = os.getenv('MUSIC_DIR', './music')

# 验证 API_KEY 是否已设置
if API_KEY == 'YOUR_API_KEY_HERE':
    print("错误: 未设置 AcoustID API 密钥！")
    print("请设置 ACOUSTID_API_KEY 环境变量，或修改代码中的默认值")
    print("获取免费 API 密钥: https://acoustid.org/api")
    import sys
    sys.exit(1)

CONFIDENCE_THRESHOLD = 0.85  # 置信度阈值，高于此值才自动修改（提高默认值以减少错误）
ADDITIONAL_VALIDATION = True  # 启用额外验证机制
MIN_SCORE_GAP = 0.1  # 最佳匹配与次佳匹配之间的最小分数差，用于进一步验证匹配的可靠性
DEBUG_MODE = False  # 设置为 True 可以查看 API 返回的原始数据
RENAME_FILES = True  # 是否自动重命名文件（如果歌曲名与文件名不一致）
FILE_NAME_FORMAT = "{artist} - {title}"  # 文件名格式，可选: "{title}", "{artist} - {title}", "{title} - {artist}"
SHOW_MULTIPLE_MATCHES = True  # 是否显示多个匹配候选（帮助判断）
REQUIRE_CONFIRMATION = False  # 是否要求人工确认（设置为 False 进行批量处理）
SKIP_EXISTING_TAGS = False  # 是否跳过已有标签的文件（避免覆盖正确的标签）
SHOW_TAG_COMPARISON = True  # 是否显示新旧标签对比
LOW_CONFIDENCE_THRESHOLD = 0.7  # 低置信度阈值，低于此值需要用户检查

# 处理结果统计
processing_results = {
    'success': [],      # 成功处理的文件
    'failed': [],       # 处理失败的文件
    'low_confidence': [],  # 低置信度匹配的文件
    'manual_check': []  # 需要用户手动检查的文件
}

def read_existing_tags(file_path):
    """读取文件现有的标签信息"""
    existing_tags = {
        'title': '',
        'artist': '',
        'album': '',
        'year': '',
        'genre': '',
        'tracknumber': ''
    }
    
    try:
        if file_path.endswith('.mp3'):
            audio = EasyID3(file_path)
            existing_tags['title'] = audio.get('title', [''])[0] if 'title' in audio else ''
            existing_tags['artist'] = audio.get('artist', [''])[0] if 'artist' in audio else ''
            existing_tags['album'] = audio.get('album', [''])[0] if 'album' in audio else ''
            existing_tags['year'] = audio.get('date', [''])[0] if 'date' in audio else ''
            existing_tags['genre'] = audio.get('genre', [''])[0] if 'genre' in audio else ''
            existing_tags['tracknumber'] = audio.get('tracknumber', [''])[0] if 'tracknumber' in audio else ''
        elif file_path.endswith('.flac'):
            audio = FLAC(file_path)
            existing_tags['title'] = audio.get('title', [''])[0] if 'title' in audio else ''
            existing_tags['artist'] = audio.get('artist', [''])[0] if 'artist' in audio else ''
            existing_tags['album'] = audio.get('album', [''])[0] if 'album' in audio else ''
            existing_tags['year'] = audio.get('date', [''])[0] if 'date' in audio else ''
            existing_tags['genre'] = audio.get('genre', [''])[0] if 'genre' in audio else ''
            existing_tags['tracknumber'] = audio.get('tracknumber', [''])[0] if 'tracknumber' in audio else ''
        elif file_path.endswith('.m4a'):
            audio = MP4(file_path)
            existing_tags['title'] = audio.get('\xa9nam', [''])[0] if '\xa9nam' in audio else ''
            existing_tags['artist'] = audio.get('\xa9ART', [''])[0] if '\xa9ART' in audio else ''
            existing_tags['album'] = audio.get('\xa9alb', [''])[0] if '\xa9alb' in audio else ''
            existing_tags['year'] = audio.get('\xa9day', [''])[0] if '\xa9day' in audio else ''
            existing_tags['genre'] = audio.get('\xa9gen', [''])[0] if '\xa9gen' in audio else ''
            if 'trkn' in audio and len(audio['trkn']) > 0:
                existing_tags['tracknumber'] = str(audio['trkn'][0][0])
        elif file_path.endswith('.wma'):
            audio = ASF(file_path)
            existing_tags['title'] = audio.get('Title', [''])[0] if 'Title' in audio else ''
            existing_tags['artist'] = audio.get('Author', [''])[0] if 'Author' in audio else ''
            existing_tags['album'] = audio.get('WM/AlbumTitle', [''])[0] if 'WM/AlbumTitle' in audio else ''
            existing_tags['year'] = audio.get('WM/Year', [''])[0] if 'WM/Year' in audio else ''
            existing_tags['genre'] = audio.get('WM/Genre', [''])[0] if 'WM/Genre' in audio else ''
            existing_tags['tracknumber'] = audio.get('WM/TrackNumber', [''])[0] if 'WM/TrackNumber' in audio else ''
    except Exception as e:
        # 如果读取失败，返回空标签
        pass
    
    return existing_tags

def update_tags(file_path, title, artist, album='', year='', genre='', tracknumber=''):
    """更新音频文件的标签"""
    try:
        if file_path.endswith('.mp3'):
            audio = EasyID3(file_path)
        elif file_path.endswith('.flac'):
            audio = FLAC(file_path)
        elif file_path.endswith('.m4a'):
            audio = MP4(file_path)
        elif file_path.endswith('.wma'):
            audio = ASF(file_path)
        else:
            return False
        
        # 更新标签（只更新非空值）
        if title:
            if file_path.endswith('.mp3'):
                audio['title'] = title
            elif file_path.endswith('.flac'):
                audio['title'] = title
            elif file_path.endswith('.m4a'):
                audio['\xa9nam'] = title
            elif file_path.endswith('.wma'):
                audio['Title'] = title
        
        if artist:
            if file_path.endswith('.mp3'):
                audio['artist'] = artist
            elif file_path.endswith('.flac'):
                audio['artist'] = artist
            elif file_path.endswith('.m4a'):
                audio['\xa9ART'] = artist
            elif file_path.endswith('.wma'):
                audio['Author'] = artist
        
        if album:
            if file_path.endswith('.mp3'):
                audio['album'] = album
            elif file_path.endswith('.flac'):
                audio['album'] = album
            elif file_path.endswith('.m4a'):
                audio['\xa9alb'] = album
            elif file_path.endswith('.wma'):
                audio['WM/AlbumTitle'] = album
        
        if year:
            if file_path.endswith('.mp3'):
                audio['date'] = str(year)
            elif file_path.endswith('.flac'):
                audio['date'] = str(year)
            elif file_path.endswith('.m4a'):
                audio['\xa9day'] = str(year)
            elif file_path.endswith('.wma'):
                audio['WM/Year'] = str(year)
        
        if genre:
            if file_path.endswith('.mp3'):
                audio['genre'] = genre
            elif file_path.endswith('.flac'):
                audio['genre'] = genre
            elif file_path.endswith('.m4a'):
                audio['\xa9gen'] = genre
            elif file_path.endswith('.wma'):
                audio['WM/Genre'] = genre
        
        if tracknumber:
            if file_path.endswith('.mp3'):
                audio['tracknumber'] = str(tracknumber)
            elif file_path.endswith('.flac'):
                audio['tracknumber'] = str(tracknumber)
            elif file_path.endswith('.m4a'):
                audio['trkn'] = [(int(tracknumber), 0)]
            elif file_path.endswith('.wma'):
                audio['WM/TrackNumber'] = str(tracknumber)
        
        # 保存更改
        audio.save()
        return True
    except Exception as e:
        print(f"更新标签时出错: {e}")
        return False

def rename_file_if_needed(file_path, title, artist):
    """根据标签信息重命名文件"""
    if not RENAME_FILES:
        return file_path
    
    if not title or not artist:
        return file_path
    
    # 获取文件扩展名
    file_dir, file_ext = os.path.split(file_path)
    new_filename = FILE_NAME_FORMAT.format(artist=artist, title=title) + file_ext[file_ext.rfind('.'):]
    
    # 清理文件名中的非法字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        new_filename = new_filename.replace(char, '_')
    
    new_file_path = os.path.join(file_dir, new_filename)
    
    # 如果新文件名与原文件名不同，则重命名
    if file_path != new_file_path:
        # 确保目标文件名不与现有文件冲突
        counter = 1
        original_new_path = new_file_path
        while os.path.exists(new_file_path):
            name_part = FILE_NAME_FORMAT.format(artist=artist, title=title)
            new_filename = f"{name_part} ({counter}){file_ext[file_ext.rfind('.'):]}"
            for char in illegal_chars:
                new_filename = new_filename.replace(char, '_')
            new_file_path = os.path.join(file_dir, new_filename)
            counter += 1
        
        try:
            os.rename(file_path, new_file_path)
            print(f"  文件已重命名: {os.path.basename(file_path)} -> {os.path.basename(new_file_path)}")
            return new_file_path
        except Exception as e:
            print(f"  重命名失败: {e}")
            return file_path
    else:
        return file_path

def run_disk_jockey(directory):
    print(f"--- DiskJockey 开始工作 ---")
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.mp3', '.flac', '.m4a', '.wma')):
                file_path = os.path.join(root, file)
                print(f"\n正在扫描: {file}")
                
                try:
                    # 识别歌曲，获取更多元数据信息
                    duration, fingerprint = acoustid.fingerprint_file(file_path)
                    results = acoustid.lookup(API_KEY, fingerprint, duration, 
                                             meta=['recordings', 'releases', 'releasegroups'])
                    
                    # 调试模式：打印原始数据
                    if DEBUG_MODE:
                        import json
                        print(f"API 返回数据: {json.dumps(results, indent=2, ensure_ascii=False)[:1000]}")
                    
                    # 收集所有符合条件的匹配结果
                    all_matches = []
                    if 'results' in results:
                        for result in results['results']:
                            score = result.get('score', 0)
                            if score >= CONFIDENCE_THRESHOLD:
                                # 获取录音信息
                                if 'recordings' in result and len(result['recordings']) > 0:
                                    recording = result['recordings'][0]
                                    
                                    # 获取标题和艺术家
                                    title = recording.get('title', '')
                                    artist = ''
                                    if 'artists' in recording and len(recording['artists']) > 0:
                                        artist = recording['artists'][0].get('name', '')
                                    
                                    # 获取专辑信息
                                    album = None
                                    year = None
                                    genre = None
                                    tracknumber = None
                                    
                                    # 尝试从多个来源获取专辑信息
                                    # 方法1: 从 result 的 releases 获取
                                    if 'releases' in result and len(result['releases']) > 0:
                                        release = result['releases'][0]
                                        album = release.get('title', '')
                                        if 'date' in release:
                                            date_info = release['date']
                                            if isinstance(date_info, dict):
                                                year = date_info.get('year', '')
                                            else:
                                                date_str = str(date_info)
                                                year = date_str.split('-')[0] if '-' in date_str else date_str
                                    
                                    # 方法2: 从 recording 的 releases 获取（如果 result 中没有）
                                    if not album and 'releases' in recording and len(recording['releases']) > 0:
                                        release = recording['releases'][0]
                                        album = release.get('title', '')
                                        if 'date' in release:
                                            date_info = release['date']
                                            if isinstance(date_info, dict):
                                                year = date_info.get('year', '')
                                            else:
                                                date_str = str(date_info)
                                                year = date_str.split('-')[0] if '-' in date_str else date_str
                                    
                                    # 方法3: 从 recording 的 releasegroups 获取（作为备选）
                                    if not album and 'releasegroups' in recording and len(recording['releasegroups']) > 0:
                                        releasegroup = recording['releasegroups'][0]
                                        album = releasegroup.get('title', '')
                                    
                                    # 尝试获取流派
                                    if 'releasegroups' in recording and len(recording['releasegroups']) > 0:
                                        releasegroup = recording['releasegroups'][0]
                                        if 'type' in releasegroup:
                                            genre = releasegroup['type']
                                    
                                    # 尝试获取曲目号
                                    if 'tracks' in recording and len(recording['tracks']) > 0:
                                        track = recording['tracks'][0]
                                        if 'position' in track:
                                            tracknumber = track['position']
                                    
                                    all_matches.append({
                                        'score': score,
                                        'title': title,
                                        'artist': artist,
                                        'album': album or '',
                                        'year': year or '',
                                        'genre': genre or '',
                                        'tracknumber': tracknumber or ''
                                    })
                    
                    # 按分数排序，选择最佳匹配
                    if all_matches:
                        all_matches.sort(key=lambda x: x['score'], reverse=True)
                        best_match = all_matches[0]
                        
                        # 检查是否有次佳匹配用于验证
                        second_best = None
                        if len(all_matches) > 1:
                            second_best = all_matches[1]
                            score_gap = best_match['score'] - second_best['score']
                            
                            # 如果最佳匹配与次佳匹配分数差小于阈值，发出警告
                            if ADDITIONAL_VALIDATION and score_gap < MIN_SCORE_GAP:
                                print(f"⚠️  警告: 最佳匹配与次佳匹配分数差 ({score_gap:.2%}) 小于阈值 ({MIN_SCORE_GAP:.2%})")
                                print(f"  最佳匹配: {best_match['score']:.2%} - {best_match['artist']} - {best_match['title']}")
                                print(f"  次佳匹配: {second_best['score']:.2%} - {second_best['artist']} - {second_best['title']}")
                                print(f"  建议人工确认此匹配的准确性")
                        
                        # 显示多个候选（如果启用）
                        if SHOW_MULTIPLE_MATCHES and len(all_matches) > 1:
                            print(f"找到 {len(all_matches)} 个匹配候选（分数 >= {CONFIDENCE_THRESHOLD}）:")
                            for i, match in enumerate(all_matches[:5], 1):  # 最多显示5个
                                print(f"  [{i}] 分数: {match['score']:.2%} - {match['artist']} - {match['title']}")
                                if match['album']:
                                    print(f"      专辑: {match['album']}")
                            print(f"  选择最高分匹配: {best_match['score']:.2%}")
                    
                        if best_match:
                            # 读取现有标签
                            existing_tags = read_existing_tags(file_path)
                            has_existing_tags = bool(existing_tags.get('title') or existing_tags.get('artist'))
                            
                            # 如果设置了跳过已有标签，且文件已有标签，则跳过
                            if SKIP_EXISTING_TAGS and has_existing_tags:
                                print("  跳过（已有标签）")
                                processing_results['success'].append({
                                    'file': file_path,
                                    'status': 'skipped_existing_tags',
                                    'message': '已跳过，文件已有标签'
                                })
                                continue
                            
                            # 显示新旧标签对比（如果启用）
                            if SHOW_TAG_COMPARISON:
                                print(f"  标签对比:")
                                print(f"    标题: {existing_tags['title']} -> {best_match['title']}")
                                print(f"    艺术家: {existing_tags['artist']} -> {best_match['artist']}")
                                print(f"    专辑: {existing_tags['album']} -> {best_match['album']}")
                                print(f"    年份: {existing_tags['year']} -> {best_match['year']}")
                                print(f"    流派: {existing_tags['genre']} -> {best_match['genre']}")
                                print(f"    曲目: {existing_tags['tracknumber']} -> {best_match['tracknumber']}")
                            
                            # 额外验证：检查标题相似度 - 已移除，不再检查现有标题与建议标题的相似度
                            
                            # 决定是否更新标签
                            should_update = True
                            
                            # 如果置信度较低，标记为需要检查
                            if best_match['score'] < LOW_CONFIDENCE_THRESHOLD:
                                processing_results['low_confidence'].append({
                                    'file': file_path,
                                    'score': best_match['score'],
                                    'title': best_match['title'],
                                    'artist': best_match['artist']
                                })
                                should_update = not REQUIRE_CONFIRMATION  # 低置信度时，如果需要确认则不更新
                            elif best_match['score'] < CONFIDENCE_THRESHOLD:
                                should_update = not REQUIRE_CONFIRMATION
                            
                            # 应用标签更新
                            if should_update:
                                # 先重命名文件（如果需要），避免文件被占用
                                new_file_path = rename_file_if_needed(file_path, 
                                                                     best_match['title'], 
                                                                     best_match['artist'])
                                # 如果文件被重命名，使用新路径更新标签
                                if new_file_path != file_path:
                                    file_path = new_file_path
                                
                                # 然后更新标签
                                if update_tags(file_path, 
                                               best_match['title'], 
                                               best_match['artist'],
                                               album=best_match['album'],
                                               year=best_match['year'],
                                               genre=best_match['genre'],
                                               tracknumber=best_match['tracknumber']):
                                    print("  标签已更新")
                                    processing_results['success'].append({
                                        'file': file_path,
                                        'status': 'updated',
                                        'old_title': existing_tags['title'],
                                        'old_artist': existing_tags['artist'],
                                        'new_title': best_match['title'],
                                        'new_artist': best_match['artist'],
                                        'confidence': best_match['score']
                                    })
                                else:
                                    print("  标签更新失败")
                                    processing_results['failed'].append({
                                        'file': file_path,
                                        'error': '标签更新失败',
                                        'confidence': best_match['score']
                                    })
                            else:
                                print("未更新标签")
                                processing_results['manual_check'].append({
                                    'file': file_path,
                                    'title': best_match['title'],
                                    'artist': best_match['artist'],
                                    'confidence': best_match['score'],
                                    'reason': '置信度不足或用户未确认'
                                })
                        else:
                            print("未找到高置信度的匹配，跳过。")
                            processing_results['failed'].append({
                                'file': file_path,
                                'error': '未找到高置信度匹配',
                                'confidence': 0
                            })
                    else:
                        print("未找到匹配结果")
                        processing_results['failed'].append({
                            'file': file_path,
                            'error': '未找到匹配结果',
                            'confidence': 0
                        })
                        
                except acoustid.NoBackendError as e:
                    print(f"错误: 未找到 fpcalc 工具。")
                    print(f"请按照以下步骤安装 chromaprint:")
                    print(f"1. 访问 https://acoustid.org/chromaprint 下载 Windows 版本")
                    print(f"2. 解压后将 fpcalc.exe 放到系统 PATH 中")
                    print(f"3. 或者修改代码中的 FPCALC_PATH 变量指向 fpcalc.exe 的位置")
                    print(f"详细说明请查看 '安装说明.md' 文件")
                    processing_results['failed'].append({
                        'file': file_path,
                        'error': '未找到 fpcalc 工具',
                        'confidence': 0
                    })
                except Exception as e:
                    import traceback
                    print(f"处理识别时出错: {e}")
                    print(f"详细错误信息:")
                    traceback.print_exc()
                    processing_results['failed'].append({
                        'file': file_path,
                        'error': str(e),
                        'confidence': 0
                    })

    print(f"\n--- DiskJockey 任务完成 ---")
    
    # 生成处理结果报告
    generate_processing_report()

def generate_processing_report():
    """生成处理结果报告"""
    print("\n" + "="*60)
    print("处理结果报告")
    print("="*60)
    
    # 成功处理的文件
    print(f"\n✅ 成功处理: {len(processing_results['success'])} 个文件")
    if processing_results['success']:
        for item in processing_results['success']:
            if item['status'] == 'updated':
                print(f"  - {os.path.basename(item['file'])} ({item['old_title']} -> {item['new_title']})")
            elif item['status'] == 'skipped_existing_tags':
                print(f"  - {os.path.basename(item['file'])} (已跳过，文件已有标签)")
    
    # 处理失败的文件
    print(f"\n❌ 处理失败: {len(processing_results['failed'])} 个文件")
    if processing_results['failed']:
        for item in processing_results['failed']:
            print(f"  - {os.path.basename(item['file'])} ({item['error']})")
    
    # 低置信度匹配的文件
    print(f"\n🔍 低置信度匹配: {len(processing_results['low_confidence'])} 个文件")
    if processing_results['low_confidence']:
        for item in processing_results['low_confidence']:
            print(f"  - {os.path.basename(item['file'])} (置信度: {item['score']:.2%}, {item['artist']} - {item['title']})")
    
    # 需要手动检查的文件
    print(f"\n⚠️  需要手动检查: {len(processing_results['manual_check'])} 个文件")
    if processing_results['manual_check']:
        for item in processing_results['manual_check']:
            if 'reason' in item:
                print(f"  - {os.path.basename(item['file'])} (原因: {item['reason']})")
            else:
                print(f"  - {os.path.basename(item['file'])} (置信度: {item['confidence']:.2%}, {item['artist']} - {item['title']})")
    
    print("\n" + "="*60)
    print("报告生成完成")
    print("="*60)

# 启动
if __name__ == "__main__":
    # 测试当前目录的MP3文件
    import glob
    test_files = glob.glob("*.mp3")
    if test_files:
        print(f"找到测试文件: {test_files[0]}")
        try:
            duration, fingerprint = acoustid.fingerprint_file(test_files[0])
            print(f"指纹计算成功! 时长: {duration}秒")
        except acoustid.NoBackendError as e:
            print(f"错误: 未找到 fpcalc 工具。")
            print(f"请按照以下步骤安装 chromaprint:")
            print(f"1. 访问 https://acoustid.org/chromaprint 下载 Windows 版本")
            print(f"2. 解压后将 fpcalc.exe 放到系统 PATH 中")
            print(f"3. 或者修改代码中的 FPCALC_PATH 变量指向 fpcalc.exe 的位置")
            print(f"详细说明请查看 '安装说明.md' 文件")
        except Exception as e:
            import traceback
            print(f"测试失败: {e}")
            traceback.print_exc()
    run_disk_jockey(MUSIC_DIR)
