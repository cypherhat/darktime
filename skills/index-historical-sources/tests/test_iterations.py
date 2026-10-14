"""Exercise late discoveries, convergence resets, ambiguous identities and reviewed merges."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

path = Path(__file__).parents[1] / 'scripts/iterate_references.py'
spec = importlib.util.spec_from_file_location('iterations', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Iterations(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.archive = dict(sources=[dict(id='book', pageCount=2)],
                            people=[dict(id='alice', name='Alice Morgan', kind='person', aliases=[])], organizations=[])
        self.pages = ['Alice Morgan directs a bank.\n\nAliceMorg an later left.\n\nAlice M0rgan attended.\n\nAlice Morgam wrote a letter.', 'Nothing relevant.']
        self.state = {}

    def corpus(self):
        (self.directory / 'book-pages.json').write_text(json.dumps(self.pages))
        return m.Corpus(self.archive, self.directory)

    def run_to_stable(self, aliases=None, equivalences=None, decisions=None):
        corpus = self.corpus()
        reports = []
        for _ in range(12):
            r = m.run_pass(self.archive, corpus, self.state, aliases or {}, equivalences or [], decisions or {})
            reports.append(r)
            if r['searchSaturated']:
                return reports
        self.fail('Iteration did not saturate')

    def test_late_ocr_and_typo_hits_prevent_early_plateau(self):
        reports = self.run_to_stable()
        self.assertFalse(reports[2]['searchSaturated'])  # two quiet passes before widening is exhausted
        self.assertEqual(reports[3]['newReferences'], 1)
        self.assertEqual(reports[4]['newReferences'], 1)
        self.assertEqual(reports[5]['newReferences'], 1)
        self.assertEqual([r['newReferences'] for r in reports[-2:]], [0, 0])
        self.assertEqual(reports[-1]['activeReferences'], 4)
        self.assertFalse(reports[-1]['reviewComplete'])

    def test_alias_revision_resets_counter_and_retains_separate_passages(self):
        self.run_to_stable()
        self.pages[1] = 'The Falcon spoke.\n\nThe Falcon returned.'
        # Both source revision and added alias invalidate the old quiet-pass proof.
        r = m.run_pass(self.archive, self.corpus(), self.state, {'alice': ['The Falcon']}, [], {})
        self.assertEqual(r['ruleLevel'], 1)
        self.assertEqual(r['quietPasses'], 0)
        self.assertEqual(r['newReferences'], 2)
        self.assertFalse(r['searchSaturated'])

    def test_widening_preserves_matches_before_dehyphenation(self):
        self.archive['people'][0]['name'] = 'Alice Mor Gan'
        self.pages[0] = 'Alice Mor-\nGan directs a bank.'
        reports = self.run_to_stable()
        self.assertTrue(all(r['activeReferences'] >= 1 for r in reports))

    def test_same_surname_is_not_automatic_identity_deduplication(self):
        self.archive['people'].append(dict(id='bob', name='Bob Morgan', kind='person', aliases=[]))
        reports = self.run_to_stable()
        paragraph = [r for r in self.state['references'].values() if r['active'] and r['page'] == 1 and r['paragraph'] == 0]
        self.assertEqual({r['entityId'] for r in paragraph}, {'alice', 'bob'})
        self.assertTrue(reports[-1]['searchSaturated'])

    def test_approved_equivalence_and_revocation_preserve_provenance(self):
        self.archive['people'].append(dict(id='alias', name='Alice Morgan', kind='person', aliases=[]))
        self.run_to_stable()
        approved = [dict(fromId='alias', toId='alice', reason='Explicit identity statement', citations=[dict(sourceId='book', pages=[1])])]
        r = m.run_pass(self.archive, self.corpus(), self.state, {}, approved, {})
        self.assertGreater(r['deduplicatedReferences'], 0)
        self.assertFalse(r['searchSaturated'])
        r = m.run_pass(self.archive, self.corpus(), self.state, {}, [], {})
        self.assertGreater(r['splitReferences'], 0)
        self.assertEqual({v['entityId'] for v in self.state['references'].values()}, {'alice', 'alias'})
        with self.assertRaises(ValueError):
            m.canonical_map({r['id']: r for r in self.archive['people']}, [dict(fromId='alice', toId='alias')], {'book': {'pageCount': 2}})

    def test_review_completion_requires_current_evidence_and_no_unresolved(self):
        self.run_to_stable()
        decisions = {key: dict(status='rejected', reason='Read passage; namesake', evidenceHash=r['evidenceHash'])
                     for key, r in self.state['references'].items() if r['active']}
        r = m.run_pass(self.archive, self.corpus(), self.state, {}, [], decisions)
        self.assertTrue(r['reviewComplete'])
        key = next(iter(decisions))
        decisions[key]['evidenceHash'] = 'stale'
        r = m.run_pass(self.archive, self.corpus(), self.state, {}, [], decisions)
        self.assertFalse(r['reviewComplete'])
        self.assertEqual(r['pendingReview'], 1)

if __name__ == '__main__':
    unittest.main()
