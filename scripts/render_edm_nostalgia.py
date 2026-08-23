from __future__ import annotations

import json, pathlib, subprocess, sys, textwrap
from PIL import Image, ImageDraw, ImageFont

W,H,FPS = 1080,1920,30
BG=(8,8,10)
WHITE=(248,248,246)
MUTED=(118,120,126)
DIM=(58,60,66)
ACCENT=(255,255,255)
PANEL=(10,10,12,220)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

TRACKS=[
    {'rank':10,'song':'Tsunami','artist':'DVBBS & Borgeous','query':'DVBBS Borgeous Tsunami official music video','fallback':2941128},
    {'rank':9,'song':'Heroes (We Could Be)','artist':'Alesso ft. Tove Lo','query':'Alesso Heroes We Could Be official video','fallback':3722010},
    {'rank':8,'song':'The Nights','artist':'Avicii','query':'Avicii The Nights official music video','fallback':1692701},
    {'rank':7,'song':'Summer','artist':'Calvin Harris','query':'Calvin Harris Summer official video','fallback':13054630},
    {'rank':6,'song':'Titanium','artist':'David Guetta ft. Sia','query':'David Guetta Titanium ft Sia official video','fallback':2941105},
    {'rank':5,'song':'Animals','artist':'Martin Garrix','query':'Martin Garrix Animals official video','fallback':3042698},
    {'rank':4,'song':"Don't You Worry Child",'artist':'Swedish House Mafia','query':"Swedish House Mafia Don't You Worry Child official video",'fallback':30328826},
    {'rank':3,'song':'Clarity','artist':'Zedd ft. Foxes','query':'Zedd Clarity official music video','fallback':12695738},
    {'rank':2,'song':'Wake Me Up','artist':'Avicii','query':'Avicii Wake Me Up official video','fallback':9003204},
    {'rank':1,'song':'Levels','artist':'Avicii','query':'Avicii Levels official music video','fallback':7722307},
]

INTRO=2.2
REGULAR=5.1
ONE=6.4
OUTRO=5.0


def run(cmd:list[str],check=True):
    print('+',' '.join(cmd),flush=True)
    return subprocess.run(cmd,check=check)


def probe_duration(path:pathlib.Path)->float:
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)],text=True).strip())


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
    # top/bottom readability plates
    d.rectangle((0,0,W,260),fill=(0,0,0,196))
    d.rectangle((0,1260,W,H),fill=(0,0,0,224))
    d.text((58,72),'TOP 10 NOSTALGIC',font=font(54,True),fill=WHITE)
    d.text((58,133),'EDM SONGS — 2010s',font=font(58,True),fill=WHITE)
    d.text((60,206),'the era that made festival EDM feel enormous',font=font(24),fill=(188,190,196))
    # frame separators
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


def download_footage(t:dict,assets:pathlib.Path)->dict:
    out=assets/f"rank-{t['rank']:02d}.mp4"
    # Prefer official/recognizable public video search. Silent visual only.
    yt=['yt-dlp','--no-playlist','--no-warnings','--socket-timeout','20','--retries','2',
        '-f','bv*[height<=1080]/bestvideo[height<=1080]/best[height<=1080]',
        '--download-sections','*00:00:15-00:00:40','--force-keyframes-at-cuts','--merge-output-format','mp4',
        '-o',str(out),f"ytsearch1:{t['query']}"]
    p=run(yt,check=False)
    if p.returncode==0 and out.exists() and out.stat().st_size>300000:
        return {'source':'youtube-search','query':t['query'],'path':str(out)}
    # Reliable fallback; still keeps the real-concert/festival visual grammar.
    if out.exists(): out.unlink()
    url=f"https://www.pexels.com/download/video/{t['fallback']}/"
    p=run(['curl','-L','--fail','--retry','4','--retry-delay','2','-A','Mozilla/5.0',url,'-o',str(out)],check=False)
    if p.returncode!=0 or not out.exists() or out.stat().st_size<100000:
        raise RuntimeError(f"failed footage for rank {t['rank']}")
    return {'source':'pexels-fallback','id':t['fallback'],'path':str(out)}


