import unittest

from backend.engine import budgeted_windows, clips, evaluate


EVENTS = [
    {'event_id': 'a', 'class_id': 'goal', 'timestamp_sec': 10, 'confidence': .9},
    {'event_id': 'b', 'class_id': 'foul', 'timestamp_sec': 14, 'confidence': .4},
    {'event_id': 'c', 'class_id': 'corner', 'timestamp_sec': 30, 'confidence': .8},
]


class DecoderTests(unittest.TestCase):
    def test_overlapping_asymmetric_windows_merge_with_provenance(self):
        rows = clips(EVENTS, 40, threshold=.1, before=8, after=5)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['event_ids'], ['a', 'b'])
        self.assertEqual(rows[0]['start_sec'], 2.0)
        self.assertEqual(rows[0]['end_sec'], 19.0)
        self.assertIn('merged', rows[0]['selection_reason'])

    def test_budget_uses_union_duration(self):
        rows = budgeted_windows(EVENTS, 40, budget_seconds=17, threshold=.1, before=8, after=5)
        self.assertEqual([event['event_id'] for row in rows for event in row['events']], ['a', 'b'])
        self.assertLessEqual(sum(row['duration_sec'] for row in rows), 17)

    def test_context_metrics_use_complete_selected_union(self):
        result = evaluate([{'start_sec': 2, 'end_sec': 10}, {'start_sec': 10, 'end_sec': 15}], [{'start_sec': 4, 'end_sec': 14}], 20)
        self.assertEqual(result['context_coverage'], 1)
        self.assertEqual(result['complete_context_rate'], 1)
        self.assertAlmostEqual(result['temporal_precision'], 10 / 13)
        self.assertAlmostEqual(result['redundant_seconds_removed'], 0)

    def test_invalid_selected_interval_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate([{'start_sec': 8, 'end_sec': 3}], [{'start_sec': 1, 'end_sec': 2}], 10)


if __name__ == '__main__':
    unittest.main()
