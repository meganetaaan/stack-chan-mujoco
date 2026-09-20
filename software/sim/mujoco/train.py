#!/usr/bin/env python3
"""Run from WSL/Linux/Windows with a main guard for spawn workers."""
import os
# Set BEFORE importing NumPy / PyTorch in the parent AND spawned workers.
for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "1"
if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    from stackchan_rl.training import main
    raise SystemExit(main())
