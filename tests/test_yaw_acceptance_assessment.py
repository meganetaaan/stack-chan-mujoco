"""Admission tests only: no dynamics or acceptance-seed sampling occurs."""
import json
from pathlib import Path
import tempfile
import unittest
from assess_yaw_acceptance import assess
from yaw_acceptance import PROTOCOL, PROTOCOL_SHA, sha


class FormalAssessmentTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        protocol=json.loads(PROTOCOL.read_text())
        self.snapshot=self.root/'snapshot.json'
        self.snapshot.write_text(json.dumps({k:protocol[k] for k in ['fixed_seeds','randomized_seeds','required_successes']}|{'protocol_sha256':PROTOCOL_SHA}))
        self.rows=[{'group':g,'seed':s} for g,key in [('fixed','fixed_seeds'),('randomized','randomized_seeds')] for s in protocol[key]]

    def save_summary(self,rows,changed=None):
        (self.root/'summary.json').write_text(json.dumps({'formal_acceptance':True,'snapshot_sha256':sha(self.snapshot),'sources_changed':changed or [],'trials':rows}))

    def test_missing_trial_is_rejected_before_reading_states(self):
        self.save_summary(self.rows[:-1])
        with self.assertRaisesRegex(ValueError,'40 unique'):assess(self.snapshot,self.root)

    def test_duplicate_replacing_a_seed_is_rejected(self):
        self.save_summary(self.rows[:-1]+self.rows[:1])
        with self.assertRaisesRegex(ValueError,'40 unique'):assess(self.snapshot,self.root)

    def test_changed_sources_are_rejected(self):
        self.save_summary(self.rows,['changed.py'])
        with self.assertRaisesRegex(ValueError,'sources changed'):assess(self.snapshot,self.root)


if __name__=='__main__':unittest.main()
