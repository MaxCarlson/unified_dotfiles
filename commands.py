#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import argparse
import re
import yaml

# ─── Load the YAML definitions ────────────────────────────────────────────────
DEFS_PATH = os.path.expanduser("~/dotfiles/definitions/commands.yaml")
with open(DEFS_PATH, "r", encoding="utf-8") as f:
    defs = yaml.safe_load(f)

alias_help = {a["name"]: a["help"] for a in defs.get("aliases", [])}
function_help = {fn["name"]: fn["help"] for fn in defs.get("functions", [])}


# ─── Metadata‐driven “help” functions ────────────────────────────────────────
def ag(pattern=None):
    """Show all aliases, optionally filtering by name or helpstring."""
    for name, helpstr in alias_help.items():
        if pattern is None or pattern in name or pattern in helpstr:
            print(f"{name}: {helpstr}")
    return 0

def ahelp(pattern=None):
    """Search alias descriptions by keyword."""
    return ag(pattern)

def fhelp(pattern=None):
    """Search function descriptions by keyword."""
    for name, helpstr in function_help.items():
        if pattern is None or pattern in name or pattern in helpstr:
            print(f"{name}: {helpstr}")
    return 0

def helpall(pattern=None):
    """Search both function and alias descriptions by keyword."""
    fhelp(pattern)
    ag(pattern)
    return 0

def fg(pattern):
    """Search functions by name or description, highlighting matches in red."""
    RED = "\033[31m"; RESET = "\033[0m"
    for name, helpstr in function_help.items():
        if pattern in name or pattern in helpstr:
            n = name.replace(pattern, f"{RED}{pattern}{RESET}")
            h = helpstr.replace(pattern, f"{RED}{pattern}{RESET}")
            print(f"{n}: {h}")
    return 0

def functionsl():
    """Lists all registered functions and their descriptions."""
    for name, desc in function_help.items():
        print(f"{name}: {desc}")
    return 0

# ─── Directory & File Handling ────────────────────────────────────────────────
def retrycmd(args):
    """Runs a command repeatedly until it succeeds."""
    if not args:
        print("Usage: dotcmd retrycmd <command> [args...]", file=sys.stderr)
        return 1
    while True:
        ret = subprocess.call(args)
        if ret == 0:
            return 0
        print(f"Command {args!r} failed (exit {ret}), retrying in 1s…", file=sys.stderr)
        time.sleep(1)

def mkcd(name, path='.'):
    """Creates a directory if it doesn't exist and prints the full path."""
    if not name:
        print("Usage: dotcmd mkcd <dirname> [path]", file=sys.stderr)
        return 1
    full = os.path.join(path, name)
    try:
        os.makedirs(full, exist_ok=True)
    except Exception as e:
        print(f"Error creating directory {full!r}: {e}", file=sys.stderr)
        return 2
    print(full)
    return 0

def create_if_missing(path):
    """Creates a file if it doesn't exist."""
    if not path:
        print("Usage: dotcmd create_if_missing <file_path>", file=sys.stderr)
        return 1
    if not os.path.exists(path):
        try:
            open(path, 'a').close()
            print(f"Created file: {path}")
        except Exception as e:
            print(f"Error creating file {path!r}: {e}", file=sys.stderr)
            return 2
    else:
        print(f"File already exists: {path}")
    return 0

def cdobs():
    """Prints the Obsidian directory path from the OBSIDIAN env var."""
    path = os.environ.get("OBSIDIAN")
    if not path:
        print("Error: OBSIDIAN environment variable is not set", file=sys.stderr)
        return 1
    print(path)
    return 0

def get_file_size(path):
    """Prints the size of a file in bytes."""
    if not path:
        print("Usage: dotcmd get_file_size <file_path>", file=sys.stderr)
        return 1
    try:
        size = os.stat(path).st_size
        print(size)
        return 0
    except Exception as e:
        print(f"Error reading file size {path!r}: {e}", file=sys.stderr)
        return 2


