"""Merge a captured tab intake without replacing longer archived conversations."""
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone
import json
import shutil

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[2]
DATE = '2026-10-08'
INTAKE = WORKSPACE / 'tmp' / ('intake-' + DATE)

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def key(tab):
    q = parse_qs(urlparse(tab['url']).query)
    return (q.get('mtid') or q.get('q') or [tab.get('title', '')])[0]

scope = read(ROOT / 'scope.json')
inventory = read(ROOT / 'updates' / (DATE + '-open-tabs.json'))
results = {r['id']: r for r in read(INTAKE / 'results.json')}
positions = {key(t): i for i, t in enumerate(scope['tabs'])}
seen = set()
changes = []
for tab in inventory['tabs']:
    identity = key(tab)
    if identity in seen:
        continue
    seen.add(identity)
    if identity not in positions:
        positions[identity] = len(scope['tabs'])
        scope['tabs'].append(dict(tab, addedAt=inventory['at']))
    ordinal = positions[identity] + 1
    target = ROOT / 'raw' / f'{ordinal:02d}.json'
    candidate = INTAKE / (tab['id'] + '.json')
    record = dict(ordinal=ordinal, tabId=tab['id'], title=tab['title'])
    if not candidate.exists() or not read(candidate)['counts']['responses']:
        result = results.get(tab['id'], {})
        record.update(status='previous_capture_retained' if target.exists() else 'pending',
                      reason=result.get('reason', result.get('error', 'Conversation content did not load.')))
        changes.append(record)
        continue
    data = read(candidate)
    data['ordinal'] = ordinal
    if data['title'] == 'Google Search' and data.get('conversationHeading'):
        data['title'] = data['conversationHeading'].removeprefix('AI Mode conversation: ')
    old = read(target) if target.exists() else None
    prior = ROOT / 'revisions' / (DATE + f'-{ordinal:02d}-before.json')
    if old:
        if old['counts']['prompts'] > data['counts']['prompts']:
            record.update(status='longer_previous_capture_retained', counts=old['counts'])
        elif [i['text'] for i in old['items']] == [i['text'] for i in data['items']]:
            record.update(status='unchanged', counts=old['counts'])
        else:
            if not prior.exists():
                write(prior, old)
            write(target, data)
            record.update(status='updated', counts=data['counts'], previousCounts=read(prior)['counts'])
    else:
        write(target, data)
        record.update(status='added', counts=data['counts'])
    record['recoveredFromSavedUrl'] = data.get('recoveredFromSavedUrl', False)
    snapshot = INTAKE / (tab['id'] + '.snapshot.txt')
    if snapshot.exists():
        shutil.copy2(snapshot, ROOT / 'raw' / f'{ordinal:02d}.snapshot.txt')
    changes.append(record)

at = datetime.now(timezone.utc).isoformat()
scope['updatedAt'] = at
write(ROOT / 'scope.json', scope)
update = dict(at=at, date=DATE, openAiModeTabs=len(inventory['tabs']),
              uniqueOpenConversations=len(seen),
              method='Read-only extraction, with saved-URL recovery authorized by the user on 8 October 2026.',
              records=changes)
write(ROOT / 'latest-update.json', update)
write(ROOT / 'updates' / (DATE + '-results.json'), update)
print(json.dumps({s: sum(c['status'] == s for c in changes) for s in sorted({c['status'] for c in changes})}, indent=2))
