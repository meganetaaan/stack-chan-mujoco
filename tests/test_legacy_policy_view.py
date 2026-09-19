import json
from pathlib import Path
import unittest
import numpy as np
from stackchan_rl.residual_heading import HeadingResidualEnv
from stackchan_rl.legacy_policy_view import LegacyPolicyView


class LegacyPolicyViewTests(unittest.TestCase):
    def test_observations_match_original_without_modifying_physics(self):
        config=json.loads(Path('policies/r6_mounted_seed20260924/config.json').read_text())
        config['randomize']=False
        env=HeadingResidualEnv(config)
        try:
            expected,_=env.reset(seed=310501)
            view=LegacyPolicyView(env.model,env.data,env.base,env.qadr,env.vadr,env.reference,config,env.start,310501)
            for i in range(21):
                before=env.get_state().copy()
                actual=view.observe(env.i,env.bank.filtered,env.previous_action)
                np.testing.assert_array_equal(actual,expected)
                np.testing.assert_array_equal(env.get_state(),before)
                if i<20:expected,_,_,_,_=env.step(np.zeros(10))
            with self.assertRaisesRegex(RuntimeError,'cannot step'):view.step(np.zeros(10))
        finally:env.close()


if __name__=='__main__':unittest.main()
