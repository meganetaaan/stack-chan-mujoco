"""Wrapper contract tests using mock KiCad calls, NOT native ERC/DRC tests."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("kicad_review", SKILL / "scripts/kicad_review.py")
assert SPEC is not None and SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sch = self.root / "root with spaces.kicad_sch"
        self.pcb = self.root / "controller.kicad_pcb"
        # These are mock inputs, deliberately not valid KiCad designs.
        self.sch.write_text("mock schematic", encoding="utf-8")
        self.pcb.write_text("mock pcb", encoding="utf-8")
        self.out = self.root / "reports"
        self.calls = []
        self.native_exit = 0
        self.report_mode = "ok"
        self.refill = True
        self.fail_kind = None
        self.timeout_kind = None
        self.mutate = False
        self.dependency_mutate_path = None

    def fake_run(self, command, **kwargs):
        self.calls.append(command)
        self.assertFalse(kwargs.get("shell", False))
        self.assertGreater(kwargs["timeout"], 0)
        if command[1:] == ["version"]:
            return subprocess.CompletedProcess(command, 0, "10.0.0\n", "")
        if command[-1] == "--help":
            flags = "--format --severity-all --exit-code-violations"
            if self.refill:
                flags += " --refill-zones"
            return subprocess.CompletedProcess(command, 0, flags, "")
        if command[1] == self.timeout_kind:
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        report = Path(command[command.index("--output") + 1])
        if self.report_mode == "ok":
            report.write_text(json.dumps({"source": command[-1], "violations": []}), encoding="utf-8")
        elif self.report_mode == "invalid":
            report.write_text("not json", encoding="utf-8")
        elif self.report_mode == "empty":
            report.write_text("{}", encoding="utf-8")
        if self.mutate:
            Path(command[-1]).write_text("changed", encoding="utf-8")
        if self.dependency_mutate_path is not None:
            self.dependency_mutate_path.write_text("changed", encoding="utf-8")
        code = 3 if command[1] == self.fail_kind else self.native_exit
        return subprocess.CompletedProcess(command, code, "mock stdout", "mock stderr")

    def invoke(self, *args):
        with patch.object(review.shutil, "which", return_value="/mock/kicad-cli"), \
             patch.object(review.subprocess, "run", side_effect=self.fake_run), \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return review.main([*args, "--output-dir", str(self.out)])

    def summaries(self):
        return [json.loads(p.read_text()) for p in self.out.glob("*/summary.json")]

    def test_no_inputs_is_not_success(self):
        with self.assertRaises(SystemExit) as exc:
            self.invoke()
        self.assertEqual(exc.exception.code, 2)
        self.assertEqual(self.calls, [])

    def test_missing_input_is_not_success(self):
        self.assertEqual(self.invoke("--pcb", str(self.root / "missing.kicad_pcb")), 2)
        self.assertEqual(self.calls, [])

    def test_wrong_extension_is_not_success(self):
        self.assertEqual(self.invoke("--pcb", str(self.sch)), 2)

    def test_missing_cli_is_not_success(self):
        with patch.object(review.shutil, "which", return_value=None), redirect_stderr(io.StringIO()):
            self.assertEqual(review.main([
                "--schematic", str(self.sch), "--pcb", str(self.pcb),
                "--output-dir", str(self.out),
            ]), 2)
        summary = self.summaries()[0]
        self.assertEqual(summary["exit_code"], 2)
        self.assertIn("preflight_error", summary)
        self.assertEqual(
            [check["status"] for check in summary["checks"]],
            ["NOT_CHECKED", "NOT_CHECKED"],
        )
        for check in summary["checks"]:
            log = Path(check["log"])
            self.assertTrue(log.is_file())
            self.assertIn("NOT_CHECKED", log.read_text(encoding="utf-8"))
        self.assertTrue((next(self.out.glob("*/preflight.log"))).is_file())

    def test_unsupported_cli_is_not_success(self):
        with patch.object(review.shutil, "which", return_value="/mock/kicad-cli"), \
             patch.object(review.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "9.0.0", "")), \
             redirect_stderr(io.StringIO()):
            self.assertEqual(review.main([
                "--pcb", str(self.pcb), "--output-dir", str(self.out),
            ]), 2)
        summary = self.summaries()[0]
        self.assertEqual(summary["checks"][0]["status"], "NOT_CHECKED")
        self.assertIn("Unsupported KiCad", summary["checks"][0]["error"])

    def test_both_checks_include_warnings_exclusions_and_do_not_save_or_infer_parity(self):
        self.assertEqual(self.invoke("--schematic", str(self.sch), "--pcb", str(self.pcb)), 0)
        commands = [c for c in self.calls if "--output" in c]
        self.assertEqual(len(commands), 2)
        for command in commands:
            self.assertIn("--severity-all", command)
            self.assertIn("--exit-code-violations", command)
            self.assertNotIn("--save-board", command)
            self.assertNotIn("--schematic-parity", command)
        self.assertNotIn("--refill-zones", commands[0])
        self.assertIn("--refill-zones", commands[1])
        self.assertEqual(commands[0][-1], str(self.sch))
        self.assertEqual(self.pcb.read_text(), "mock pcb")
        summary = self.summaries()[0]
        self.assertEqual([c["status"] for c in summary["checks"]], ["PASS", "PASS"])
        self.assertTrue(summary["manual_review_required"])

    def test_native_violation_exit_becomes_lint_failure(self):
        self.native_exit = 5
        self.assertEqual(self.invoke("--pcb", str(self.pcb)), 1)
        self.assertEqual(self.summaries()[0]["checks"][0]["status"], "FAIL")

    def test_tool_error_does_not_prevent_remaining_check(self):
        self.fail_kind = "sch"
        self.assertEqual(self.invoke("--schematic", str(self.sch), "--pcb", str(self.pcb)), 2)
        self.assertEqual([c["status"] for c in self.summaries()[0]["checks"]], ["NOT_CHECKED", "PASS"])

    def test_timeout_is_not_success(self):
        self.timeout_kind = "pcb"
        self.assertEqual(self.invoke("--pcb", str(self.pcb)), 2)

    def test_bad_or_missing_report_is_not_success(self):
        for mode in ("missing", "invalid", "empty"):
            with self.subTest(mode=mode):
                self.report_mode = mode
                self.assertEqual(self.invoke("--pcb", str(self.pcb)), 2)

    def test_new_run_cannot_reuse_stale_report(self):
        self.assertEqual(self.invoke("--pcb", str(self.pcb)), 0)
        self.report_mode = "missing"
        self.assertEqual(self.invoke("--pcb", str(self.pcb)), 2)
        self.assertEqual(len(self.summaries()), 2)

    def test_duplicate_inputs_are_only_checked_once(self):
        self.assertEqual(self.invoke("--pcb", str(self.pcb), "--pcb", str(self.pcb)), 0)
        self.assertEqual(len(self.summaries()[0]["checks"]), 1)

    def test_same_basename_does_not_collide(self):
        other = self.root / "other" / self.pcb.name
        other.parent.mkdir()
        other.write_text("second mock pcb")
        self.assertEqual(self.invoke("--pcb", str(self.pcb), "--pcb", str(other)), 0)
        reports = [c["report"] for c in self.summaries()[0]["checks"]]
        self.assertEqual(len(set(reports)), 2)

    def test_old_cli_requires_explicit_prefilled_confirmation(self):
        self.refill = False
        self.assertEqual(self.invoke("--pcb", str(self.pcb)), 2)
        self.assertEqual(self.invoke("--pcb", str(self.pcb), "--zones-prefilled"), 0)
        success_summary = next(
            summary for summary in self.summaries()
            if summary["checks"][0]["status"] == "PASS"
        )
        check = success_summary["checks"][0]
        self.assertEqual(check["zones"], "prefilled_by_caller")
        self.assertNotIn("--refill-zones", check["command"])

    def test_prefilled_confirmation_is_not_needed_for_schematic(self):
        self.refill = False
        self.assertEqual(self.invoke("--schematic", str(self.sch)), 0)

    def test_invalid_timeout_is_rejected(self):
        with self.assertRaises(SystemExit) as exc:
            self.invoke("--pcb", str(self.pcb), "--timeout", "0")
        self.assertEqual(exc.exception.code, 2)

    def test_input_change_is_not_success(self):
        self.mutate = True
        self.assertEqual(self.invoke("--pcb", str(self.pcb)), 2)

    def test_hierarchical_and_rule_dependencies_are_snapshotted(self):
        child = self.root / "child.kicad_sch"
        project = self.sch.with_suffix(".kicad_pro")
        rules = self.sch.with_suffix(".kicad_dru")
        self.sch.write_text('(property "Sheetfile" "child.kicad_sch")', encoding="utf-8")
        child.write_text("child", encoding="utf-8")
        project.write_text("project", encoding="utf-8")
        rules.write_text("rules", encoding="utf-8")

        self.assertEqual(self.invoke("--schematic", str(self.sch)), 0)
        check = self.summaries()[0]["checks"][0]
        expected = {str(path.resolve()) for path in (self.sch, child, project, rules)}
        self.assertEqual(set(check["dependencies"]), expected)
        self.assertEqual(set(check["dependency_sha256"]), expected)

    def test_change_to_any_hierarchical_dependency_is_not_success(self):
        child = self.root / "child.kicad_sch"
        project = self.sch.with_suffix(".kicad_pro")
        rules = self.sch.with_suffix(".kicad_dru")
        self.sch.write_text('(property "Sheetfile" "child.kicad_sch")', encoding="utf-8")
        child.write_text("child", encoding="utf-8")
        project.write_text("project", encoding="utf-8")
        rules.write_text("rules", encoding="utf-8")

        for dependency in (child, project, rules):
            with self.subTest(dependency=dependency.name):
                self.dependency_mutate_path = dependency
                self.assertEqual(self.invoke("--schematic", str(self.sch)), 2)
                check = self.summaries()[-1]["checks"][0]
                self.assertIn("Review dependency", check["error"])


if __name__ == "__main__":
    unittest.main()
