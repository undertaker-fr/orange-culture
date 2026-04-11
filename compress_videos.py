"""
橙子文化网站 - 视频批量压缩脚本
用法：python compress_videos.py
会自动把 videos/ 里的 mp4 重新编码到合理大小，原图备份到 videos-original/
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
#   29-35 低质量（仅追求小文件）
SETTINGS = {
    "hero.mp4":    {"width": 1280, "crf": 30, "preset": "medium"},
    "feature.mp4": {"width": 1280, "crf": 27, "preset": "medium"},
}
# ====================

ROOT = Path(__file__).parent
SRC = ROOT / "videos"
BACKUP = ROOT / "videos-original"

if not SRC.exists():
    print(f"[ERROR] 找不到 {SRC}")
    sys.exit(1)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
print(f"[INFO] 使用 ffmpeg: {FFMPEG}\n")

# 1. 备份原视频
if not BACKUP.exists():
    print(f"[BACKUP] 首次运行，正在备份原视频到 {BACKUP.name}/ ...")
    shutil.copytree(SRC, BACKUP)
    print(f"[BACKUP] 备份完成\n")
else:
    print(f"[BACKUP] 已存在 {BACKUP.name}/，跳过备份\n")

# 2. 遍历压缩
videos = [f for f in SRC.iterdir() if f.suffix.lower() == ".mp4"]
if not videos:
    print("[WARN] videos/ 里没有 mp4 文件")
    sys.exit(0)

total_before = 0
total_after = 0

for f in videos:
    src_backup = BACKUP / f.name
    if not src_backup.exists():
        print(f"[SKIP] {f.name} 没有备份，跳过")
        continue

    size_before = src_backup.stat().st_size
    total_before += size_before

    opts = SETTINGS.get(f.name, {"width": 1280, "crf": 28, "preset": "medium"})

    print(f"[ENCODE] {f.name}  ({size_before/1024/1024:.2f} MB)")
    print(f"         参数: width={opts['width']}, crf={opts['crf']}, preset={opts['preset']}")

    # 输出到临时文件，编码成功后再覆盖
    tmp_out = SRC / f"_tmp_{f.name}"

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
