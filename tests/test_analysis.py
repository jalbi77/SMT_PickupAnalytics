import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from analysis import calculate, SPECS
from streamlit.testing.v1 import AppTest


def sample():
    return pd.DataFrame([dict(DeviceComment='A001', Fidl='F001', Nid='N001',
                              FeedCount=100, PickupCount=100, RejectParts=1,
                              NoPickupCount=2, PickupErrors=3, VisionErrors=4)])


class AnalysisTests(unittest.TestCase):
    def test_weights_and_aggregation(self):
        for name, expected in [('Bauteile', 15), ('Feeder', 8), ('Saugdüsen', 20)]:
            result, missing = calculate(pd.concat([sample(), sample()]), name)
            self.assertEqual(missing, 0)
            self.assertEqual(result.iloc[0].WeightedErrors, expected * 2)
            self.assertAlmostEqual(result.iloc[0].ErrorIndex, expected / 100)
            self.assertEqual(result.iloc[0].UnweightedErrors, (5 if name == 'Feeder' else 10) * 2)

    def test_zero_denominator(self):
        df = sample()
        df['FeedCount'] = 0
        result, _ = calculate(df, 'Bauteile')
        self.assertTrue(pd.isna(result.iloc[0].ErrorIndex))
        self.assertIn('Nicht bewertbar', result.iloc[0].Status)

    def test_missing_id_and_empty(self):
        df = sample()
        df['Fidl'] = None
        result, missing = calculate(df, 'Feeder')
        self.assertTrue(result.empty)
        self.assertEqual(missing, 1)
        self.assertTrue(calculate(sample().iloc[:0], 'Bauteile')[0].empty)

    def test_bad_counts(self):
        for bad in [None, -1, float('inf'), 'bad']:
            df = sample()
            df['FeedCount'] = bad
            with self.assertRaises((ValueError, TypeError)):
                calculate(df, 'Bauteile')

    def test_ui_refresh_failure_retains_data(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'main.py')).run(timeout=20)
        self.assertFalse(app.exception)
        with patch('data.load_data', return_value=(sample(), sample())):
            app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe), 3)
        with patch('data.load_data', side_effect=RuntimeError('test')):
            app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.error), 1)
        self.assertEqual(len(app.dataframe), 3)


if __name__ == '__main__':
    unittest.main()
