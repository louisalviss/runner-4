from __future__ import annotations

import json, pathlib, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W,H,FPS = 1080,1920,30
WHITE=(248,248,246)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

# Source policy: no preference for official/licensed/stock. The only production
# criteria are song match, visual usefulness, quality, and technical usability.
TRACKS=[
    {'rank':10,'song':'Tsunami','artist':'DVBBS & Borgeous'},
    {'rank':9,'song':'Heroes (We Could Be)','artist':'Alesso ft. Tove Lo'},
    {'rank':8,'song':'The Nights','artist':'Avicii'},
    {'rank':7,'song':'Summer','artist':'Calvin Harris'},
    {'rank':6,'song':'Titanium','artist':'David Guetta ft. Sia'},
    {'rank':5,'song':'Animals','artist':'Martin Garrix'},
    {'rank':4,'song':"Don't You Worry Child",'artist':'Swedish House Mafia'},
    {'rank':3,'song':'Clarity','artist':'Zedd ft. Foxes'},
    {'rank':2,'song':'Wake Me Up','artist':'Avicii'},
    {'rank':1,'song':'Levels','artist':'Avicii'},
]

INTRO=2.2
REGULAR=5.1
ONE=6.4
OUTRO=5.0


def run(cmd:list[str],check=True):
    print('+',' '.join(cmd),flush=True)
    return subprocess.run(cmd,check=check)


def probe_duration(path:pathlib.Path)->float:
    return float(subprocess.check_output([
        'ffprobe','-v','error','-show_entries','format=duration',
        '-of','default=nw=1:nk=1',str(path)
    ],text=True).strip())


def has_audio(path:pathlib.Path)->bool:
    p=subprocess.check_output([
        'ffprobe','-v','error','-select_streams','a:0',
        '-show_entries','stream=codec_type','-of','csv=p=0',str(path)
    ],text=True).strip()
    return p=='audio'


def font(size:int,bold=False):
    return ImageFont.truetype(BOLD if bold else FONT,size)


def fit_text(draw:ImageDraw.ImageDraw,text:str,maxw:int,start:int,minsize:int,bold=True):
    for s in range(start,minsize-1,-2):
        f=font(s,bold)
        if draw.textbbox((0,0),text,font=f)[2] <= maxw:
            return f
    return font(minsize,bold)


def overlay_png(current_index:int|None,out:pathlib.Path,cta=False):
    im=Image.new('RGBA',(W,H),(0,0,0,0))
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,260),fill=(0,0,0,196))
    d.rectangle((0,1260,W,H),fill=(0,0,0,224))
    d.text((58,72),'TOP 10 NOSTALGIC',font=font(54,True),fill=WHITE)
    d.text((58,133),'EDM SONGS — 2010s',font=font(58,True),fill=WHITE)
    d.text((60,206),'the era that made festival EDM feel enormous',font=font(24),fill=(188,190,196))
    d.line((42,1260,1038,1260),fill=(255,255,255,90),width=2)
    y0=1308; rowh=49
    for i,t in enumerate(TRACKS):
        y=y0+i*rowh
        active=(current_index==i)
        revealed=(current_index is not None and i<=current_index)
        if active:
            d.rounded_rectangle((46,y-4,1034,y+42),radius=10,fill=(255,255,255,235))
            numfill=(10,10,12); songfill=(10,10,12); artfill=(70,72,78)
        elif revealed:
            numfill=(246,246,244); songfill=(246,246,244); artfill=(160,162,168)
        else:
            numfill=(82,84,90); songfill=(82,84,90); artfill=(69,71,76)
        d.text((65,y),f"{t['rank']:>2}",font=font(31,True),fill=numfill)
        songf=fit_text(d,t['song'],560,31,22,True)
        d.text((132,y),t['song'],font=songf,fill=songfill)
        artistf=fit_text(d,t['artist'],290,23,18,False)
        aw=d.textbbox((0,0),t['artist'],font=artistf)[2]
        d.text((1008-aw,y+4),t['artist'],font=artistf,fill=artfill)
    if cta:
        d.rounded_rectangle((55,1810,1025,1886),radius=24,fill=(255,255,255,235))
        c='Which one is your #1?'
        f=font(33,True); tw=d.textbbox((0,0),c,font=f)[2]
        d.text(((W-tw)//2,1829),c,font=f,fill=(10,10,12))
    im.save(out)


def intro_overlay(out:pathlib.Path):
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,H),fill=(0,0,0,105))
    d.text((58,115),'2010s EDM',font=font(38,True),fill=(210,212,218))
    lines=['TOP 10','NOSTALGIC','EDM SONGS']
    yy=590
    for j,line in enumerate(lines):
        f=font(105 if j!=1 else 94,True)
        d.text((58,yy+j*116),line,font=f,fill=WHITE)
    d.text((62,1020),'festival anthems • YouTube era • pure nostalgia',font=font(27),fill=(220,222,226))
    im.save(out)