# ─── Help‐grep Utility ───────────────────────────────────────────────────────
def hrg(prog, pattern):
    """Searches a program's help output for a pattern."""
    if not prog or not pattern:
        print("Usage: dotcmd hrg <program> <pattern>", file=sys.stderr)
        return 1
    help_out = ""
    for flag in ("--help", "-h", "-?", "/?"):
        try:
            help_out = subprocess.check_output([prog, flag], stderr=subprocess.STDOUT, text=True)
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    if not help_out:
        print(f"Error: Unable to retrieve help for '{prog}'", file=sys.stderr)
        return 2
    for line in help_out.splitlines():
        if re.search(pattern, line):
            print(line)
    return 0


# ─── Neovim “mkvi” ───────────────────────────────────────────────────────────
def mkvi(folder, filename=None):
    """Creates a directory and opens a file using Neovim."""
    if not folder:
        print("Usage: dotcmd mkvi <folder> [filename]", file=sys.stderr)
        return 1
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        print(f"Error creating directory {folder!r}: {e}", file=sys.stderr)
        return 2
    target = os.path.join(folder, filename) if filename else folder
    return subprocess.call(["nvim", target])


# ─── Tree & Listing Wrappers ────────────────────────────────────────────────
def lt(depth):
    """Lists files in tree format up to the specified depth."""
    if not depth:
        print("Usage: dotcmd lt <depth>", file=sys.stderr)
        return 1
    return subprocess.call(["eza","-lah","--icons","--classify","--tree",f"--level={depth}","--git"])

def ltf(depth, output_file="./ltf-output.txt"):
    """Runs lt and writes output to a file."""
    if not depth:
        print("Usage: dotcmd ltf <depth> [output_file]", file=sys.stderr)
        return 1
    out_dir = os.path.dirname(output_file)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    proc = subprocess.run(
        ["eza","-lah","--icons","--classify","--tree",f"--level={depth}","--git"],
        capture_output=True, text=True
    )
    if proc.returncode != 0:
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        return proc.returncode
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(proc.stdout)
    print(f"ltf output (depth {depth}) written to: {os.path.abspath(output_file)}")
    return 0


# ─── fd / eza Pipelines ─────────────────────────────────────────────────────
def fdtl(pattern):
    """Finds files by name, sorted by mod-time, then runs eza -lt."""
    raw = subprocess.check_output(["fd",pattern,"-t","f","--print0"], stderr=subprocess.DEVNULL)
    files = [f for f in raw.split(b"\0") if f]
    files.sort(key=lambda f: os.stat(f).st_mtime, reverse=True)
    for f in files:
        subprocess.call(["eza","-lt",f.decode()])
    return 0

def fdta(pattern):
    """Finds files by name, sorted by mod-time."""
    raw = subprocess.check_output(["fd",pattern,"-t","f","--print0"], stderr=subprocess.DEVNULL)
    files = [f for f in raw.split(b"\0") if f]
    files.sort(key=lambda f: os.stat(f).st_mtime, reverse=True)
    for f in files:
        print(f.decode())
    return 0


# ─── ripgrep Variants ────────────────────────────────────────────────────────
def rgcmd(args):
    """Runs ripgrep with default options."""
    return subprocess.call(["rg","--max-columns=200","--max-columns-preview"] + args)

def rgta(pattern, path="."):
    """Files-with-matches, sorted by mod-time."""
    raw = subprocess.check_output(["rg","--files-with-matches",pattern,path,"--null"], stderr=subprocess.DEVNULL)
    files = [f for f in raw.split(b"\0") if f]
    files.sort(key=lambda f: os.stat(f).st_mtime, reverse=True)
    for f in files:
        print(f.decode())
    return 0

def rgtf(pattern, path="."):
    """Matching lines in files-with-matches, sorted by mod-time."""
    raw = subprocess.check_output(["rg","--files-with-matches",pattern,path,"--null"], stderr=subprocess.DEVNULL)
    files = [f for f in raw.split(b"\0") if f]
    files.sort(key=lambda f: os.stat(f).st_mtime, reverse=True)
    for f in files:
        subprocess.call(["rg",pattern,f.decode()])
    return 0

def rgfn(pattern, path="."):
    """Same as rgtf but only filenames printed."""
    raw = subprocess.check_output(["rg","--files-with-matches",pattern,path,"--null"], stderr=subprocess.DEVNULL)
    files = [f for f in raw.split(b"\0") if f]
    files.sort(key=lambda f: os.stat(f).st_mtime, reverse=True)
    for f in files:
        print(f.decode())
    return 0

