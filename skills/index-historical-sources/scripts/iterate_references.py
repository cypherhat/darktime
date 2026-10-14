#!/usr/bin/env python3
"""Widen reference discovery until two consecutive passes add no new passages.
Candidate search only: never edits the archive or automatically approves identity merges.
"""
import argparse
import fcntl
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata

VERSION = 1
ENGINE_HASH = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
RULES = [
    'registered names and reviewed aliases',
    'short names, institution base names and case-sensitive acronym leads',
    'surnames, personal initials and corporate suffix variants',
    'line-wrap dehyphenation and compact multiword OCR matching',
    'bounded OCR character confusions',
    'single-edit long tokens with an exact contextual name anchor',
]

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def normalize(text):
    text = re.sub(r'\b(?:[A-Za-z]\.\s*){2,}', lambda m: ''.join(re.findall(r'[A-Za-z]', m.group())) + ' ', text)
    text = unicodedata.normalize('NFKD', text).replace('\u00ad', '')
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()

def ocr_fold(text):
    return text.replace('0', 'o').replace('1', 'i').replace('l', 'i').replace('rn', 'm')

def one_edit(a, b):
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) <= 1
    if len(a) > len(b):
        a, b = b, a
    i = j = errors = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1
        else:
            errors += 1
            if errors > 1:
                return False
        j += 1
    return True

def variants(record, aliases):
    result = {}
    def add(text, level, kind):
        text = normalize(text)
        if len(text) >= 2:
            old = result.get((text, kind))
            if old is None or level < old:
                result[(text, kind)] = level
    for name in [record['name']] + record.get('aliases', []) + aliases:
        add(name, 1, 'registered')
    name = record['name'].split(',')[0]
    words = name.split()
    if record['kind'] == 'person':
        if len(words) > 2:
            add(words[0] + ' ' + words[-1], 2, 'generated')
        if words:
            surname = words[-1]
            if ' of ' in name and words[0] not in {'King', 'Lord', 'Sir'}:
                surname = words[0]
            if len(normalize(surname)) >= 4:
                add(surname, 3, 'ambiguous-surname')
            if len(words) >= 2:
                add(' '.join(w[0] for w in words[:-1]) + ' ' + words[-1], 3, 'generated-initials')
                add(words[0][0] + ' ' + words[-1], 3, 'generated-initials')
    else:
        base = re.split(r'\s+[·—]|\(', name)[0].strip()
        add(base, 2, 'generated')
        for part in re.split(r'\s*/\s*', base):
            add(part, 2, 'generated')
        initials = ''.join(w[0] for w in re.findall(r'[A-Za-z]+', base)
                           if w.lower() not in {'the', 'of', 'for', 'and', 'in', 'a', 'an', 'at', 'to'})
        if 3 <= len(initials) <= 6 and initials.upper() not in {'THE', 'AND', 'FOR', 'ALL', 'NOT', 'NOW'}:
            add(initials, 2, 'generated-acronym')
        for term in list(result):
            stripped = re.sub(r'\s+(company|corporation|incorporated|limited|inc|ltd|co)$', '', term[0])
            if stripped != term[0] and len(stripped.split()) >= 2:
                add(stripped, 3, 'generated-suffix')
    return [(term, kind, level) for (term, kind), level in result.items()]

