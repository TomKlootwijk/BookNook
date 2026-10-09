"""Merge an incremental Chrome intake while retaining previous complete captures."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from xml.etree import ElementTree
import argparse, json, re

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--batch', required=True)
args = parser.parse_args()
assert re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}[a-z0-9-]*', args.batch)
intake = WORKSPACE / 'tmp' / ('intake-' + args.batch)
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
def query(tab):
    return parse_qs(urlparse(tab['url']).query)
def identity(tab):
    q = query(tab)
    return (q.get('mtid') or q.get('q') or [tab.get('title', '')])[0]
def clean_url(value):
    u = urlparse(value)
    q = parse_qs(u.query, keep_blank_values=True)
    q.pop('google_abuse', None)
    return urlunparse(u._replace(query=urlencode(q, doseq=True)))

def normalized_text(item):
    return re.sub(r'\s+', '', item.get('text', '').removeprefix('You said: ').replace('\u200b', ''))

scope = read(ROOT / 'scope.json')
inventory = read(intake / 'open-tabs.json')
results = {}
for r in read(intake / 'results.json'):
    if r['id'] not in results or r['status'] != 'error':
        results[r['id']] = r
positions = {identity(t): i+1 for i,t in enumerate(scope['tabs'])}
seen, changes = set(), []
new_ordinals = []
for t in inventory['tabs']:
    ident = identity(t)
    ordinal = positions.get(ident) or t.get('existingOrdinal')
    if not ordinal and len(t.get('queryMatchOrdinals', [])) == 1:
        ordinal = t['queryMatchOrdinals'][0]
    dedup = ('ordinal', ordinal) if ordinal else ('identity', ident)
    if dedup in seen:
        continue
    seen.add(dedup)
    r = results.get(t['id'], {})
    candidate = intake / (t['id'] + '.json')
    data = read(candidate) if candidate.exists() and r.get('status') == 'captured' else None
    if not ordinal:
        ordinal = len(scope['tabs']) + 1
        scope['tabs'].append({k:t[k] for k in ['id', 'title', 'url']})
        scope['tabs'][-1]['url'] = clean_url(t['url'])
        scope['tabs'][-1]['addedAt'] = inventory['at']
        positions[ident] = ordinal
    target = ROOT / 'raw' / f'{ordinal:02d}.json'
    old = read(target) if target.exists() else None
    record = dict(ordinal=ordinal, tabId=t['id'], title=t['title'])
    if data:
        assert data['counts']['prompts'] == data['counts']['responses'], t['id']
        assert not any('[Truncated]' in (i.get('html', '') + ''.join(i.get('htmlChunks', []))) for i in data['items'])
        data.update(ordinal=ordinal, url=clean_url(data['url']))
        if old:
            same_text = len(data['items']) == len(old['items']) and all(
                a['role'] == b['role'] and normalized_text(a) == normalized_text(b)
                for a,b in zip(data['items'], old['items']))
            media_added = any(any(a.get(k) and a.get(k) != b.get(k)
                for k in ['widgets','attachmentAudit','attachmentNotes'])
                for a,b in zip(data['items'],old['items']))
            if data['counts']['responses'] < old['counts']['responses'] or (same_text and not media_added):
                record.update(status='previous_capture_retained', counts=old['counts'])
                changes.append(record)
                continue
            write(ROOT / 'revisions' / f'{args.batch}-{ordinal:02d}-before.json', old)
            # Preserve already archived markup and diagrams on unchanged turns.
            for i,item in enumerate(data['items']):
                if i < len(old['items']) and item['role'] == old['items'][i]['role'] and normalized_text(item) == normalized_text(old['items'][i]):
                    saved = dict(old['items'][i])
                    for key in ['attachmentAudit','attachmentNotes']:
                        if item.get(key): saved[key] = item[key]
                    if item.get('widgets'):
                        saved['widgets'] = saved.get('widgets', []) + [w for w in item['widgets'] if w not in saved.get('widgets', [])]
                    data['items'][i] = saved
            record.update(status='updated', previousCounts=old['counts'])
        else:
            record['status'] = 'added'
            new_ordinals.append(ordinal)
        if t['id'] == '1037241492' and (intake / '1492-widgets.json').exists():
            widget_data = read(intake / '1492-widgets.json')
            for widget in widget_data:
                item = [i for i in data['items'] if i['role'] == 'google'][widget['response']-1]
                item['widgets'] = []
                for j,s in enumerate(widget['svgs'], 1):
                    markup = ''.join(s['chunks'])
                    ElementTree.fromstring(markup)
                    relative = f'assets/{ordinal:02d}-response-{widget["response"]}-chart-{j}.svg'
                    (ROOT / relative).write_text(markup, encoding='utf-8')
                    item['widgets'].append(dict(path=relative, caption=widget['text'].splitlines()[0] + ' — diagram captured from the original conversation.'))
            write(ROOT / 'assets/widgets' / f'{ordinal:02d}-{args.batch}.json', widget_data)
        write(target, data)
        record['counts'] = data['counts']
    elif old:
        record.update(status='unchanged' if r.get('status') == 'retained_existing' else 'previous_capture_retained_unreadable', counts=old['counts'])
        if record['status'].endswith('unreadable'):
            record['reason'] = 'The open tab could not be read in this batch; the previous complete capture is retained.'
    else:
        record.update(status='pending', reason='No readable capture was available.')
    changes.append(record)

at = datetime.now(timezone.utc).isoformat()
update = dict(at=at, date=args.batch[:10], batchId=args.batch,
              openAiModeTabs=inventory.get('openAiModeTabs', len(inventory['tabs'])),
              uniqueOpenConversations=inventory.get('uniqueOpenConversations', len(seen)),
              historyConversations=inventory.get('historyConversations', 0),
              method=inventory.get('method', 'Read-only DOM extraction from open Chrome tabs, with saved-URL recovery for new conversations.'),
              records=changes, newOrdinals=new_ordinals)
scope['updatedAt'] = at
write(ROOT / 'scope.json', scope)
write(ROOT / 'latest-update.json', update)
write(ROOT / 'updates' / (args.batch + '-results.json'), update)
clean_inventory = dict(at=inventory['at'], batchId=args.batch, tabs=[dict(id=t['id'], title=t['title'], url=clean_url(t['url'])) for t in inventory['tabs']])
write(ROOT / 'updates' / (args.batch + '-open-tabs.json'), clean_inventory)
print(json.dumps({'newOrdinals':new_ordinals, 'records':len(changes), 'statuses':{s:sum(c['status']==s for c in changes) for s in sorted({c['status'] for c in changes})}}, indent=2))