def rgtc(pattern, path="."):
    """Files matching by content OR filename, sorted by mod-time."""
    raw1 = subprocess.check_output(["rg","--files-with-matches",pattern,path,"--null"], stderr=subprocess.DEVNULL)
    raw2 = subprocess.check_output(["rg","--files","-g",pattern,path,"--null"], stderr=subprocess.DEVNULL)
    files = set(raw1.split(b"\0") + raw2.split(b"\0"))
    files.discard(b"")
    files = sorted(files, key=lambda f: os.stat(f).st_mtime, reverse=True)
    for f in files:
        print(f.decode())
    return 0

def rgtm(pattern, path="."):
    """Same as rgtc but sorted by creation time."""
    raw1 = subprocess.check_output(["rg","--files-with-matches",pattern,path,"--null"], stderr=subprocess.DEVNULL)
    raw2 = subprocess.check_output(["rg","--files","-g",pattern,path,"--null"], stderr=subprocess.DEVNULL)
    files = set(raw1.split(b"\0") + raw2.split(b"\0"))
    files.discard(b"")
    files = sorted(files, key=lambda f: os.stat(f).st_ctime, reverse=True)
    for f in files:
        print(f.decode())
    return 0


# ─── rgmax / rgmaxn ─────────────────────────────────────────────────────────
def rgmax(phrase, num=1, path="."):
    """Returns top N files with the most matches for a phrase."""
    raw = subprocess.check_output(["rg","-c","--fixed-strings",phrase,path], stderr=subprocess.DEVNULL, text=True)
    counts = []
    for line in raw.splitlines():
        if ":" not in line: continue
        file, cnt = line.rsplit(":",1)
        try:
            counts.append((int(cnt), file))
        except ValueError:
            continue
    for cnt, file in sorted(counts, reverse=True)[:num]:
        print(f"{file}:{cnt}")
    return 0

def rgmaxn(phrase, path="."):
    """Alias for rgmax with default num_files=100."""
    return rgmax(phrase, num=100, path=path)


# ─── Rsync wrappers ─────────────────────────────────────────────────────────
def rp(opts):
    """Copy files via rsync under the hood with in-place progress."""
    if not opts:
        print("Usage: dotcmd rp [rsync-options] SRC [DEST]", file=sys.stderr)
        return 1
    return subprocess.call(["rsync","-a","--info=progress2","--stats","--human-readable"] + opts)

def rpv(opts):
    """Verbose copy (rsync under the hood, very verbose)."""
    return rp(["-vvv"] + opts)

def rpd(opts):
    """Dry-run copy (rsync under the hood)."""
    return rp(["--dry-run"] + opts)

def rpi(opts):
    """Copy ignoring existing files (rsync under the hood)."""
    return rp(["--ignore-existing"] + opts)

def rpdel(opts):
    """Copy then delete source files (rsync under the hood)."""
    return rp(["--remove-source-files"] + opts)

