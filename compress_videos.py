"""
橙子文化网站 - 视频批量压缩脚本
用法：python compress_videos.py

工作流程：
  - videos-original/  ← 原视频（你只需要维护这里）
  - videos/           ← 压缩后的输出（脚本自动生成，会被网页引用）

每次想替换视频，把新 mp4 放进 videos-original/ 覆盖同名文件，重跑本脚本即可。
"""
import imageio_ffmpeg
import subprocess
import shutil
import sys
from pathlib import Path

# ===== 可调参数 =====
# CRF：恒定质量，越小质量越高文件越大
#   18-23 高质量
#   24-28 中等（网页背景视频甜蜜点）
#   29-35 低质量(仅追求小文件)
SETTINGS = {
    "hero.mp4":    {"width": 1280, "crf": 30, "preset": "medium"},
    "feature.mp4": {"width": 1280, "crf": 27, "preset": "medium"},
}
DEFAULT_OPTS = {"width": 1280, "crf": 28, "preset": "medium"}
# ====================

ROOT = Path(__file__).parent
SRC = ROOT / "videos"
BACKUP = ROOT / "videos-original"

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
print(f"[INFO] 使用 ffmpeg: {FFMPEG}\n")

# 1. 如果没有 videos-original/，首次跑时把 videos/ 备份过去
if not BACKUP.exists():
    if not SRC.exists():
        print(f"[ERROR] 找不到 {SRC} 也找不到 {BACKUP}")
        sys.exit(1)
    print(f"[BACKUP] 首次运行，正在备份 videos/ → {BACKUP.name}/ ...")
    shutil.copytree(SRC, BACKUP)
    print(f"[BACKUP] 备份完成\n")

# 2. 始终以 videos-original/ 为源，遍历压缩输出到 videos/
SRC.mkdir(exist_ok=True)
videos = [f for f in BACKUP.iterdir() if f.suffix.lower() == ".mp4"]
if not videos:
    print(f"[WARN] {BACKUP} 里没有 mp4 文件")
    sys.exit(0)

total_before = 0
total_after = 0

for src_backup in videos:
    f = SRC / src_backup.name  # 输出路径

    size_before = src_backup.stat().st_size
    total_before += size_before

    opts = SETTINGS.get(src_backup.name, DEFAULT_OPTS)

    print(f"[ENCODE] {src_backup.name}  ({size_before/1024/1024:.2f} MB)")
    print(f"         参数: width={opts['width']}, crf={opts['crf']}, preset={opts['preset']}")

    # 输出到临时文件，编码成功后再覆盖
    tmp_out = SRC / f"_tmp_{src_backup.name}"

    cmd = [
        FFMPEG, "-y", "-i", str(src_backup),
        "-vf", f"scale={opts['width']}:-2",
        "-c:v", "libx264",
        "-crf", str(opts["crf"]),
        "-preset", opts["preset"],
        "-an",                          # 移除音轨（这些都是无声背景视频）
        "-movflags", "+faststart",      # 把元数据放文件头部，便于流式播放
        "-pix_fmt", "yuv420p",          # 最大兼容性
        str(tmp_out),
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        # 用编码后的文件覆盖原文件
        shutil.move(str(tmp_out), str(f))

        size_after = f.stat().st_size
        total_after += size_after
        ratio = (1 - size_after / size_before) * 100
        print(f"         → {size_after/1024/1024:.2f} MB  (减少 {ratio:.0f}%)\n")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 编码 {f.name} 失败:")
        print(e.stderr.decode("utf-8", errors="ignore")[-500:])
        if tmp_out.exists():
            tmp_out.unlink()
        total_after += size_before

print("=" * 56)
print(f"总计: {total_before/1024/1024:.2f} MB  →  {total_after/1024/1024:.2f} MB  "
      f"(-{(1 - total_after/total_before)*100:.0f}%)")
print(f"\n[OK] 完成！原视频已备份到 {BACKUP.name}/")
