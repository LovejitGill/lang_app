"""Pinned optional Intel-macOS Java/LanguageTool downloads; no system changes."""

import hashlib
import platform
import subprocess
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / ".tools" / "benchmark"
ARTIFACTS = [
    (
        "java.tar.gz",
        "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/OpenJDK21U-jre_x64_mac_hotspot_21.0.12.1_1.tar.gz",
        "6717ec641fd9ce0bb209ca083ee23b42202ac68cb6fcc5753496e0e4a0f41989",
    ),
    (
        "lt.zip",
        "https://languagetool.org/download/LanguageTool-6.6.zip",
        "53600506b399bb5ffe1e4c8dec794fd378212f14aaf38ccef9b6f89314d11631",
    ),
]


def main():
    if platform.system() != "Darwin" or platform.machine() != "x86_64":
        raise SystemExit("This optional installer is pinned for Intel macOS only.")
    ROOT.mkdir(parents=True, exist_ok=True)
    for name, url, expected in ARTIFACTS:
        archive = ROOT / name
        if not archive.exists():
            subprocess.run(
                ["curl", "-fLsS", "--retry", "2", url, "-o", str(archive)], check=True
            )
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
            raise SystemExit(f"Checksum mismatch: {archive}; remove it and retry.")
        if name.endswith(".gz"):
            with tarfile.open(archive) as bundle:
                bundle.extractall(ROOT, filter="data")
        else:
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(ROOT)
        print(f"{name}: SHA-256 verified")
    print("Optional benchmark runtime ready; no system Java installation changed.")


if __name__ == "__main__":
    main()