def source_queries(t:dict)->list[str]:
    a=t['artist']; s=t['song']
    # Deliberately broad: DHS/source selection is not constrained to official sources.
    return [
        f'{a} {s}',
        f'{a} {s} live',
        f'{a} {s} festival',
        f'{s} {a} music video',
        f'{s} {a} crowd live',
    ]


def download_footage(t:dict,assets:pathlib.Path)->dict:
    out=assets/f"rank-{t['rank']:02d}.mp4"
    info=assets/f"rank-{t['rank']:02d}.info.json"
    for query in source_queries(t):
        for p in (out,info):
            if p.exists(): p.unlink()
        cmd=[
            'yt-dlp','--no-playlist','--no-warnings','--socket-timeout','25','--retries','3',
            '--match-filter','duration > 35 & duration < 900',
            '-f','bv*[height<=1080]+ba/b[height<=1080]/b',
            '--download-sections','*00:00:15-00:00:43','--force-keyframes-at-cuts',
            '--merge-output-format','mp4','--write-info-json',
            '-o',str(out),f'ytsearch1:{query}'
        ]
        p=run(cmd,check=False)
        if p.returncode==0 and out.exists() and out.stat().st_size>500000 and has_audio(out):
            meta={'source':'internet-search','query':query,'path':str(out)}
            if info.exists():
                try:
                    raw=json.loads(info.read_text(encoding='utf-8'))
                    meta.update({
                        'title':raw.get('title'),
                        'webpage_url':raw.get('webpage_url'),
                        'uploader':raw.get('uploader'),
                    })
                except Exception:
                    pass
            return meta
    raise RuntimeError(f"No usable internet source found for rank {t['rank']} {t['song']}")


def make_segment(src:pathlib.Path,overlay:pathlib.Path,dur:float,out:pathlib.Path,start:float=0.0):
    fadeout=max(0.0,dur-0.08)
    fc=(
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"eq=contrast=1.04:saturation=1.08:brightness=-0.015[v];"
        f"[1:v]format=rgba[ov];"
        f"[v][ov]overlay=0:0:format=auto,fps={FPS},format=yuv420p[vout]"
    )
    run([
        'ffmpeg','-hide_banner','-loglevel','error','-y','-stream_loop','-1','-ss',f'{start:.2f}','-i',str(src),
        '-loop','1','-i',str(overlay),'-t',f'{dur:.3f}','-filter_complex',fc,
        '-map','[vout]','-map','0:a:0','-af',f'aresample=48000,afade=t=in:st=0:d=0.08,afade=t=out:st={fadeout:.3f}:d=0.08',
        '-ac','2','-ar','48000','-c:v','libx264','-preset','veryfast','-crf','19','-c:a','aac','-b:a','192k',
        '-r',str(FPS),'-movflags','+faststart','-shortest',str(out)
    ])


def make_intro(src:pathlib.Path,overlay:pathlib.Path,dur:float,out:pathlib.Path,start:float=0.0):
    make_segment(src,overlay,dur,out,start=start)


