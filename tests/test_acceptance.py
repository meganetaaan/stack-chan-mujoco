import unittest
from stackchan_rl.acceptance import PROTOCOL, assess_batch, assess_trial


def trial(index=0, **changes):
    record = dict(protocol=PROTOCOL, trial_id=str(index), design_id="fixture-design",
                  controller_id="fixture-controller", evidence="synthetic-test-fixture",
                  domain="simulation", forward_m=10., elapsed_s=100., fall=False,
                  self_collision=False, protective_stop=False, assisted=False,
                  interrupted=False, continuous_bipedal_walk=True)
    return record | changes


class AcceptanceTests(unittest.TestCase):
    def test_exact_boundary(self):
        self.assertTrue(assess_trial(trial())["passed"])

    def test_short_distance(self):
        self.assertFalse(assess_trial(trial(forward_m=9.999))["passed"])

    def test_overshoot_does_not_buy_time(self):
        self.assertFalse(assess_trial(trial(forward_m=12., elapsed_s=101.))["passed"])

    def test_invalid_measurements(self):
        for value in (None, True, "10", float("nan"), float("inf")):
            with self.subTest(value=value):
                self.assertFalse(assess_trial(trial(forward_m=value))["passed"])
        self.assertFalse(assess_trial(trial(elapsed_s=0))["passed"])
        self.assertFalse(assess_trial(trial(elapsed_s=1e-320))["passed"])

    def test_missing_safety_evidence(self):
        for key in ("fall", "self_collision", "protective_stop", "assisted", "interrupted"):
            for value in (None, True, 0):
                self.assertFalse(assess_trial(trial(**{key: value}))["passed"])

    def test_success_count_and_domain(self):
        records = [trial(i, fall=i < 2) for i in range(20)]
        report = assess_batch(records)
        self.assertTrue(report["recorded_criteria_met"])
        self.assertFalse(report["hardware_criteria_met"])
        records[2]["fall"] = True
        self.assertFalse(assess_batch(records)["recorded_criteria_met"])

    def test_incomplete_duplicate_and_mixed(self):
        self.assertFalse(assess_batch([])["recorded_criteria_met"])
        self.assertFalse(assess_batch([trial(i) for i in range(19)])["recorded_criteria_met"])
        self.assertFalse(assess_batch([trial()] * 20)["recorded_criteria_met"])
        for key, value in (("domain", "hardware"), ("design_id", "other"), ("controller_id", "other")):
            records = [trial(i) for i in range(20)]
            records[0][key] = value
            self.assertFalse(assess_batch(records)["recorded_criteria_met"])

    def test_walk_and_provenance_required(self):
        for key, value in (("continuous_bipedal_walk", False), ("evidence", ""), ("protocol", "old")):
            self.assertFalse(assess_trial(trial(**{key: value}))["passed"])
