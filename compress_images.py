"""
橙子文化网站 - 图片批量压缩脚本
用法：python compress_images.py

工作流程：
  - images-original/  ← 原图（你只需要维护这里）
  - images/           ← 压缩后的输出（脚本自动生成，会被网页引用）

每次想替换/新增图片，就把图片放到 images-original/ 里，重跑本脚本即可。
"""
from PIL import Image
from pathlib import Path
import shutil
import sys

# ===== 可调参数 =====
MAX_WIDTH = 1600      # 最大宽度（够高清屏用了）
MAX_HEIGHT = 1600     # 最大高度
JPEG_QUALITY = 82     # JPEG 质量：80-85 是肉眼看不出损失的甜蜜点
# ====================

ROOT = Path(__file__).parent
SRC = ROOT / "images"
BACKUP = ROOT / "images-original"

exts = {".jpg", ".jpeg", ".png", ".webp"}

# 1. 如果没有 images-original/，首次跑时把 images/ 备份过去
if not BACKUP.exists():
    if not SRC.exists():
        print(f"[ERROR] 找不到 {SRC} 也找不到 {BACKUP}")
        sys.exit(1)
    print(f"[BACKUP] 首次运行，正在备份 images/ → {BACKUP.name}/ ...")
    shutil.copytree(SRC, BACKUP)
    print(f"[BACKUP] 备份完成\n")

# 2. 始终以 images-original/ 为源，复制到 images/，再压缩
SRC.mkdir(exist_ok=True)
src_files = [f for f in BACKUP.iterdir() if f.suffix.lower() in exts]

if not src_files:
    print(f"[WARN] {BACKUP} 里没有可处理的图片")
    sys.exit(0)

print(f"[SYNC] 从 {BACKUP.name}/ 复制 {len(src_files)} 张原图到 {SRC.name}/ ...")
for sf in src_files:
    shutil.copy2(sf, SRC / sf.name)
print(f"[SYNC] 复制完成\n")

files = [f for f in SRC.iterdir() if f.suffix.lower() in exts]

if not files:
    print(f"[WARN] {SRC} 里没有可压缩的图片")
    sys.exit(0)

total_before = 0
total_after = 0

print(f"{'文件名':<20} {'原大小':>10} {'→':^4} {'新大小':>10} {'减少':>8}")
print("-" * 60)

for f in files:
    size_before = f.stat().st_size
    total_before += size_before

    try:
        img = Image.open(f)

        # 转成 RGB（去掉 alpha 通道，JPEG 不支持透明）
        if img.mode in ("RGBA", "P", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # 按最长边等比缩放
        img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)

        # 保存：progressive=True 让图片边下边显示（体感快很多）
        # optimize=True 额外压缩
        img.save(
            f,
            "JPEG",
            quality=JPEG_QUALITY,
            optimize=True,
            progressive=True,
        )

        size_after = f.stat().st_size
        total_after += size_after
        ratio = (1 - size_after / size_before) * 100

        print(f"{f.name:<20} {size_before/1024:>8.0f} KB  →  {size_after/1024:>8.0f} KB  -{ratio:>5.0f}%")

    except Exception as e:
        print(f"[ERROR] 处理 {f.name} 失败: {e}")
        total_after += size_before  # 失败的算原大小

print("-" * 60)
print(f"{'总计':<20} {total_before/1024/1024:>8.2f} MB  →  {total_after/1024/1024:>8.2f} MB  "
      f"-{(1 - total_after/total_before)*100:>5.0f}%")
print()
print(f"[OK] 完成！原图已备份到 {BACKUP.name}/")
print(f"[OK] 现在可以 git add . && git commit && git push 推送更新了")
