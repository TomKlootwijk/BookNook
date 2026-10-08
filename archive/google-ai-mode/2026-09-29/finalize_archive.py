from pathlib import Path
from pypdf import PdfReader, PdfWriter
import hashlib, json, re, zipfile

root=Path(__file__).resolve().parent
workspace=root.parents[2]
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
export_date=manifest.get('exportDate','2026-09-29')
filename=f'BookNook-Google-AI-Mode-{export_date}'
pdf=workspace/'output/pdf'/(filename+'.pdf')
reader=PdfReader(pdf)
texts=[p.extract_text() for p in reader.pages]
starts={}
for i,t in enumerate(texts):
    m=re.search(r'CONVERSATION\s+(\d{2,})',t)
    if m:starts[int(m.group(1))]=i
assert len(starts)==manifest['capturedCount'],(len(starts),manifest['capturedCount'])
prompts=sum(len(re.findall(r'PROMPT\s+\d+\s*[·•]',t)) for t in texts)
responses=sum(len(re.findall(r'RESPONSE\s+\d+\s*[·•]',t)) for t in texts)
assert prompts==manifest['prompts'],(prompts,manifest['prompts'])
assert responses==manifest['responses'],(responses,manifest['responses'])
assert not manifest['issues'],manifest['issues']
writer=PdfWriter();writer.clone_document_from_reader(reader)
writer.add_metadata({'/Title':'BookNook - Google AI Mode Conversations & Doodles - '+export_date,'/Author':'BookNook personal archive','/Subject':f"{manifest['capturedCount']} of {manifest['scopeCount']} scoped conversations; {prompts} prompt/response pairs"})
writer.add_outline_item('Archive coverage',0)
index_page=next(i for i,t in enumerate(texts) if 'Conversation index' in t)
writer.add_outline_item('Conversation index',index_page)
for c in manifest['conversations']:
    writer.add_outline_item(f"{c['ordinal']:02d}. {c['title']}",starts[c['ordinal']])
    c['pdfPage']=starts[c['ordinal']]+1
temp=pdf.with_suffix('.bookmarked.pdf')
with temp.open('wb') as f:writer.write(f)
temp.replace(pdf)
manifest['pdf']={'path':str(pdf.relative_to(workspace)).replace('\\','/'),'pages':len(reader.pages),'bytes':pdf.stat().st_size,'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'promptMarkersVerified':prompts,'responseMarkersVerified':responses}
(root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
# Retain only task artifacts in the portable package.
zip_path=workspace/'output'/(filename+'.zip')
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for path in sorted(root.rglob('*')):
        # Per-conversation Markdown is included. Omit its large duplicate
        # concatenation from the ZIP; it remains available in the repository.
        if path.is_file() and path.name not in ['13.assets.json','media-needs.json','all-conversations.md'] and '__pycache__' not in path.parts:
            z.write(path,'archive/'+str(path.relative_to(root)).replace('\\','/'))
    z.write(pdf,filename+'.pdf')
with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None
(workspace/'README.md').write_text(
    '# BookNook\n\nGoogle AI Mode archive updated '+export_date+'.\n\n'
    '- [Combined PDF](output/pdf/'+filename+'.pdf)\n'
    '- [Browse HTML and Markdown transcripts](archive/google-ai-mode/2026-09-29/index.html)\n'
    '- [Portable archive ZIP](output/'+filename+'.zip)\n'
    '- [Capture manifest](archive/google-ai-mode/2026-09-29/manifest.json)\n\n'
    'Coverage: '+str(manifest['capturedCount'])+' of '+str(manifest['scopeCount'])+' conversations in the cumulative archive, '
    +str(prompts)+' prompt/response pairs. '+str(len(manifest['missing']))+' missing conversations are recorded in the manifest and PDF.\n', encoding='utf-8')

print(json.dumps({'pdfPages':len(reader.pages),'pdfBytes':pdf.stat().st_size,'verifiedPrompts':prompts,'verifiedResponses':responses,'bookmarks':len(manifest['conversations'])+2,'zipBytes':zip_path.stat().st_size,'chapterPages':starts},indent=2))
