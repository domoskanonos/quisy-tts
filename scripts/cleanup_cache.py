#!/usr/bin/env python3
"""Cleanup script to remove old cache files.

Usage:
    python scripts/cleanup_cache.py [--days N] [--dir path]

Defaults: 30 days, cache directory from settings/ProjectConfig
"""

import argparse
from pathlib import Path
import sys

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from services.cache_service import FileCacheService
from config import ProjectConfig


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=30, help="Remove files older than DAYS")
    p.add_argument("--dir", type=str, default=None, help="Optional cache directory override")
    return p.parse_args()


def main():
    args = parse_args()
    settings = ProjectConfig.get_settings()
    cache_dir = Path(args.dir) if args.dir else settings.AUDIO_DIR
    cache = FileCacheService(cache_dir=cache_dir)
    removed = cache.cleanup_old_files(max_age_hours=args.days * 24)
    print(f"Removed {removed} files from {cache_dir}")


if __name__ == "__main__":
    main()
