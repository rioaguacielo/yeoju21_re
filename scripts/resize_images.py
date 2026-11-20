#!/usr/bin/env python3
"""uploads/ 안의 큰 이미지를 자동으로 줄입니다.

- 긴 변이 1600px 보다 크거나 파일이 700KB 보다 크면 긴 변 1600px 로 줄이고 다시 저장합니다.
- 휴대폰 사진의 회전 정보(EXIF)를 반영해 바로 세운 뒤, 위치 정보 등 메타데이터는 지웁니다.
- 줄인 파일은 같은 이름으로 덮어씁니다(본문 링크가 그대로 유지됨).

GitHub Actions(.github/workflows/deploy.yml)가 사이트를 만들기 전에 실행합니다.
"""
import sys
from pathlib import Path

from PIL import Image, ImageOps

MAX_SIDE = 1600
MAX_BYTES = 700 * 1024
JPEG_QUALITY = 82
EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def shrink(path: Path) -> bool:
    size = path.stat().st_size
    with Image.open(path) as im:
        w, h = im.size
        if max(w, h) <= MAX_SIDE and size <= MAX_BYTES:
            return False
        im = ImageOps.exif_transpose(im)
        im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
        ext = path.suffix.lower()
        if ext in (".jpg", ".jpeg"):
            im.convert("RGB").save(path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        elif ext == ".png":
            if im.mode in ("RGBA", "LA", "P") and "transparency" in im.info or im.mode in ("RGBA", "LA"):
                im.save(path, "PNG", optimize=True)
            else:
                # 사진을 PNG로 올린 경우에도 이름은 그대로 두고 용량만 줄입니다.
                im.convert("RGB").quantize(colors=256).save(path, "PNG", optimize=True)
        else:
            im.save(path, "WEBP", quality=JPEG_QUALITY)
    print(f"resized {path} ({size // 1024}KB -> {path.stat().st_size // 1024}KB, {w}x{h} -> max {MAX_SIDE})")
    return True


def main(root="uploads"):
    changed = 0
    for p in sorted(Path(root).rglob("*")):
        if p.is_file() and p.suffix.lower() in EXTS:
            try:
                changed += shrink(p)
            except Exception as e:  # 깨진 이미지는 건너뜁니다
                print(f"skip {p}: {e}")
    print(f"{changed} image(s) resized")


if __name__ == "__main__":
    main(*sys.argv[1:])
