"""Build a local, offline study archive from read-only Chrome DOM captures."""
import base64
import hashlib
import html
import json
import mimetypes
import re
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from xml.etree import ElementTree

from bs4 import BeautifulSoup, Comment
from latex2mathml.converter import convert
from markdownify import markdownify

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[2]
OUT = WORKSPACE / 'output' / 'pdf'
OUT.mkdir(parents=True, exist_ok=True)
(ROOT / 'conversations').mkdir(exist_ok=True)
(ROOT / 'assets').mkdir(exist_ok=True)
scope = json.loads((ROOT / 'scope.json').read_text(encoding='utf-8'))
latest_update = json.loads((ROOT / 'latest-update.json').read_text(encoding='utf-8')) if (ROOT / 'latest-update.json').exists() else None
bundled_assets = json.loads((ROOT / 'bundled-assets.json').read_text(encoding='utf-8')) if (ROOT / 'bundled-assets.json').exists() else {}
export_date = (latest_update or {}).get('date', (latest_update or {}).get('at', '2026-09-29')[:10])
date_label = date.fromisoformat(export_date).strftime('%d %B %Y').lstrip('0')
records = sorted([json.loads(p.read_text(encoding='utf-8')) for p in (ROOT / 'raw').glob('*.json') if p.stem.isdigit()], key=lambda d: d['ordinal'])
captured = {d['ordinal'] for d in records}
update_status = {r['ordinal']: r for r in (latest_update or {}).get('records', [])}
missing = [dict(ordinal=i+1, title=t['title'].removesuffix(' - Google Search'), url=t['url'], reason='The conversation could not be loaded for capture.' if i+1 in update_status else 'The original tab was unreadable during the earlier export.') for i,t in enumerate(scope['tabs']) if i+1 not in captured]
issues = []
media_gaps = []
media_status = json.loads((ROOT / 'media-status.json').read_text(encoding='utf-8')) if (ROOT / 'media-status.json').exists() else {}
pending_urls = {(x['conversation'], x['url']) for x in media_status.get('pendingImages', [])}
math_total = 0
image_total = 0

CSS = '''
@page { size:A4; margin:18mm 17mm 19mm; @bottom-left { content:"BookNook | Google AI Mode | 29 Sep 2026"; font:8pt Arial; color:#64706c; } @bottom-right {content:counter(page); font:8pt Arial; color:#64706c;} }
* {box-sizing:border-box} body{font:10pt/1.55 Arial,"Segoe UI",sans-serif;color:#202c28;margin:0;background:white}
main{max-width:900px;margin:30px auto;padding:0 28px} h1{font:25pt/1.18 Georgia,serif;color:#174b40;margin:10px 0 18px;overflow-wrap:anywhere}
h2{font-size:15pt;line-height:1.3;color:#174b40;margin:22px 0 10px} h3,h4,[role=heading]{font-weight:700;line-height:1.4;margin:16px 0 8px;break-after:avoid}
.eyebrow{font-size:9pt;font-weight:bold;letter-spacing:.13em;text-transform:uppercase;color:#60756b}.meta{font-size:9pt;color:#66746e}.cover{padding:24px 0}.cover p{max-width:650px}
.chapter{break-before:page}.chapterhead{border-bottom:2px solid #b5c9bf;padding-bottom:14px;margin-bottom:20px}.chapterhead h1{font-size:21pt}
.turn{margin-top:22px}.role{font-size:9pt;letter-spacing:.08em;text-transform:uppercase;font-weight:bold;color:#175b49;border-top:1px solid #c5d5cd;padding-top:12px;margin-bottom:10px;break-after:avoid}
.prompt{background:#eef3ef;padding:12px 15px;border-left:3px solid #708d7c;white-space:pre-wrap;overflow-wrap:anywhere;break-inside:avoid}
p,li{orphans:3;widows:3} ul,ol{padding-left:22px} li{margin:5px 0} a{color:#265e68;text-decoration:underline;overflow-wrap:anywhere}
table{width:100%;border-collapse:collapse;table-layout:fixed;margin:12px 0;font-size:9pt} th,td{border:1px solid #c6d1cb;padding:7px;vertical-align:top;overflow-wrap:anywhere} tr{break-inside:avoid} thead{display:table-header-group}
pre{font:8pt/1.4 Consolas,"Courier New",monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#f0f3f2;padding:12px;border:1px solid #d4ded8;max-width:100%} code{font-family:Consolas,"Courier New",monospace}
img{max-width:100%;max-height:220mm;object-fit:contain;height:auto;break-inside:avoid} .content img{display:inline-block;margin:8px 5px;vertical-align:middle} svg{max-width:100%} figure{margin:16px 0;break-inside:avoid}
math{font-family:"Cambria Math",serif;font-size:1.04em} .equation{display:inline-block;vertical-align:middle;max-width:100%}.equation.block{display:block;margin:12px 0;text-align:center;break-inside:avoid}.math-fallback{font:9pt Consolas;white-space:pre-wrap}
.sources{font-size:8.5pt;margin-top:18px;padding-top:7px;border-top:1px dotted #c6d1cb}.sources li{margin:4px 0}.sourceurl{font-size:8pt;color:#526b65}mark{background:#edf3da;color:inherit}
.citation-inline,.citation-inline div{display:inline;font-size:8pt;color:#64756d}.content img.source-icon{width:14px;height:14px;margin:0 3px;vertical-align:middle}
.toc li{margin:7px 0;break-inside:avoid}.toc a{color:#174b40}.notice{background:#f5f3e9;border-left:3px solid #aaa174;padding:12px}.pagebreak{break-before:page}.content div{max-width:100%}hr{border:0;border-top:1px solid #d2dbd6;margin:16px 0}
@media print { main{max-width:none;margin:0;padding:0}.screenonly{display:none}a{text-decoration:none}.cover{padding-top:20mm} }
'''
CSS = CSS.replace('29 Sep 2026', date.fromisoformat(export_date).strftime('%d %b %Y').lstrip('0'))

