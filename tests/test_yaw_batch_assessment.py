import json
from pathlib import Path
import shutil
import tempfile
import unittest
from assess_yaw_development_batch import assess,sha


class BatchAssessmentTests(unittest.TestCase):
    def setUp(self):
        source=Path('validation/yaw_backward_contact_development_v1/fresh20')
        if not source.exists():source=Path('outputs/yaw_adaptive_width_fresh20_v1')
        if not (source/'311102/report.json').exists():self.skipTest('recorded batch fixture required')
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.batch=Path(self.temp.name)
        shutil.copytree(source/'311102',self.batch/'311102')
        manifest=json.loads((source/'manifest.json').read_text());manifest['seeds']=[311102]
        self.write('manifest.json',manifest)
        self.entry={'seed':311102,'development_trial_pass':True,'report_sha256':sha(self.batch/'311102/report.json')}
        self.write('summary.json',{'sources_changed':[],'successes':1,'trials':[self.entry]})

    def write(self,name,value):
        (self.batch/name).write_text(json.dumps(value)+'\n')

    def test_recomputes_recorded_success(self):
        self.assertEqual(assess(self.batch)['successes'],1)

    def test_missing_trial_is_rejected(self):
        self.write('summary.json',{'sources_changed':[],'successes':0,'trials':[]})
        with self.assertRaisesRegex(ValueError,'missing, extra, or duplicate'):assess(self.batch)

    def test_rehashed_false_success_label_is_rejected(self):
        report=json.loads((self.batch/'311102/report.json').read_text())
        report['development_trial_pass']=False
        self.write('311102/report.json',report)
        self.entry.update(development_trial_pass=False,report_sha256=sha(self.batch/'311102/report.json'))
        self.write('summary.json',{'sources_changed':[],'successes':0,'trials':[self.entry]})
        with self.assertRaisesRegex(ValueError,'success label mismatch'):assess(self.batch)


if __name__=='__main__':unittest.main()
