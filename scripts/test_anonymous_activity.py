import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from anonymous_activity import validate_activity
from test_update_profile import pr
from update_profile import render
from visuals import build_visuals, hero, PALETTES


def activity():
    return {
        'schemaVersion': 1,
        'asOf': '2026-11-04',
        'lifetimeContributions': 13123,
        'lastYearContributions': 9853,
        'anonymousPrivateLastYear': 9795,
        'days': [['2026-10-01', 12], ['2026-11-04', 36]],
    }


class AnonymousActivityTests(unittest.TestCase):
    def test_private_identifiers_cannot_enter_published_activity(self):
        data = activity()
        data['repositoryNames'] = ['private-customer-project']
        with self.assertRaises(ValueError):
            validate_activity(data)

    def test_private_details_cannot_be_hidden_inside_calendar_entries(self):
        data = activity()
        data['days'][0].append('private commit message')
        with self.assertRaises(ValueError):
            validate_activity(data)

    def test_inconsistent_private_totals_are_rejected(self):
        data = activity()
        data['anonymousPrivateLastYear'] = 10000
        with self.assertRaises(ValueError):
            validate_activity(data)

    def test_private_pr_cannot_enter_artwork(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                build_visuals([pr(private=True)], activity(), Path(directory))

    def test_private_activity_is_counted_but_no_private_identifiers_are_added(self):
        output = render([pr()], activity())
        self.assertIn('13,123 lifetime contributions', output)
        self.assertIn('9,795 anonymous private contributions', output)
        self.assertNotIn('private-customer-project', output)
        self.assertNotIn('github-profile-summary-cards', output)

    def test_responsive_artwork_handles_empty_single_and_large_counts(self):
        states = [activity(), activity(), activity()]
        for key in ('lifetimeContributions', 'lastYearContributions', 'anonymousPrivateLastYear'):
            states[0][key] = 0
        states[0]['days'] = []
        states[1]['lifetimeContributions'] = 1
        states[1]['lastYearContributions'] = 1
        states[1]['anonymousPrivateLastYear'] = 1
        states[2]['lifetimeContributions'] = 1234567
        states[2]['lastYearContributions'] = 123456
        states[2]['anonymousPrivateLastYear'] = 123000
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for data in states:
                build_visuals([] if data['lifetimeContributions'] == 0 else [pr()], data, target)
                self.assertEqual(len(list(target.glob('*.svg'))), 12)
                for path in target.glob('*.svg'):
                    root = ET.parse(path).getroot()
                    self.assertEqual(root.tag, '{http://www.w3.org/2000/svg}svg')
                    self.assertNotIn('NaN', path.read_text())


if __name__ == '__main__':
    unittest.main()