def esc(s): return html.escape(str(s), quote=True)
def write_aggregate(path, text):
    # Keep the previous large artifact intact if Windows temporarily locks it.
    temporary = path.with_name(path.name + '.building')
    temporary.write_text(text, encoding='utf-8')
    for attempt in range(10):
        try:
            temporary.replace(path)
            break
        except OSError:
            if attempt == 9:
                raise
            time.sleep(1)

def page(title, body):
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\' data:; style-src \'unsafe-inline\'; font-src \'self\' data:"><title>'+esc(title)+'</title><style>'+CSS+'</style></head><body><main>'+body+'</main></body></html>'

def clean_message(item, ordinal, index):
    global math_total, image_total
    markup = ''.join(item['htmlChunks']) if item.get('htmlChunks') else item['html']
    if '[Truncated]' in markup:
        raise ValueError(f'Truncated response markup: conversation {ordinal}, message {index}')
    soup = BeautifulSoup(markup, 'html.parser')
    # Google hosts some rendered diagrams in separate embedded frames. Preserve
    # their observed SVG content alongside the corresponding response.
    for widget in item.get('widgets', []):
        asset = ROOT / widget['path']
        if asset.suffix == '.svg':
            ElementTree.fromstring(asset.read_bytes())
        mime = mimetypes.guess_type(asset.name)[0] or 'application/octet-stream'
        figure = soup.new_tag('figure')
        figure.append(soup.new_tag('img', attrs={
            'src': 'data:' + mime + ';base64,' + base64.b64encode(asset.read_bytes()).decode('ascii'),
            'alt': widget['caption']
        }))
        caption = soup.new_tag('figcaption')
        caption.string = widget['caption']
        figure.append(caption)
        if widget.get('displayedText'):
            state = soup.new_tag('p', attrs={'class': 'meta'})
            state.string = 'Recorded diagram labels and controls: ' + ' '.join(widget['displayedText'].split())
            figure.append(state)
        soup.append(figure)
    for note in item.get('widgetNotes', []):
        status = soup.new_tag('p', attrs={'class': 'meta'})
        status.string = note
        soup.append(status)
    # Live maps use short-lived blob tiles. Preserve a read-only raster capture
    # of the rendered map, including its attribution, for offline documents.
    for region in list(soup.select('[role="region"][aria-label^="Map of"]')):
        map_capture = ROOT / 'assets' / f'{ordinal:02d}-map.png'
        if not map_capture.exists() and ordinal == 101:
            map_capture = ROOT / 'assets' / '101-map-source-2.png'
        if map_capture.exists():
            figure = soup.new_tag('figure')
            figure.append(soup.new_tag('img', attrs={
                'src': 'data:image/png;base64,' + base64.b64encode(map_capture.read_bytes()).decode('ascii'),
                'alt': region.get('aria-label', 'Map from the source conversation')
            }))
            caption = soup.new_tag('figcaption')
            caption.string = 'Map from the source conversation (static archival capture). Map data ©2026 Google; original terms link retained in the source markup.'
            figure.append(caption)
            region.replace_with(figure)
    # Drop application controls and dialogs, while preserving all response prose.
    for x in soup.select('script,style,iframe,form,input,textarea,[role="dialog"],.DBd2Wb,saveai-chat-export-btn'):
        x.decompose()
    for c in soup.find_all(string=lambda x:isinstance(x, Comment)): c.extract()
    for x in soup.select('span.WBgIic'):
        x['class']=['citation-inline']
    for x in soup.select('img.IpiY3d'):
        x['class']=['source-icon']
    equations = [x for x in soup.select('[data-xpm-latex]') if not x.find_parent(attrs={'data-xpm-latex': True})]
    for latex in equations:
        # Some formulas are a span carrying the complete LaTeX plus many SVG
        # fragments. Prefer that complete expression over any fragment.
        x = latex.parent if latex.name == 'img' and latex.parent.has_attr('data-xpm-math-type') else latex
        tex = latex.get('data-xpm-latex','')
        # Google marks many inline symbols as "block"; their surrounding DOM
        # already supplies the intended paragraph/display layout.
        block = False
        if not tex.strip():
            x.replace_with(soup.new_string(' '))
            continue
        try:
            m = BeautifulSoup(convert(tex), 'html.parser')
            wrap = soup.new_tag('span', attrs={'class':'equation'+(' block' if block else ''),'title':tex})
            wrap.append(m)
            x.replace_with(wrap)
            math_total += 1
        except Exception as e:
            issues.append({'conversation':ordinal,'message':index,'type':'math_fallback','latex':tex,'error':str(e)})
            wrap=soup.new_tag('code',attrs={'class':'math-fallback'});wrap.string=tex;x.replace_with(wrap)
    # Supplementary accessibility MathML duplicates the rendered math above.
    for x in list(soup.find_all('div',style=True)):
        if x.parent is not None and 'opacity: 0.001' in x.get('style',''): x.decompose()
    for x in list(soup.find_all('svg')):
        if not x.get('aria-label') and not x.find('title'): x.decompose()
    for x in list(soup.find_all('li')):
        if not x.get_text(strip=True) and not x.find(['img','math','svg']): x.decompose()
    for x in list(soup.find_all('button')):
        text=x.get_text(' ',strip=True)
        if not text or re.match(r'^(Copy|Copied|Show .*code block|About this result|Good response|Bad response|Share|SaveAI|Related results|Show all related results)$',text):x.decompose()
        else:x.unwrap()
    for x in list(soup.find_all('img')):
        src=x.get('src','')
        absolute_src = 'https:' + src if src.startswith('//') else src
        if absolute_src in bundled_assets:
            asset = ROOT / bundled_assets[absolute_src]
            mime = mimetypes.guess_type(asset.name)[0] or 'application/octet-stream'
            src = 'data:' + mime + ';base64,' + base64.b64encode(asset.read_bytes()).decode('ascii')
            x['src'] = src
        if src.startswith('data:image/gif') or 'favicon' in src or not src:
            x.decompose();continue
        if src.startswith('data:'):
            try:
                header,data=src.split(',',1)
                b=base64.b64decode(data) if ';base64' in header else data.encode()
                ext={'image/png':'png','image/jpeg':'jpg','image/webp':'webp','image/svg+xml':'svg','image/gif':'gif'}.get(header[5:].split(';')[0],'bin')
                filename=hashlib.sha256(b).hexdigest()[:20]+'.'+ext
                (ROOT/'assets'/filename).write_bytes(b)
                image_total+=1
            except Exception as e: issues.append({'conversation':ordinal,'message':index,'type':'image_decode','error':str(e)})
        else:
            record={'conversation':ordinal,'message':index,'type':'unbundled_image','url':src}
            if (ordinal,src) in pending_urls:
                media_gaps.append(record)
                x.replace_with(soup.new_string('[Image capture pending; original source URL preserved in the raw archive.]'))
            else:
                issues.append(record)
                x.replace_with(soup.new_string('[Image: '+x.get('alt',src)+']'))
    for x in soup.find_all(True):
        is_math = x.name == 'math' or x.find_parent('math') is not None
        keep={'href','src','alt','title','colspan','rowspan','role','aria-level'}
        if is_math: keep|={'xmlns','display','mathvariant','stretchy','fence','separator','accent','accentunder','columnalign','columnspacing','rowspacing','notation','linethickness','encoding'}
        if set(x.get('class',[])) & {'equation','math-fallback','citation-inline','source-icon'}: keep.add('class')
        for k in list(x.attrs):
            if k not in keep: del x.attrs[k]
        if x.name=='a' and not x.get('href','').startswith(('https://','http://','#')): x.attrs.pop('href',None)
        if x.get('role')=='heading':
            x.name='h'+str(min(4,max(3,int(x.get('aria-level','3')))))
            x.attrs.pop('role',None);x.attrs.pop('aria-level',None)
    return str(soup)

