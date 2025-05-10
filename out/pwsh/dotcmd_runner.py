#!/usr/bin/env python3
import sys
import commands

if len(sys.argv) < 2:
    print("Usage: dotcmd_runner.py <function_name> [args...]")
    sys.exit(1)

func_name = sys.argv[1]
args = sys.argv[2:]

if hasattr(commands, func_name):
    try:
        func = getattr(commands, func_name)
        result = func(*args)
        if result is not None:
            print(result)
    except Exception as e:
        print(f"[dotcmd_runner] Error running '{func_name}': {e}", file=sys.stderr)
        sys.exit(1)
else:
    print(f"[dotcmd_runner] Unknown command: '{func_name}'", file=sys.stderr)
    sys.exit(1)
