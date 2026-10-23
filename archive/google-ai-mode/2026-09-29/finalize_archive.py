from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, DictionaryObject, ArrayObject, TextStringObject, NumberObject, BooleanObject
import bisect, hashlib, json, re, zipfile

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
writer.add_metadata({'/Title':'BookNook - Google AI Mode Conversations & Doodles - '+export_date,'/Author':'BookNook personal archive','/Subject':f"{manifest['capturedCount']} of {manifest['scopeCount']} scoped conversations; {prompts} prompts and {responses} responses"})
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
pdf_parts=[]
if pdf.stat().st_size > 95*1024*1024:
    # Keep the combined local PDF and publish complete chapter-aligned volumes.
    boundaries=[0]
    for c in manifest['conversations']:
        start=starts[c['ordinal']]
        if start-boundaries[-1]>=800: boundaries.append(start)
    boundaries.append(len(reader.pages))
    # Keep cross-volume index links without importing every linked chapter
    # into the first volume. The combined PDF retains internal destinations.
    page_ids={page.indirect_reference.idnum:n for n,page in enumerate(reader.pages)}
    volume_index_links=0
    for page in reader.pages[:starts[1]]:
        for ref in page.get('/Annots',[]):
            annotation=ref.get_object()
            if not annotation.get('/Dest'):continue
            target=page_ids[annotation['/Dest'][0].idnum]
            destination_volume=bisect.bisect_right(boundaries,target)-1
            annotation.pop('/Dest')
            annotation[NameObject('/A')]=DictionaryObject({
                NameObject('/S'):NameObject('/GoToR'),
                NameObject('/F'):TextStringObject(filename+f'-volume-{destination_volume+1:02d}.pdf'),
                NameObject('/D'):ArrayObject([NumberObject(target-boundaries[destination_volume]),NameObject('/Fit')]),
                NameObject('/NewWindow'):BooleanObject(False),
            })
            volume_index_links+=1
    manifest['pdf']['volumeIndexRemoteLinks']=volume_index_links
    for i,(start,end) in enumerate(zip(boundaries,boundaries[1:]),1):
        volume=PdfWriter()
        for page in reader.pages[start:end]:volume.add_page(page)
        if start==0:
            volume.add_outline_item('Archive coverage',0)
            volume.add_outline_item('Conversation index',index_page)
        for c in manifest['conversations']:
            if start<=starts[c['ordinal']]<end:volume.add_outline_item(f"{c['ordinal']:02d}. {c['title']}",starts[c['ordinal']]-start)
        part=pdf.with_name(filename+f'-volume-{i:02d}.pdf')
        with part.open('wb') as f:volume.write(f)
        assert part.stat().st_size<100*1024*1024
        pdf_parts.append(part)
    manifest['pdf']['volumes']=[dict(path=str(p.relative_to(workspace)).replace('\\','/'),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),firstPage=boundaries[i]+1,lastPage=boundaries[i+1]) for i,p in enumerate(pdf_parts)]
(root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
# Retain only task artifacts in the portable package.
zip_path=workspace/'output'/(filename+'.zip')
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for path in sorted(root.rglob('*')):
        # Per-conversation Markdown is included. Omit its large duplicate
        # concatenation from the ZIP; it remains available in the repository.
        if path.is_file() and path.name not in ['13.assets.json','media-needs.json','all-conversations.md'] and '__pycache__' not in path.parts:
            z.write(path,'archive/'+str(path.relative_to(root)).replace('\\','/'))
    for document in pdf_parts or [pdf]:z.write(document,document.name)
with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None
zip_parts=[]
if zip_path.stat().st_size > 95*1024*1024:
    # Each volume is an ordinary ZIP. Extract all into the same directory.
    with zipfile.ZipFile(zip_path) as source:
        volume=None;used=0
        try:
            for member in source.infolist():
                estimate=member.compress_size+len(member.filename.encode('utf8'))*2+256
                if volume is None or used+estimate>90*1024*1024:
                    if volume:volume.close()
                    part=zip_path.with_name(filename+f'-part-{len(zip_parts)+1:02d}.zip')
                    zip_parts.append(part)
                    volume=zipfile.ZipFile(part,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)
                    used=0
                volume.writestr(member.filename,source.read(member))
                used+=estimate
        finally:
            if volume:volume.close()
    for part in zip_parts:
        assert part.stat().st_size < 100*1024*1024
        with zipfile.ZipFile(part) as z:assert z.testzip() is None
archive_links='- [Portable archive ZIP](output/'+filename+'.zip)\n'
if zip_parts:
    archive_links='- Portable archive volumes (extract all into one directory): '+', '.join('[Part '+str(i+1)+'](output/'+part.name+')' for i,part in enumerate(zip_parts))+'.\n'
pdf_links='- [Combined PDF](output/pdf/'+filename+'.pdf)\n'
if pdf_parts:pdf_links='- Complete PDF in volumes: '+', '.join('[Volume '+str(i+1)+'](output/pdf/'+p.name+')' for i,p in enumerate(pdf_parts))+'. Read in order; every page is included.\n'
(workspace/'README.md').write_text(
    '# BookNook\n\nGoogle AI Mode archive updated '+export_date+'.\n\n'
    +pdf_links+
    '- [Browse HTML and Markdown transcripts](archive/google-ai-mode/2026-09-29/index.html)\n'
    +archive_links+
    '- [Capture manifest](archive/google-ai-mode/2026-09-29/manifest.json)\n\n'
    'Coverage: '+str(manifest['capturedCount'])+' of '+str(manifest['scopeCount'])+' conversations in the cumulative archive, '
    +str(prompts)+' prompts and '+str(responses)+' responses. '+str(len(manifest['missing']))+' missing conversations are recorded in the manifest and PDF.\n\n'
    +'The PDF and [media status](archive/google-ai-mode/2026-09-29/media-status.json) identify source gaps. '+manifest.get('mediaStatus',{}).get('note','')+'\n', encoding='utf-8')

print(json.dumps({'pdfPages':len(reader.pages),'pdfBytes':pdf.stat().st_size,'verifiedPrompts':prompts,'verifiedResponses':responses,'bookmarks':len(manifest['conversations'])+2,'zipBytes':zip_path.stat().st_size,'chapterPages':starts},indent=2))
