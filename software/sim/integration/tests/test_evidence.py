import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from result_bundle import validate


class EvidenceTests(unittest.TestCase):
    def fixture(self,domain):
        return {'schema_version':1,'domain':domain,'commands':[],
                'inputs':[{'path':'input.json','sha256':'0'*64}],
                'parameters':[{'name':'fixture','value':1,'unit':'1','status':'assumed','source':'synthetic test fixture'}],
                'gates':[{'criterion':'synthetic test only','passed':True}],
                'artifacts':[],'passed':True}

    def test_shared_domains(self):
        for domain in ['mujoco','circuits','structural','sil','actuator']:
            self.assertTrue(validate(self.fixture(domain))['passed'])

    def test_rejects_false_overall_success(self):
        r=self.fixture('mujoco');r['gates'][0]['passed']=False
        with self.assertRaises(ValueError):validate(r)

    def test_rejects_missing_evidence_kind_and_nonfinite(self):
        r=self.fixture('circuits');r['parameters'][0]['status']='unknown'
        with self.assertRaises(ValueError):validate(r)
        r=self.fixture('structural');r['parameters'][0]['value']=float('nan')
        with self.assertRaises(ValueError):validate(r)

    def test_rejects_paths_outside_bundle(self):
        r=self.fixture('mujoco');r['inputs'][0]['path']='../untracked.dat'
        with self.assertRaises(ValueError):validate(r)


if __name__=='__main__':unittest.main()