chapters=[]; toc=[]; manifest=[]; all_md=[]
for d in records:
    n=d['ordinal'];title=d['title'].removesuffix(' - Google Search')
    if len(title)>250:title=title[:220].rsplit(' ',1)[0]+'…'
    slug=re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')[:80] or 'conversation'
    basename=f'{n:02d}-{slug}'
    chunks=[];md=[f'# {title}\n',f'Captured: {d["capturedAt"]}\n',f'Source: {d.get("originalUrl",d["url"])}\n']
    prompt_count=0;response_count=0
    for j,item in enumerate(d['items'],1):
        if item['role']=='user':
            prompt_count+=1;label=f'Prompt {prompt_count} · You';txt=item['text'];txt=txt.removeprefix('You said: ')
            body='<div class="prompt">'+esc(txt)+'</div>'; md.append(f'## Prompt {prompt_count} — You\n\n{txt}\n')
            for note in item.get('attachmentNotes', []):
                body += '<p class="meta">'+esc(note)+'</p>'
                md.append('Attachment availability: '+note+'\n')
        else:
            response_count+=1;label=f'Response {response_count} · Google AI Mode';clean=clean_message(item,n,j)
            body='<div class="content">'+clean+'</div>'
            md_soup=BeautifulSoup(clean,'html.parser')
            for eq in list(md_soup.select('.equation')):eq.replace_with(' $'+eq.get('title','')+'$ ')
            md.append(f'## Response {response_count} — Google AI Mode\n\n'+markdownify(str(md_soup),heading_style='ATX')+'\n')
            links={a['url']:a['text'] for a in item['links'] if a['url'].startswith(('http://','https://')) and 'support.google.com/websearch' not in a['url'] and 'policies.google.com/' not in a['url'] and 'support.google.com/legal/' not in a['url'] and not a['url'].startswith('https://www.google.com/search')}
            if links:
                body+='<div class="sources"><strong>Source links preserved from this response</strong><ol>'+''.join('<li><a href="'+esc(u)+'">'+esc(t or urlparse(u).netloc)+'</a><br><span class="sourceurl">'+esc(u)+'</span></li>' for u,t in links.items())+'</ol></div>'
                md.append('### Source links\n\n'+'\n'.join('- ['+(t or urlparse(u).netloc).replace(']','\\]')+']('+u+')' for u,t in links.items())+'\n')
        chunks.append('<section class="turn"><div class="role">'+esc(label)+'</div>'+body+'</section>')
    head='<header class="chapterhead"><div class="eyebrow">Conversation '+str(n).zfill(2)+'</div><h1>'+esc(title)+'</h1><p class="meta">'+str(prompt_count)+' prompts · '+str(response_count)+' responses · Captured '+esc(d['capturedAt'])+'</p><p><a href="'+esc(d.get('originalUrl',d['url']))+'">Open the original Google AI Mode conversation</a></p></header>'
    chapter='<article class="chapter" id="conversation-'+str(n)+'">'+head+''.join(chunks)+'</article>'
    (ROOT/'conversations'/(basename+'.html')).write_text(page(title,chapter),encoding='utf-8')
    (ROOT/'conversations'/(basename+'.md')).write_text('\n'.join(md),encoding='utf-8')
    chapters.append(chapter);all_md.append('\n'.join(md))
    toc.append('<li><a href="#conversation-'+str(n)+'">'+esc(title)+'</a><span class="meta"> — '+str(prompt_count)+' exchanges</span></li>')
    manifest.append({'ordinal':n,'title':title,'prompts':prompt_count,'responses':response_count,'html':'conversations/'+basename+'.html','markdown':'conversations/'+basename+'.md','source':d.get('originalUrl',d['url']),'recoveredFromSavedUrl':d.get('recoveredFromSavedUrl',False)})

