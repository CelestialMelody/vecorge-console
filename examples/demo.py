"""体验状态行、进度、失败详情、报告和中断。"""

import argparse
from functools import partial
from pathlib import Path
import time
import tomllib

from vecorge_console import Cell, Config, Console, Report, Table


ROOT = Path(__file__).resolve().parents[1]


def show_status(console):
    report = ROOT / "examples/output/validation/long-task-name/verification-report.txt"
    console.status("ok", "build", "example")
    console.status("info", "report", console.path(report))
    console.detail(f"Example report path: {report}\n")


def show_progress(console):
    with console.progress("Preparing tasks") as progress:
        time.sleep(0.8)
        console.write("Reading inputs")
        time.sleep(0.6)
        console.write(" ready\n")
        progress.update(total=3, label="Checking samples")
        time.sleep(0.6)
        for done in range(1, 4):
            progress.update(done=done)
            time.sleep(0.35)
    console.status("ok", "test", "3 samples")


def show_failure(console, *, code):
    diagnostics = "\n".join(f"diagnostic {number:02d}" for number in range(1, 46))
    console.status("fail", "test", "example", detail=f"exit {code}", error=True)
    console.failure(
        command=f"sh -c 'exit {code}'",
        output=diagnostics,
        hint="Check the input file",
        error=True,
    )


def show_report(console):
    summary = Table(
        "Summary", ("method", "elapsed (ms)", "speedup"),
        [
            ("baseline", "10.0", "1.00x"),
            ("candidate", "8.0", Cell("1.25x", "positive")),
        ],
        right=(1, 2),
    )
    console.report(Report("Console example", [("samples", 3)], [summary], ("Synthetic data",)))


def wait_for_interrupt(console):
    with console.progress("Press Ctrl+C to interrupt", delay_seconds=0):
        time.sleep(30)


def load_exit_codes(path):
    codes = {"failure": 7, "interrupted": 130}
    if path is None:
        return codes

    with path.open("rb") as stream:
        document = tomllib.load(stream)
    configured = document.get("exit_codes")
    if set(document) != {"exit_codes"} or not isinstance(configured, dict):
        raise ValueError("expected an [exit_codes] table")
    for name, value in configured.items():
        if name not in codes:
            raise ValueError(f"unknown exit code field: exit_codes.{name}")
        if type(value) is not int or not 1 <= value <= 255:
            raise ValueError(f"exit_codes.{name} must be an integer from 1 to 255")
        codes[name] = value
    return codes


def main():
    demos = {
        "status": show_status,
        "progress": show_progress,
        "failure": show_failure,
        "report": show_report,
        "interrupt": wait_for_interrupt,
    }
    parser = argparse.ArgumentParser(description="Run the vecorge-console examples.")
    parser.add_argument("case", choices=("all", *demos), nargs="?", default="all")
    parser.add_argument(
        "--config", type=Path, default=Path(__file__).with_name("workbench.toml"),
        help="display configuration to load",
    )
    parser.add_argument("--exit-codes", type=Path, help="demo exit-code configuration to load")
    args = parser.parse_args()
    try:
        console = Console(Config.load(args.config), root=ROOT)
        exit_codes = load_exit_codes(args.exit_codes)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    demos["failure"] = partial(show_failure, code=exit_codes["failure"])
    cases = ("status", "progress", "failure", "report") if args.case == "all" else (args.case,)
    try:
        for case in cases:
            demos[case](console)
    except KeyboardInterrupt:
        console.status("warn", "demo", "example", detail="interrupted", error=True)
        return exit_codes["interrupted"]
    return exit_codes["failure"] if args.case == "failure" else 0


if __name__ == "__main__":
    raise SystemExit(main())