class Corpus:
    def __init__(self, archive, pages_dir):
        self.passages = []
        self.tokens = defaultdict(set)
        self.compact_prefix = defaultdict(set)
        self.folded_prefix = defaultdict(set)
        self.page_hashes = {}
        for source in archive['sources']:
            pages = json.loads((pages_dir / f"{source['id']}-pages.json").read_text())
            if len(pages) != source['pageCount'] or not all(isinstance(p, str) for p in pages):
                raise ValueError(f"{source['id']}: page array does not match registered PDF pages")
            self.page_hashes[source['id']] = digest(pages)
            for page, raw in enumerate(pages, 1):
                for ordinal, paragraph in enumerate(re.split(r'\n\s*\n', raw)):
                    if not paragraph.strip():
                        continue
                    text = normalize(paragraph)
                    joined = normalize(re.sub(r'(?<=\w)[-‐‑]\s*\n\s*(?=\w)', '', paragraph))
                    tokens = joined.split()
                    passage = dict(sourceId=source['id'], page=page, paragraph=ordinal,
                                   textHash=digest(' '.join(paragraph.split())), text=text,
                                   joined=joined, compact=''.join(tokens), folded=ocr_fold(''.join(tokens)),
                                   raw=paragraph)
                    position = len(self.passages)
                    self.passages.append(passage)
                    for token in set(text.split() + tokens):
                        self.tokens[token].add(position)
                    for i in range(len(tokens)):
                        # Prefixes at token boundaries also cover letter-spaced and split words.
                        prefix = ''.join(tokens[i:i + 5])[:4]
                        if len(prefix) == 4:
                            self.compact_prefix[prefix].add(position)
                        prefix = ocr_fold(''.join(tokens[i:i + 6]))[:4]
                        if len(prefix) == 4:
                            self.folded_prefix[prefix].add(position)
        self.vocabulary = defaultdict(set)
        for token in self.tokens:
            if len(token) >= 5:
                self.vocabulary[('prefix', token[:2], len(token))].add(token)
                self.vocabulary[('suffix', token[-2:], len(token))].add(token)

    def matches(self, term, kind, level):
        words = term.split()
        anchor = min(words, key=lambda w: len(self.tokens.get(w, set())))
        for position in self.tokens.get(anchor, set()):
            p = self.passages[position]
            texts = [p['text'], p['joined']] if level >= 4 else [p['text']]
            if any(f' {term} ' in f' {text} ' for text in texts):
                if kind == 'generated-acronym':
                    pattern = r'\b' + r'\.?\s*'.join(term.upper()) + r'\.?\b'
                    if not re.search(pattern, p['raw']):
                        continue
                yield position, kind
        compact = ''.join(words)
        if len(words) < 2 or len(compact) < 10 or kind == 'generated-acronym':
            return
        if level >= 4:
            for position in self.compact_prefix.get(compact[:4], set()):
                if compact in self.passages[position]['compact']:
                    yield position, 'ocr-compact'
        if level >= 5:
            folded = ocr_fold(compact)
            for position in self.folded_prefix.get(folded[:4], set()):
                if folded in self.passages[position]['folded']:
                    yield position, 'ocr-confusable'
        if level >= 6:
            for i, word in enumerate(words):
                if len(word) < 6:
                    continue
                # Require all other name tokens exactly, preserving order in the final phrase.
                anchors = [self.tokens.get(w, set()) for j, w in enumerate(words) if j != i]
                candidates = set.intersection(*map(set, anchors)) if anchors else set()
                if not candidates:
                    continue
                vocabulary = set().union(*(self.vocabulary.get((part, fragment, n), set())
                                           for part, fragment in [('prefix', word[:2]), ('suffix', word[-2:])]
                                           for n in range(len(word) - 1, len(word) + 2)))
                for alternate in vocabulary:
                    if alternate == word or not one_edit(word, alternate):
                        continue
                    phrase = ' '.join(words[:i] + [alternate] + words[i + 1:])
                    for position in candidates & self.tokens[alternate]:
                        if f' {phrase} ' in f" {self.passages[position]['joined']} ":
                            yield position, 'single-edit-with-anchor'

def canonical_map(records, equivalences, sources):
    mapping = {}
    for row in equivalences:
        a, b = row['fromId'], row['toId']
        if a not in records or b not in records or records[a]['kind'] != records[b]['kind']:
            raise ValueError('Equivalence endpoints must be existing identities of the same kind')
        if not row.get('reason') or not row.get('citations'):
            raise ValueError('Approved equivalences require a reason and citations')
        if a in mapping and mapping[a] != b:
            raise ValueError(f'Conflicting equivalences for {a}')
        for c in row['citations']:
            if c['sourceId'] not in sources or not c.get('pages') or any(
                not isinstance(p, int) or isinstance(p, bool) or not 0 < p <= sources[c['sourceId']]['pageCount']
                for p in c['pages']
            ):
                raise ValueError('Invalid equivalence citation')
        mapping[a] = b
    result = {}
    for id in records:
        seen, current = set(), id
        while current in mapping:
            if current in seen:
                raise ValueError('Cyclic equivalences')
            seen.add(current)
            current = mapping[current]
        result[id] = current
    return result

