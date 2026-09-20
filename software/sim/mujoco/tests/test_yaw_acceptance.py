from pathlib import Path
import json
import tempfile
from types import SimpleNamespace
import unittest
from yaw_acceptance import CONTROLS,PROTOCOL,create_snapshot,validate_trial


class AcceptanceAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.design=Path('assets/r8_yaw_offset_flange_v1')
        reference=Path('validation/yaw_adaptive_width_development_v1/yaw_adaptive_width_ref205_v1/reference.json.gz')
        self.path=create_snapshot(self.design,reference,Path(self.temp.name)/'snapshot')
        snapshot=json.loads(self.path.read_text())
        self.args=SimpleNamespace(**CONTROLS,acceptance_manifest=self.path,protocol=PROTOCOL,
                                  design=self.design,reference=Path(snapshot['reference']),seed=217000,randomize=False)

    def test_valid_fixed_group_is_admitted(self):
        self.assertEqual(validate_trial(self.args)['group'],'fixed')

    def test_wrong_group_is_rejected(self):
        self.args.seed=218000
        with self.assertRaisesRegex(ValueError,'seed does not belong'):validate_trial(self.args)

    def test_control_override_is_rejected(self):
        self.args.yaw_kp=5.
        with self.assertRaisesRegex(ValueError,'control override'):validate_trial(self.args)

    def test_omitted_joint_map_hash_is_rejected(self):
        snapshot=json.loads(self.path.read_text())
        del snapshot['source_sha256'][str(self.design/'models/joint_map.json')]
        self.path.write_text(json.dumps(snapshot))
        with self.assertRaisesRegex(ValueError,'incomplete dependency'):validate_trial(self.args)

    def test_changed_reference_is_rejected(self):
        with self.args.reference.open('ab') as f:f.write(b'changed')
        with self.assertRaisesRegex(ValueError,'frozen dependency changed'):validate_trial(self.args)


if __name__=='__main__':unittest.main()