def make_segment(src:pathlib.Path,overlay:pathlib.Path,dur:float,out:pathlib.Path,start:float=0.0):
    # Full-bleed crop; static native overlay keeps the TikTok-native ranking template clean.
    vf=(f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"eq=contrast=1.04:saturation=1.08:brightness=-0.015,"
        f"overlay=0:0:format=auto,fps={FPS},format=yuv420p")
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-stream_loop','-1','-ss',f'{start:.2f}','-i',str(src),'-loop','1','-i',str(overlay),
         '-t',f'{dur:.3f}','-filter_complex',vf,'-map','0:v:0','-an','-r',str(FPS),'-c:v','libx264','-preset','veryfast','-crf','19','-movflags','+faststart',str(out)]
    run(cmd)


def make_intro(src:pathlib.Path,overlay:pathlib.Path,dur:float,out:pathlib.Path):
    vf=(f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"eq=contrast=1.06:saturation=1.10:brightness=-0.03,overlay=0:0:format=auto,fps={FPS},format=yuv420p")
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-stream_loop','-1','-i',str(src),'-loop','1','-i',str(overlay),'-t',f'{dur:.3f}',
         '-filter_complex',vf,'-map','0:v:0','-an','-r',str(FPS),'-c:v','libx264','-preset','veryfast','-crf','19','-movflags','+faststart',str(out)])


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
    make_intro(pathlib.Path(sources[0]['path']),ov/'intro.png',INTRO,intro)
    outputs.append(intro); timeline.append({'type':'intro','start':cursor,'end':cursor+INTRO}); cursor+=INTRO

    for i,(t,meta) in enumerate(zip(TRACKS,sources)):
        dur=ONE if t['rank']==1 else REGULAR
        target=clips/f"c{len(outputs):02d}-rank-{t['rank']:02d}.mp4"
        src=pathlib.Path(meta['path'])
        # Vary source position a little when full sources are available.
        start=(i%4)*1.25
        make_segment(src,ov/f'list-{i:02d}.png',dur,target,start=start)
        outputs.append(target)
        timeline.append({'type':'track','rank':t['rank'],'song':t['song'],'artist':t['artist'],'start':round(cursor,3),'end':round(cursor+dur,3),'source':meta})
        cursor+=dur

    outro=clips/f"c{len(outputs):02d}-outro.mp4"
    make_segment(pathlib.Path(sources[-1]['path']),ov/'outro.png',OUTRO,outro,start=8.0)
    outputs.append(outro); timeline.append({'type':'outro','start':round(cursor,3),'end':round(cursor+OUTRO,3)}); cursor+=OUTRO

    lst=work/'concat.txt'; lst.write_text('\n'.join("file '"+str(p.resolve())+"'" for p in outputs)+'\n')
    final=out/'final.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(lst),'-an','-vf',f'fps={FPS},format=yuv420p',
         '-r',str(FPS),'-c:v','libx264','-preset','medium','-crf','18','-movflags','+faststart',str(final)])
    D=probe_duration(final)
    if abs(D-59.5)>0.40: raise RuntimeError(f'duration mismatch {D}')

    timing={'title':'Top 10 Nostalgic EDM Songs — 2010s','duration':D,'fps':FPS,'resolution':[W,H],'audio':'intentionally omitted for DHS','timeline':timeline}
    (out/'timing.json').write_text(json.dumps(timing,ensure_ascii=False,indent=2),encoding='utf-8')

    # Contact sheet for visual QC.
    sample=[0.8,3.5,8.6,13.7,18.8,23.9,29.0,34.1,39.2,44.3,49.4,55.5,58.8]
    thumbs=[]
    for j,t in enumerate(sample):
        q=work/f'q{j:02d}.jpg'
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',f'{t:.2f}','-i',str(final),'-frames:v','1','-vf','scale=270:480',str(q)])
        thumbs.append(Image.open(q).convert('RGB'))
    sheet=Image.new('RGB',(1080,1920),(16,16,18))
    for j,im in enumerate(thumbs[:16]): sheet.paste(im,((j%4)*270,(j//4)*480))
    sheet.save(out/'qa-contact.jpg',quality=94)

    # Machine QA.
    raw=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(final)],text=True))
    vs=next(s for s in raw['streams'] if s.get('codec_type')=='video')
    qa={'duration':D,'resolution':[vs['width'],vs['height']],'codec':vs['codec_name'],'fps':FPS,'audio_streams':sum(1 for s in raw['streams'] if s.get('codec_type')=='audio'),'sources':sources}
    assert qa['resolution']==[1080,1920],qa
    assert qa['codec']=='h264',qa
    assert qa['audio_streams']==0,qa
    (out/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(qa,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
