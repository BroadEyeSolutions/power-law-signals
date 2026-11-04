import csv
import os
import shutil
import tempfile
import unittest

from analysis.resolve_sources import load_maps
from analysis.update_maps import find_new, append

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class UpdateMaps(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        for f in os.listdir(os.path.join(ROOT, 'maps')):
            if f.endswith('.csv'):
                shutil.copy(os.path.join(ROOT, 'maps', f), self.dir)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def rows(self, f):
        with open(os.path.join(self.dir, f), newline='', encoding='utf-8') as fh:
            return list(csv.DictReader(fh))

    def test_known_values_add_nothing(self):
        leads = [{'utm_source': 'facebook', 'utm_medium': 'ig', 'utm_campaignid': '120200000000101', 'form_id': 'WF-0001', 'capture_method': 'web_form'}]
        self.assertEqual(find_new(leads, load_maps(self.dir), self.dir), {})

    def test_new_values_are_appended_unverified_and_existing_rows_kept(self):
        before = self.rows('MAP_CAMPAIGN.csv')
        leads = [
            {'utm_source': 'threads_ads', 'utm_campaign': 'x'},
            {'utm_source': 'meta', 'utm_medium': 'reels_feed', 'utm_campaignid': '120200000000999', 'utm_campaign': 'new-camp'},
            {'utm_source': 'meta', 'utm_campaignid': '120200000000999'},
            {'form_id': 'WF-0099', 'capture_method': 'kiosk'},
        ]
        new = find_new(leads, load_maps(self.dir), self.dir, today='2026-11-02')
        self.assertEqual([r['raw_value'] for r in new['MAP_SOURCE.csv']], ['threads_ads'])
        self.assertEqual(new['MAP_MEDIUM.csv'][0]['raw_value'], 'reels_feed')
        self.assertEqual(new['MAP_CAPTURE.csv'][0]['raw_value'], 'kiosk')
        self.assertEqual(new['MAP_FORM.csv'][0]['status'], 'unregistered')
        camp = new['MAP_CAMPAIGN.csv']
        self.assertEqual(len(camp), 1)                       # one campaign id, seen twice, gets one row
        self.assertEqual(camp[0]['campaign_key'], 'C00005')  # the next key, never a reused one
        self.assertIn('Seen on 2 lead(s)', camp[0]['notes'])
        backup = append(self.dir, new)
        after = self.rows('MAP_CAMPAIGN.csv')
        self.assertEqual(after[:len(before)], before)        # nothing above the new rows changed
        self.assertEqual((after[-1]['status'], after[-1]['pro_campaign']), ('unverified', ''))
        self.assertTrue(os.path.exists(os.path.join(backup, 'MAP_CAMPAIGN.csv')))
        # the new campaign is now known, so a second run adds nothing for it
        again = find_new(leads, load_maps(self.dir), self.dir)
        self.assertNotIn('MAP_CAMPAIGN.csv', again)


if __name__ == '__main__':
    unittest.main()