missing_html='<ul>'+''.join('<li><strong>'+str(m['ordinal']).zfill(2)+'. '+esc(m['title'])+'</strong><br>'+esc(m['reason'])+'</li>' for m in missing)+'</ul>' if missing else '<p>All scoped conversation transcripts were captured.</p>'
if media_status:
    missing_html += '<p><strong>Media availability.</strong> '+esc(media_status.get('note',''))+' Gaps are marked in context; original URLs and source markup are retained. See media-status.json for details.</p>'
update_note = '<p class="meta">Last updated: '+esc(latest_update['at'])+'. New conversations are appended after the existing collection.</p>' if latest_update else ''
cover='<section class="cover"><div class="eyebrow">BookNook / Personal study archive</div><h1>Google AI Mode<br>Conversations & doodles</h1><p class="meta">'+esc(date_label)+'</p>'+update_note+'<p>'+str(len(records))+' conversations captured from '+str(len(scope['tabs']))+' conversations in the archive scope. '+str(sum(d['counts']['prompts'] for d in records))+' prompts and '+str(sum(d['counts']['responses'] for d in records))+' responses.</p><p>This is an archival transcript. User prompts and Google AI Mode responses are labeled separately. Wording is preserved; layout is adapted for reading. Google responses are reproduced as source material, without independent validation.</p><p>Equations retain their source LaTeX in the editable archive and are rendered in the PDF. Embedded images, text diagrams, tables, and available source links are included. Linked external pages and videos are references, not full copies of those external works.</p><div class="notice"><strong>Coverage record</strong>'+missing_html+'</div><p class="meta">The initial scope is retained and extended with new conversations on each update. Captures use loaded conversation pages. On 8 October 2026, the user authorized reopening saved URLs to recover stalled tabs. Earlier and current raw captures retain their capture times and recovery provenance.</p></section>'
book=cover+'<section class="pagebreak"><div class="eyebrow">Contents</div><h1>Conversation index</h1><ol class="toc">'+''.join(toc)+'</ol></section>'+''.join(chapters)
write_aggregate(ROOT/'book.html', page('BookNook - Google AI Mode archive',book))
write_aggregate(ROOT/'all-conversations.md', '# BookNook Google AI Mode archive\n\n'+'\n\n---\n\n'.join(all_md))
index=cover+'<h2>Open a conversation</h2><ol class="toc">'+''.join('<li><a href="'+esc(m['html'])+'">'+esc(m['title'])+'</a> · <a href="'+esc(m['markdown'])+'">Markdown</a></li>' for m in manifest)+'</ol>'
(ROOT/'index.html').write_text(page('BookNook archive index',index),encoding='utf-8')
report={'exportDate':export_date,'scopeCount':len(scope['tabs']),'capturedCount':len(records),'prompts':sum(d['counts']['prompts'] for d in records),'responses':sum(d['counts']['responses'] for d in records),'mathRendered':math_total,'embeddedImages':image_total,'conversations':manifest,'missing':missing,'issues':issues,'mediaGaps':media_gaps,'mediaStatus':media_status}
if latest_update: report['latestUpdate'] = latest_update
(ROOT/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'README.md').write_text('# BookNook Google AI Mode archive\n\nUpdated '+date_label+'.\n\n- Open `index.html` to browse individual HTML and Markdown transcripts.\n- `book.html` is the complete typeset source for the combined PDF.\n- `raw/` contains original message markup, readable text, equations, links, and DOM snapshots.\n- `assets/` contains embedded image copies.\n- `manifest.json` records capture coverage, provenance, and conversion issues.\n\n## Missing conversations\n\n'+('\n'.join(f'- {m["ordinal"]:02d}. {m["title"]}: {m["reason"]}' for m in missing) or 'None.')+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['conversations','issues','latestUpdate','missing','mediaGaps','mediaStatus']},ensure_ascii=True,indent=2))
print('Conversion issues:',len(issues))
