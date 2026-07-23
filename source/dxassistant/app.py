from __future__ import annotations

import argparse
import shutil
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from .config import load_config
from .dashboard import Dashboard


def default_config_path() -> Path:
    """Use an editable config beside the executable in a frozen build."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "config.json"
    return Path(__file__).resolve().parent.parent / "config.json"


def default_template_path(config_path: Path | None = None) -> Path:
    """Locate the credential-free template beside the requested live config."""

    path = config_path or default_config_path()
    return path.with_name("config.template.json")


def ensure_config_file(path: Path, template_path: Path | None = None) -> None:
    """Create an operator-owned live config without ever modifying the template."""

    if path.exists():
        return
    template = template_path or default_template_path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(template, path)
    except OSError as error:
        raise ValueError(
            f"Could not create configuration file {path} from {template}: {error}"
        ) from error


def main(argv=None):
    parser = argparse.ArgumentParser(description="Receive-only WSJT-X and OmniRig DX search dashboard")
    parser.add_argument("--config", type=Path, default=default_config_path())
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    arguments = parser.parse_args(argv)
    try:
        ensure_config_file(arguments.config)
        config = load_config(arguments.config)
    except ValueError as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("DX Assistant configuration error", str(error))
        root.destroy()
        return 2
    if arguments.smoke_test:
        from .omnirig import OmniRigClient

        return 0 if OmniRigClient().bridge_path.is_file() else 3
    root = tk.Tk()
    Dashboard(root, config)
    root.mainloop()
    return 0
