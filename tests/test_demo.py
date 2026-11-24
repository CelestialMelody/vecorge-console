"""用同一份演示检查终端与重定向行为。"""

import errno
import os
from pathlib import Path
import re
import select
import signal
import struct
import subprocess
import sys
import time
from tempfile import TemporaryDirectory, TemporaryFile
from textwrap import dedent
import unittest


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples/demo.py"
ERASE_LINE = b"\r\x1b[2K"
COLOR = re.compile(rb"\x1b\[[0-9;]*m")


def demo_command(*arguments):
    return [sys.executable, "-B", str(DEMO), *arguments]


def terminal_environment(**overrides):
    env = dict(os.environ, TERM="xterm-256color", PYTHONIOENCODING="utf-8")
    env.pop("NO_COLOR", None)
    env.update(overrides)
    return env


def redirected(*arguments):
    return subprocess.run(
        demo_command(*arguments), cwd=ROOT, env=terminal_environment(),
        capture_output=True, timeout=12,
    )


class RedirectedDemoTests(unittest.TestCase):
    def test_default_demo_saves_readable_plain_text(self):
        result = redirected()
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
        self.assertIn(b"[OK]   build    example\n", result.stdout)
        self.assertIn(b"Context\n", result.stdout)
        self.assertIn(b"Reading inputs ready\n", result.stdout)
        self.assertNotIn(b"Example report path:", result.stdout)
        self.assertIn(b"1.25x", result.stdout)
        self.assertNotIn(b"\x1b", result.stdout + result.stderr)
        self.assertNotIn(b"\r", result.stdout + result.stderr)

    def test_failure_keeps_the_first_and_last_twenty_diagnostics(self):
        result = redirected("failure")
        self.assertEqual(result.returncode, 7, result.stderr.decode("utf-8"))
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"[FAIL] test     example: exit 7", result.stderr)
        self.assertIn(b"... 5 lines omitted ...", result.stderr)
        self.assertIn(b"                hint: Check the input file\n", result.stderr)
        shown = re.findall(rb"(?m)^ {18}diagnostic (\d+)$", result.stderr)
        self.assertEqual([int(line) for line in shown], [*range(1, 21), *range(26, 46)])

    def test_failure_uses_the_selected_exit_code(self):
        example = ROOT / "examples/exit-codes.toml"
        result = redirected("failure", "--exit-codes", str(example))
        self.assertEqual(result.returncode, 17, result.stderr.decode("utf-8"))
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"[FAIL] test     example: exit 17", result.stderr)
        self.assertIn(b"... 5 lines omitted ...", result.stderr)

    def test_invalid_exit_code_reports_the_field(self):
        with TemporaryDirectory() as directory:
            file = Path(directory) / "exit-codes.toml"
            file.write_text("[exit_codes]\nfailure = 0\n", encoding="utf-8")
            result = redirected("failure", "--exit-codes", str(file))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"exit_codes.failure", result.stderr)
        self.assertNotIn(b"[FAIL]", result.stderr)

    def test_explicit_configuration_controls_status_color(self):
        with TemporaryDirectory() as directory:
            file = Path(directory) / "console.toml"
            file.write_text(
                '[display]\ncolor = "always"\n\n[status]\nok = "failure"\n',
                encoding="utf-8",
            )
            result = redirected("status", "--config", str(file))
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
        self.assertIn(b"\x1b[38;2;221;89;85m[OK]\x1b[0m", result.stdout)

    def test_verbose_status_shows_the_full_example_path(self):
        with TemporaryDirectory() as directory:
            config = Path(directory) / "console.toml"
            config.write_text("[display]\nverbose = true\n", encoding="utf-8")
            result = redirected("status", "--config", str(config))
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
        example = Path("examples/output/validation/long-task-name/verification-report.txt")
        self.assertIn(f"[INFO] report   {example}\n".encode(), result.stdout)
        self.assertIn(f"Example report path: {ROOT / example}\n".encode(), result.stdout)

    def test_invalid_configuration_reports_the_field(self):
        with TemporaryDirectory() as directory:
            file = Path(directory) / "console.toml"
            file.write_text('[display]\ncolor = "unknown"\n', encoding="utf-8")
            result = redirected("status", "--config", str(file))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"display.color", result.stderr)


    def test_saved_report_preserves_the_text_layout(self):
        result = redirected("report")
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
        banner = "=" * 78
        expected = "\n".join((
            banner,
            " Console example",
            banner,
            "",
            "Context",
            "  samples  3",
            "",
            "Summary",
            "  method    | elapsed (ms) | speedup",
            "  ----------+--------------+--------",
            "  baseline  |         10.0 |   1.00x",
            "  candidate |          8.0 |   1.25x",
            "",
            "Note",
            "  • Synthetic data",
            "",
        ))
        self.assertEqual(result.stdout.decode("utf-8"), expected)