def reference_id(identity, p):
    return digest([identity, p['sourceId'], p['page'], p['paragraph'], p['textHash']])[:24]

def run_pass(archive, corpus, state, aliases, equivalences, decisions):
    records = {r['id']: r for r in archive['people'] + archive['organizations']}
    sources = {s['id']: s for s in archive['sources']}
    if not records or not sources:
        raise ValueError('Seed identities and registered sources are required; this tool does not discover unnamed entities')
    if len(records) != len(archive['people']) + len(archive['organizations']) or len(sources) != len(archive['sources']):
        raise ValueError('Duplicate identity or source IDs must be resolved explicitly')
    canonical = canonical_map(records, equivalences, sources)
    if set(aliases) - set(records):
        raise ValueError('Alias file references unknown identities')
    if any(not isinstance(v, list) or any(not isinstance(a, str) or len(normalize(a)) < 2 for a in v) for v in aliases.values()):
        raise ValueError('Aliases must be arrays of nonempty candidate names')
    revision = digest(dict(version=VERSION, engineHash=ENGINE_HASH, rules=RULES, identities=[
        {k: r.get(k) for k in ['id', 'name', 'kind', 'aliases']} for r in records.values()
    ], sources=archive['sources'], pageHashes=corpus.page_hashes, aliases=aliases, equivalences=equivalences))
    if state.get('revision') != revision:
        state['revision'] = revision
        state['level'] = 0
        state['quietPasses'] = 0
    level = min(state.get('level', 0) + 1, len(RULES))
    references = state.setdefault('references', {})
    # Re-key only explicitly approved identity equivalences, preserving original identity provenance.
    merged = {}
    for old in references.values():
        groups = defaultdict(list)
        for original in old['identityIds']:
            groups[canonical.get(original, original)].append(original)
        for identity, originals in groups.items():
            r = dict(old)
            key = reference_id(identity, r)
            r['entityId'] = identity
            r['identityIds'] = sorted(originals)
            if key in merged:
                r['identityIds'] = sorted(set(r['identityIds'] + merged[key]['identityIds']))
                r['rules'] = sorted(set(r['rules'] + merged[key]['rules']))
            merged[key] = r
    deduplicated = max(0, len(references) - len(merged))
    split = max(0, len(merged) - len(references))
    references = state['references'] = merged
    for r in references.values():
        r['currentRules'] = []
        r['currentIdentityIds'] = []
    new_ids = []
    current_keys = set()
    for record in records.values():
        for term, kind, threshold in variants(record, aliases.get(record['id'], [])):
            if threshold > level:
                continue
            for position, rule in corpus.matches(term, kind, level):
                passage = corpus.passages[position]
                key = reference_id(canonical[record['id']], passage)
                current_keys.add(key)
                if key not in references:
                    references[key] = {k: passage[k] for k in ['sourceId', 'page', 'paragraph', 'textHash']}
                    references[key].update(entityId=canonical[record['id']], identityIds=[], rules=[], currentRules=[], currentIdentityIds=[],
                                           snippet=' '.join(passage['raw'].split())[:320], firstPass=len(state.get('passes', [])) + 1)
                    new_ids.append(key)
                r = references[key]
                r['identityIds'] = sorted(set(r['identityIds'] + [record['id']]))
                r['rules'] = sorted(set(r['rules'] + [rule]))
                r['currentRules'] = sorted(set(r['currentRules'] + [rule]))
                r['currentIdentityIds'] = sorted(set(r['currentIdentityIds'] + [record['id']]))
    # Narrowing inputs does not erase historical candidates; only current matches count as active.
    for key, r in references.items():
        r['active'] = key in current_keys
        r['evidenceHash'] = digest([r['entityId'], r['sourceId'], r['page'], r['paragraph'], r['textHash'], r['currentIdentityIds'], r['currentRules']])
    state['level'] = level
    state['quietPasses'] = state.get('quietPasses', 0) + 1 if level == len(RULES) and not new_ids else 0
    saturated = level == len(RULES) and state['quietPasses'] >= 2
    active = {k: r for k, r in references.items() if r['active']}
    pending = unresolved = 0
    for key in active:
        decision = decisions.get(key)
        if not decision:
            pending += 1
        elif decision.get('status') not in {'accepted', 'rejected', 'unresolved'} or not decision.get('reason'):
            raise ValueError(f'Invalid review decision for {key}')
        elif decision.get('evidenceHash') != active[key]['evidenceHash']:
            pending += 1
        elif decision['status'] == 'unresolved':
            unresolved += 1
    report = dict(passNumber=len(state.get('passes', [])) + 1, revision=revision, ruleLevel=level,
                  rules=RULES[:level], newReferences=len(new_ids), newReferenceIds=new_ids,
                  activeReferences=len(active), deduplicatedReferences=deduplicated, splitReferences=split, quietPasses=state['quietPasses'], searchSaturated=saturated,
                  pendingReview=pending, unresolved=unresolved,
                  reviewComplete=saturated and pending == 0 and unresolved == 0,
                  timestamp=datetime.now(timezone.utc).isoformat())
    state.setdefault('passes', []).append(report)
    return report

