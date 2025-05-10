# setup.py - run from project root to generate and install dotfiles for PowerShell or Zsh

import os
import shutil
import argparse
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description="Generate and install unified dotfiles for PowerShell or Zsh.")
parser.add_argument("--shell", "-s", required=True, choices=["powershell", "zsh"], help="Target shell type")
parser.add_argument("--target", "-t", required=True, help="Path to place the config file (e.g. PowerShell profile or .zshrc.d dir)")
parser.add_argument("--mode", "-m", choices=["copy", "symlink"], default="copy", help="Copy or symlink the file")
args = parser.parse_args()

root_dir = Path(__file__).resolve().parent
out_dir = root_dir / "out" / ("pwsh7" if args.shell == "powershell" else "linux")
out_dir.mkdir(parents=True, exist_ok=True)

# ─── Generate the file ───────────────────────────────────────────────────────
filename = f"unified.{ 'ps1' if args.shell == 'powershell' else 'zsh' }"
gen_script = str(root_dir / "gen_dotfiles.py")
temp_file = root_dir / filename

print(f"Generating {filename}...")
with open(temp_file, "w", encoding="utf-8") as f:
    subprocess.run(["python", gen_script, args.shell], check=True, stdout=f)

# ─── Move generated file into output dir ─────────────────────────────────────
if not temp_file.exists():
    raise FileNotFoundError(f"Expected generated file {temp_file} not found.")
shutil.move(str(temp_file), out_dir / filename)

# ─── Install the generated file ──────────────────────────────────────────────
target_dir = Path(args.target).expanduser().resolve()
target_dir.mkdir(parents=True, exist_ok=True)
dest = target_dir / filename

print(f"Installing {filename} to {target_dir} using mode: {args.mode}\n")

if args.mode == "copy":
    shutil.copy(out_dir / filename, dest)
elif args.mode == "symlink":
    if dest.exists() or dest.is_symlink():
        dest.unlink()
    dest.symlink_to(out_dir / filename)

print(f" → {'Copied' if args.mode == 'copy' else 'Linked'} {filename}")

# ─── Show shell integration instructions ─────────────────────────────────────
if args.shell == "powershell":
    print(f"\nAdd the following line to your PowerShell profile:")
    print(f". '{dest}'  # dot-source unified PS profile")
else:
    print(f"\nAdd the following to your ~/.zshrc:")
    print(f"source '{dest}'  # unified zsh config")