@unittest.skipUnless(os.name == "posix", "requires a POSIX pseudo-terminal")
class TerminalDemoTests(unittest.TestCase):
    def capture(self, command, *, columns=80, interrupt_on=None, stdout=None, **environment):
        import fcntl
        import pty
        import termios

        master, slave = pty.openpty()
        output = bytearray()
        interrupted = False
        try:
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, columns, 0, 0))
            with subprocess.Popen(
                command, cwd=ROOT, env=terminal_environment(**environment),
                stdout=slave if stdout is None else stdout, stderr=slave,
            ) as process:
                try:
                    os.close(slave)
                    slave = None
                    deadline = time.monotonic() + 10
                    while True:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0 or not select.select([master], [], [], remaining)[0]:
                            self.fail(f"command did not finish in a pseudo-terminal: {command!r}")
                        try:
                            chunk = os.read(master, 65536)
                        except OSError as error:
                            if error.errno == errno.EIO:
                                break
                            raise
                        if not chunk:
                            break
                        output.extend(chunk)
                        if interrupt_on and not interrupted and interrupt_on in output:
                            process.send_signal(signal.SIGINT)
                            interrupted = True
                    code = process.wait(timeout=2)
                finally:
                    if process.poll() is None:
                        process.kill()
        finally:
            if slave is not None:
                os.close(slave)
            os.close(master)
        return code, bytes(output)

    def test_auto_color_respects_no_color(self):
        code, colored = self.capture(demo_command("status"))
        self.assertEqual(code, 0, colored.decode("utf-8"))
        self.assertIn(b"\x1b[38;2;76;155;107m[OK]\x1b[0m", colored)
        code, plain = self.capture(demo_command("status"), NO_COLOR="1")
        self.assertEqual(code, 0, plain.decode("utf-8"))
        self.assertEqual(plain, COLOR.sub(b"", colored))

    def test_report_uses_the_reference_header_style(self):
        code, output = self.capture(demo_command("report"))
        self.assertEqual(code, 0, output.decode("utf-8"))
        self.assertIn(b"\x1b[38;2;138;147;163mmethod\x1b[0m", output)
        self.assertIn(b"\x1b[38;2;76;155;107m1.25x\x1b[0m", output)

    def test_narrow_terminal_wraps_long_status_at_the_object_column(self):
        code, output = self.capture(demo_command("status"), columns=40, NO_COLOR="1")
        self.assertEqual(code, 0, output.decode("utf-8"))
        lines = output.splitlines()
        self.assertTrue(any(line.startswith(b" " * 16) for line in lines))
        self.assertTrue(all(len(line) <= 39 for line in lines), lines)

    def test_progress_moves_from_waiting_to_counting(self):
        code, output = self.capture(demo_command("progress"))
        self.assertEqual(code, 0, output.decode("utf-8"))
        for milestone in (b"Preparing tasks", b"Reading inputs ready\r\n", b"[1/3]", b"[3/3]"):
            self.assertIn(milestone, output)
        waiting = output.index(b"Preparing tasks")
        first = output.index(b"[1/3]")
        last = output.index(b"[3/3]")
        line = output.index(b"Reading inputs ready\r\n")
        self.assertLess(waiting, line)
        self.assertLess(line, first)
        self.assertLess(first, last)
        progress, _, status = output.rpartition(ERASE_LINE)
        self.assertIn(b"[3/3]", progress)
        self.assertIn(b"[OK]", status)
        self.assertNotIn(b"[1/3]", status)

    def test_redirecting_stdout_leaves_progress_on_the_terminal(self):
        with TemporaryFile() as saved:
            code, terminal = self.capture(
                demo_command("progress"), stdout=saved, NO_COLOR="1",
            )
            saved.seek(0)
            output = saved.read()
        self.assertEqual(code, 0, terminal.decode("utf-8"))
        self.assertEqual(output, b"Reading inputs ready\n[OK]   test     3 samples\n")
        self.assertIn(b"[1/3]", terminal)
        self.assertTrue(terminal.endswith(ERASE_LINE), terminal)
        self.assertNotIn(b"Reading inputs", terminal)
        self.assertNotIn(b"[OK]", terminal)

    def test_live_output_keeps_a_partial_line_until_newline(self):
        program = dedent("""
            from time import sleep
            from vecorge_console import Console

            console = Console()
            with console.progress("Waiting for output", delay_seconds=0):
                console.write("partial")
                sleep(0.4)
                console.write(" output\\n")
                sleep(0.4)
            console.status("ok", "test", "example")
        """)
        code, output = self.capture([sys.executable, "-B", "-c", program], NO_COLOR="1")
        self.assertEqual(code, 0, output.decode("utf-8"))
        self.assertIn(b"partial output\r\n", output)
        initial, _, resumed = output.partition(b"partial output\r\n")
        self.assertIn(b"Waiting for output", initial)
        self.assertIn(b"Waiting for output", resumed)
        self.assertIn(b"[OK]", resumed)
        self.assertLess(resumed.index(b"Waiting for output"), resumed.index(b"[OK]"))

    def test_dumb_terminal_displays_result_without_progress(self):
        code, output = self.capture(demo_command("progress"), TERM="dumb")
        self.assertEqual(code, 0, output.decode("utf-8"))
        self.assertIn(b"[OK]", output)
        self.assertNotIn(b"\x1b", output)
        self.assertNotIn(b"Preparing tasks", output)

    def test_interrupt_clears_the_active_progress_line(self):
        code, output = self.capture(demo_command("interrupt"), interrupt_on=b"Press Ctrl+C")
        self.assertEqual(code, 130, output.decode("utf-8"))
        progress, _, warning = output.rpartition(ERASE_LINE)
        self.assertIn(b"Press Ctrl+C", progress)
        self.assertIn(b"[WARN]", warning)
        self.assertIn(b"interrupted", warning)
        self.assertNotIn(b"[OK]", output)

    def test_interrupt_uses_the_selected_exit_code_after_cleaning(self):
        with TemporaryDirectory() as directory:
            file = Path(directory) / "exit-codes.toml"
            file.write_text("[exit_codes]\ninterrupted = 23\n", encoding="utf-8")
            code, output = self.capture(
                demo_command("interrupt", "--exit-codes", str(file)), interrupt_on=b"Press Ctrl+C",
            )
        self.assertEqual(code, 23, output.decode("utf-8"))
        progress, _, warning = output.rpartition(ERASE_LINE)
        self.assertIn(b"Press Ctrl+C", progress)
        self.assertIn(b"[WARN]", warning)
        self.assertNotIn(b"[OK]", output)
