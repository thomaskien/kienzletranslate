"""Run only after explicit CC BY-NC 4.0 acceptance by the installer."""
import sys
from huggingface_hub import snapshot_download

MODEL = "facebook/seamless-m4t-v2-large"
REVISION = "5f8cc790b19fc3f67a61c105133b20b34e3dcb76"

if __name__ == "__main__":
    snapshot_download(MODEL, revision=REVISION, local_dir=sys.argv[1],
                      allow_patterns=["*.json", "*.safetensors", "*.model", "README.md"],
                      max_workers=2)
