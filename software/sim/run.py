#!/usr/bin/env python3
"""Run monorepo simulation tools without depending on the caller's directory."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SIM = ROOT/'software/sim/mujoco'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entry', choices=['baseline', 'verify-migration', 'test', 'script'])
    args, rest = parser.parse_known_args()
    cwd = ROOT
    if args.entry == 'script':
        if not rest or Path(rest[0]).name != rest[0] or not (SIM/rest[0]).is_file():
            parser.error('script requires the basename of an existing MuJoCo Python script')
        command = [sys.executable, *rest]
        cwd = SIM
    elif args.entry == 'test':
        command = [sys.executable, '-m', 'unittest', *(rest or ['tests.test_teleop_yaw', 'tests.test_teleop_r9']), '-v']
        cwd = SIM
    else:
        name = {'baseline':'run_baseline.py', 'verify-migration':'verify_migration.py'}[args.entry]
        command = [sys.executable, str(ROOT/'software/sim/integration'/name), *rest]
    raise SystemExit(subprocess.call(command, cwd=cwd))


if __name__ == '__main__':main()