# ─── Main dispatch ─────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(prog="dotcmd")
    subs = p.add_subparsers(dest="cmd", required=True)

    # help utilities
    subs.add_parser("ag").add_argument("pattern", nargs="?", default=None)
    subs.add_parser("ahelp").add_argument("pattern", nargs="?", default=None)
    subs.add_parser("fhelp").add_argument("pattern", nargs="?", default=None)
    subs.add_parser("helpall").add_argument("pattern", nargs="?", default=None)
    subs.add_parser("fg").add_argument("pattern", help="Search term")

    # List all functions:
    subs.add_parser("functionsl")

    # directory/file
    subs.add_parser("retrycmd").add_argument("cmd", nargs=argparse.REMAINDER)
    p2 = subs.add_parser("mkcd"); p2.add_argument("name"); p2.add_argument("path", nargs="?", default=".")
    subs.add_parser("create_if_missing").add_argument("path")
    subs.add_parser("cdobs")
    subs.add_parser("get_file_size").add_argument("path")

    # help-grep
    p3 = subs.add_parser("hrg"); p3.add_argument("prog"); p3.add_argument("pattern")

    # editor
    p4 = subs.add_parser("mkvi"); p4.add_argument("folder"); p4.add_argument("filename", nargs="?")

    # trees
    p5 = subs.add_parser("lt"); p5.add_argument("depth")
    p6 = subs.add_parser("ltf"); p6.add_argument("depth"); p6.add_argument("output_file", nargs="?", default="./ltf-output.txt")

    # fd/eza
    subs.add_parser("fdtl").add_argument("pattern")
    subs.add_parser("fdta").add_argument("pattern")

    # ripgrep
    pr = subs.add_parser("rg"); pr.add_argument("args", nargs=argparse.REMAINDER)
    p7 = subs.add_parser("rgta"); p7.add_argument("pattern"); p7.add_argument("--path", default=".")
    p8 = subs.add_parser("rgtf"); p8.add_argument("pattern"); p8.add_argument("--path", default=".")
    subs.add_parser("rgfn").add_argument("pattern"); subs.add_parser("rgtc").add_argument("pattern")
    subs.add_parser("rgtm").add_argument("pattern")
    p9 = subs.add_parser("rgmax"); p9.add_argument("phrase"); p9.add_argument("--num", type=int, default=1); p9.add_argument("--path", default=".")
    p10 = subs.add_parser("rgmaxn"); p10.add_argument("phrase"); p10.add_argument("--path", default=".")

    # rsync
    subs.add_parser("rp").add_argument("options", nargs=argparse.REMAINDER)
    subs.add_parser("rpv").add_argument("options", nargs=argparse.REMAINDER)
    subs.add_parser("rpd").add_argument("options", nargs=argparse.REMAINDER)
    subs.add_parser("rpi").add_argument("options", nargs=argparse.REMAINDER)
    subs.add_parser("rpdel").add_argument("options", nargs=argparse.REMAINDER)

    args = p.parse_args()
    cmd = args.cmd

    # help
    if cmd == "ag":        sys.exit(ag(args.pattern))
    if cmd == "ahelp":     sys.exit(ahelp(args.pattern))
    if cmd == "fhelp":     sys.exit(fhelp(args.pattern))
    if cmd == "helpall":   sys.exit(helpall(args.pattern))
    if cmd == "fg":        sys.exit(fg(args.pattern))
    if cmd == "functionsl":sys.exit(functionsl())

    # directory/file
    if cmd == "retrycmd":        sys.exit(retrycmd(args.cmd))
    if cmd == "mkcd":            sys.exit(mkcd(args.name, args.path))
    if cmd == "create_if_missing": sys.exit(create_if_missing(args.path))
    if cmd == "cdobs":           sys.exit(cdobs())
    if cmd == "get_file_size":   sys.exit(get_file_size(args.path))

    # help-grep
    if cmd == "hrg":             sys.exit(hrg(args.prog, args.pattern))

    # editor
    if cmd == "mkvi":            sys.exit(mkvi(args.folder, args.filename))

    # trees
    if cmd == "lt":              sys.exit(lt(args.depth))
    if cmd == "ltf":             sys.exit(ltf(args.depth, args.output_file))

    # fd/eza
    if cmd == "fdtl":            sys.exit(fdtl(args.pattern))
    if cmd == "fdta":            sys.exit(fdta(args.pattern))

    # ripgrep
    if cmd == "rg":              sys.exit(rgcmd(args.args))
    if cmd == "rgta":            sys.exit(rgta(args.pattern, args.path))
    if cmd == "rgtf":            sys.exit(rgtf(args.pattern, args.path))
    if cmd == "rgfn":            sys.exit(rgfn(args.pattern, args.path))
    if cmd == "rgtc":            sys.exit(rgtc(args.pattern, args.path))
    if cmd == "rgtm":            sys.exit(rgtm(args.pattern, args.path))
    if cmd == "rgmax":           sys.exit(rgmax(args.phrase, args.num, args.path))
    if cmd == "rgmaxn":          sys.exit(rgmaxn(args.phrase, args.path))

    # rsync
    if cmd == "rp":              sys.exit(rp(args.options))
    if cmd == "rpv":             sys.exit(rpv(args.options))
    if cmd == "rpd":             sys.exit(rpd(args.options))
    if cmd == "rpi":             sys.exit(rpi(args.options))
    if cmd == "rpdel":           sys.exit(rpdel(args.options))

    p.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()