def atomic_write(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--pages-dir', type=Path, required=True)
    parser.add_argument('--state-dir', type=Path, required=True)
    parser.add_argument('--aliases', type=Path)
    parser.add_argument('--equivalences', type=Path)
    parser.add_argument('--decisions', type=Path)
    parser.add_argument('--until-stable', action='store_true')
    parser.add_argument('--max-passes', type=int, default=12)
    args = parser.parse_args()
    if args.max_passes < 1:
        parser.error('--max-passes must be positive')
    archive = json.loads(args.archive.read_text())
    aliases = json.loads(args.aliases.read_text()) if args.aliases else {}
    equivalences = json.loads(args.equivalences.read_text()) if args.equivalences else []
    decisions = json.loads(args.decisions.read_text()) if args.decisions else {}
    args.state_dir.mkdir(parents=True, exist_ok=True)
    lock = (args.state_dir / 'run.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('Another iteration is running in this state directory.')
    path = args.state_dir / 'state.json'
    state = json.loads(path.read_text()) if path.exists() else {}
    corpus = Corpus(archive, args.pages_dir)
    for _ in range(args.max_passes if args.until_stable else 1):
        report = run_pass(archive, corpus, state, aliases, equivalences, decisions)
        atomic_write(path, state)
        public = {k: v for k, v in report.items() if k != 'newReferenceIds'}
        public.update(passHistory=[{k: p[k] for k in ('passNumber', 'ruleLevel', 'newReferences', 'quietPasses', 'searchSaturated')} for p in state['passes'] if p['revision'] == report['revision']], engineVersion=VERSION, engineHash=ENGINE_HASH, entitiesScreened=len(archive['people']) + len(archive['organizations']),
                      sourcesScreened=len(archive['sources']), pagesScreened=sum(s['pageCount'] for s in archive['sources']),
                      limitation='Two quiet passes establish saturation under these inputs and rules, not exhaustive historical indexing. Candidate passages still require evidence review.')
        atomic_write(args.state_dir / 'report.json', public)
        queue = [{**r, 'referenceId': key, 'decision': decisions.get(key)} for key, r in state['references'].items() if r['active']]
        atomic_write(args.state_dir / 'review-queue.json', queue)
        print(f"Pass {report['passNumber']} · rules {report['ruleLevel']}/{len(RULES)} · new {report['newReferences']} · quiet {report['quietPasses']}/2 · pending {report['pendingReview']} · saturated {report['searchSaturated']}", flush=True)
        if not args.until_stable or report['searchSaturated']:
            break
    if args.until_stable and not report['searchSaturated']:
        raise SystemExit('Pass limit reached without saturation; resume with the same state directory. No completion certified.')

if __name__ == '__main__':
    main()
