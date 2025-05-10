# setup.py — generate & install the unified dotfiles

#!/usr/bin/env python3
import argparse, subprocess, os, shutil

parser = argparse.ArgumentParser(description="Generate & install unified dotfiles")
parser.add_argument("--shell", "-s", required=True, choices=["zsh", "pwsh"])
parser.add_argument("--target", "-t", required=True, help="Directory to install into")
parser.add_argument("--mode", "-m", choices=["copy", "symlink"], default="copy")
args = parser.parse_args()

root = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(root, "out", args.shell)
os.makedirs(out_dir, exist_ok=True)

# Generate the unified file
print(f"Generating unified.{args.shell}...")
subprocess.run(["python", os.path.join(root, "gen_dotfiles.py"), args.shell], check=True)

# Install unified.{ps1,zsh}
fname = f"unified.{ 'ps1' if args.shell=='pwsh' else 'zsh' }"
src = os.path.join(out_dir, fname)
dst = os.path.join(os.path.abspath(args.target), fname)
os.makedirs(os.path.abspath(args.target), exist_ok=True)

def install(src_path, dst_path):
    if args.mode == "copy":
        shutil.copy2(src_path, dst_path)
    else:
        if os.path.exists(dst_path):
            os.remove(dst_path)
        os.symlink(src_path, dst_path)
    print(f" → {'Copied' if args.mode=='copy' else 'Linked'} {os.path.basename(dst_path)}")

print(f"Installing {fname} to {args.target} ({args.mode})")
install(src, dst)

# Also install dotcmd_runner.py for pwsh
if args.shell == "pwsh":
    runner_src = os.path.join(out_dir, "dotcmd_runner.py")
    runner_dst = os.path.join(args.target, "dotcmd_runner.py")
    if os.path.exists(runner_src):
        install(runner_src, runner_dst)
    else:
        print("WARNING: dotcmd_runner.py missing — dotcmd will fail")

# Show how to hook it up
hook = f". '{dst}'" if args.shell=="pwsh" else f"source '{dst}'"
print(f"\nAdd this to your profile:\n  {hook}")
