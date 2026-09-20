"""Keep interpolation from overstating the time bound used for goal screening."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TraversalTests(unittest.TestCase):
    def run_measurement(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            (run/'report.json').write_text(json.dumps({'simulation':{'failure':None}}))
            (run/'trajectory.csv').write_text('time_s,forward_m\n'+rows)
            output = run/'measurement.json'
            subprocess.run([sys.executable,str(ROOT/'measure_forward_traversal.py'),
                            '--run',str(run),'--out',str(output)],check=True,capture_output=True)
            return json.loads(output.read_text())

    def test_uses_observed_crossing_bound_and_keeps_initial_rest(self):
        r = self.run_measurement('1,0\n99.98,9.999\n100.02,10.003\n')
        self.assertLess(r['crossing']['interpolated_time_s'],100)
        self.assertGreater(r['crossing']['first_sample_at_distance_time_s'],100)
        self.assertLess(r['crossing']['conservative_average_speed_m_s'],.1)
        self.assertFalse(r['goal_achieved'])
        self.assertIsNone(r['contact_metrics'])

    def test_back_and_forth_travel_does_not_count_as_forward_ten_metres(self):
        r = self.run_measurement('1,0\n10,6\n20,0\n30,6\n')
        self.assertIsNone(r['crossing'])
        self.assertFalse(r['goal_achieved'])


if __name__ == '__main__':
    unittest.main()
