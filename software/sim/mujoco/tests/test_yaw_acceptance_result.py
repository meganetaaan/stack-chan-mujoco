"""Verifier fixtures relabel a copied development record; no formal trial is run."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from run_yaw_acceptance import verify_result


class AcceptanceResultTests(unittest.TestCase):
    def setUp(self):
        source=Path('validation/yaw_backward_contact_development_v1/fresh20/311102')
        if not source.exists():source=Path('outputs/yaw_adaptive_width_fresh20_v1/311102')
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.trial=Path(self.temp.name)/'fixture';shutil.copytree(source,self.trial)
        self.report=json.loads((self.trial/'report.json').read_text())
        self.report.update(formal_acceptance=True,acceptance={'manifest_sha256':'unit-test-only'},acceptance_pass=True)
        self.save()

    def save(self):
        (self.trial/'report.json').write_text(json.dumps(self.report)+'\n')

    def test_recorded_metrics_are_recomputed(self):
        self.assertTrue(verify_result(self.trial,311102,'randomized','unit-test-only')['pass'])

    def test_wrong_snapshot_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'snapshot mismatch'):
            verify_result(self.trial,311102,'randomized','different')

    def test_changed_seed_parameters_are_rejected(self):
        self.report['parameters']['mass_scale']+=.001;self.save()
        with self.assertRaisesRegex(ValueError,'randomization differs'):
            verify_result(self.trial,311102,'randomized','unit-test-only')


if __name__=='__main__':unittest.main()
