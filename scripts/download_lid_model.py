#!/usr/bin/env python3
"""Download the pinned MIT-licensed CPU language detector."""
import sys
from pathlib import Path

from huggingface_hub import snapshot_download


MODEL = 'Systran/faster-whisper-base'
REVISION = 'ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66'
FILES = ['config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt',
         'preprocessor_config.json']
REQUIRED = FILES[:4]


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: download_lid_model.py TARGET_DIRECTORY')
    target = snapshot_download(MODEL, revision=REVISION, local_dir=sys.argv[1],
                      allow_patterns=FILES, max_workers=2)
    missing = [name for name in REQUIRED if not (Path(target)/name).is_file()]
    if missing:
        raise RuntimeError('incomplete LID model download: ' + ', '.join(missing))