def main():
    if len(sys.argv)<2: raise SystemExit('usage: render_edm_nostalgia.py OUTDIR')
    out=pathlib.Path(sys.argv[1]); assets=out/'assets'; work=out/'work'; ov=work/'overlay'; clips=work/'clips'
    for d in (out,assets,work,ov,clips): d.mkdir(parents=True,exist_ok=True)

    sources=[]
    for t in TRACKS:
        meta=download_footage(t,assets); sources.append(meta)
        print(json.dumps({'track':t,'source':meta},ensure_ascii=False),flush=True)

    intro_overlay(ov/'intro.png')
    for i in range(len(TRACKS)):
        overlay_png(i,ov/f'list-{i:02d}.png')
    overlay_png(len(TRACKS)-1,ov/'outro.png',cta=True)

    outputs=[]; timeline=[]; cursor=0.0
    intro=clips/'c00-intro.mp4'
    make_intro(pathlib.Path(sources[0]['path']),ov/'intro.png',INTRO,intro,start=0.0)
    outputs.append(intro); timeline.append({'type':'intro','start':cursor,'end':cursor+INTRO}); cursor+=INTRO

    for i,(t,meta) in enumerate(zip(TRACKS,sources)):
        dur=ONE if t['rank']==1 else REGULAR
        target=clips/f"c{len(outputs):02d}-rank-{t['rank']:02d}.mp4"
        src=pathlib.Path(meta['path'])
        start=INTRO if i==0 else (i%4)*1.2
        make_segment(src,ov/f'list-{i:02d}.png',dur,target,start=start)
        outputs.append(target)
        timeline.append({
            'type':'track','rank':t['rank'],'song':t['song'],'artist':t['artist'],
            'start':round(cursor,3),'end':round(cursor+dur,3),'source':meta
        })
        cursor+=dur

    outro=clips/f"c{len(outputs):02d}-outro.mp4"
    make_segment(pathlib.Path(sources[-1]['path']),ov/'outro.png',OUTRO,outro,start=ONE+1.5)
    outputs.append(outro); timeline.append({'type':'outro','start':round(cursor,3),'end':round(cursor+OUTRO,3)}); cursor+=OUTRO

    lst=work/'concat.txt'; lst.write_text('\n'.join("file '"+str(p.resolve())+"'" for p in outputs)+'\n')
    joined=work/'joined.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(lst),'-c','copy',str(joined)])
    final=out/'final.mp4'
    run([
        'ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(joined),'-map','0:v:0','-map','0:a:0',
        '-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=11','-c:a','aac','-b:a','192k','-movflags','+faststart',str(final)
    ])
    D=probe_duration(final)
    if abs(D-59.5)>0.45: raise RuntimeError(f'duration mismatch {D}')

    timing={
        'title':'Top 10 Nostalgic EDM Songs — 2010s','duration':D,'fps':FPS,'resolution':[W,H],
        'audio':'embedded from selected source clips; normalized for final output',
        'source_policy':'broad internet selection; no official-source priority',
        'timeline':timeline
    }
    (out/'timing.json').write_text(json.dumps(timing,ensure_ascii=False,indent=2),encoding='utf-8')

    sample=[0.8,3.5,8.6,13.7,18.8,23.9,29.0,34.1,39.2,44.3,49.4,55.5,58.8]
    thumbs=[]
    for j,t in enumerate(sample):
        q=work/f'q{j:02d}.jpg'
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',f'{t:.2f}','-i',str(final),'-frames:v','1','-vf','scale=270:480',str(q)])
        thumbs.append(Image.open(q).convert('RGB'))
    sheet=Image.new('RGB',(1080,1920),(16,16,18))
    for j,im in enumerate(thumbs[:16]): sheet.paste(im,((j%4)*270,(j//4)*480))
    sheet.save(out/'qa-contact.jpg',quality=94)

    raw=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(final)],text=True))
    vs=next(s for s in raw['streams'] if s.get('codec_type')=='video')
    qa={
        'duration':D,'resolution':[vs['width'],vs['height']],'codec':vs['codec_name'],'fps':FPS,
        'audio_streams':sum(1 for s in raw['streams'] if s.get('codec_type')=='audio'),
        'sources':sources
    }
    assert qa['resolution']==[1080,1920],qa
    assert qa['codec']=='h264',qa
    assert qa['audio_streams']==1,qa
    (out/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(qa,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
