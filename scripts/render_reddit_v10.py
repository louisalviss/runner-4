from __future__ import annotations

import asyncio, json, math, os, pathlib, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
import edge_tts

W,H,FPS = 1080,1920,30
VOICE='vi-VN-NamMinhNeural'
RATE='+22%'
BASE_D=48.216
BG=(8,9,12); WHITE=(246,247,249); MUT=(158,163,171); ORANGE=(255,79,50)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

VO=(
'Ngày 14 tháng 9 năm 2009, một người lên Reddit và viết: Tôi vừa thử heroin hôm qua. '
'Anh 24 tuổi, có bằng thạc sĩ, công việc tốt, và tin rằng mình chỉ đang thử một lần. '
'Bình luận cảnh báo anh dừng lại. Nhưng anh vẫn tin mình kiểm soát được. '
'Mười ba ngày sau, cùng tài khoản quay lại. Anh nói mình đã dùng heroin kể từ bài đầu, và hôm đó vừa tiêm lần đầu. '
'Những tháng sau là nghiện, triệu chứng cai, Suboxone, relapse, rồi một lần overdose mà anh nói phải dùng Narcan và nhập viện. '
'Nhưng đây không phải câu chuyện kết thúc bằng cái chết. Năm 2017, anh quay lại: gần sáu năm sạch ma túy và rượu. '
'Năm 2021: vẫn sống, vẫn sạch, vẫn ổn. '
'Đây là lời kể của một tài khoản ẩn danh, không phải hồ sơ y khoa được xác minh. Nhưng hai bài đăng cách nhau mười ba ngày đã đủ kể phần đáng sợ nhất.'
)

def run(cmd:list[str]):
    print('+',' '.join(cmd)); subprocess.run(cmd,check=True)

def probe(path:pathlib.Path)->float:
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)],text=True).strip())

def font(size:int,b=False):
    return ImageFont.truetype(BOLD if b else FONT,size)

def contain(im:Image.Image,w:int,h:int)->Image.Image:
    iw,ih=im.size; s=min(w/iw,h/ih); return im.resize((int(iw*s),int(ih*s)),Image.Resampling.LANCZOS)

def wrap(draw,text,fnt,maxw):
    lines=[]; cur=''
    for word in text.split():
        t=(cur+' '+word).strip()
        if draw.textbbox((0,0),t,font=fnt)[2] <= maxw: cur=t
        else:
            if cur: lines.append(cur)
            cur=word
    if cur: lines.append(cur)
    return lines

def compose_screenshot(src:pathlib.Path,label:str,out:pathlib.Path,lower:str=''):
    shot=Image.open(src).convert('RGB')
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.text((80,92),label,font=font(28,True),fill=ORANGE)
    framed=contain(shot,900,1450)
    x=(W-framed.width)//2; y=220+(1420-framed.height)//2
    d.rounded_rectangle((x-8,y-8,x+framed.width+8,y+framed.height+8),radius=18,fill=(32,34,39))
    im.paste(framed,(x,y))
    if lower:
        for i,line in enumerate(wrap(d,lower,font(37,True),900)[:2]):
            d.text((80,1640+i*50),line,font=font(37,True),fill=WHITE)
    im.save(out,quality=96)

def compose_timeline(out:pathlib.Path):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.text((80,110),'TIMELINE',font=font(28,True),fill=ORANGE)
    d.text((80,410),'14 SEP 2009',font=font(60,True),fill=WHITE)
    d.text((80,500),'“I did heroin yesterday.”',font=font(43,True),fill=MUT)
    d.line((150,870,930,870),fill=ORANGE,width=7)
    d.ellipse((132,852,168,888),fill=ORANGE); d.ellipse((912,852,948,888),fill=ORANGE)
    d.text((385,770),'13 DAYS',font=font(60,True),fill=ORANGE)
    d.text((80,1040),'27 SEP 2009',font=font(60,True),fill=WHITE)
    d.text((80,1130),'“first injection today”',font=font(43,True),fill=MUT)
    d.text((80,1540),'Không phải 13 tuần. Không phải 13 tháng.',font=font(34,True),fill=WHITE)
    im.save(out,quality=96)

def compose_compare(post1:pathlib.Path,post2:pathlib.Path,out:pathlib.Path):
    a=Image.open(post1).convert('RGB'); b=Image.open(post2).convert('RGB')
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.text((80,100),'TWO POSTS • 13 DAYS APART',font=font(28,True),fill=ORANGE)
    aa=contain(a,430,1280); bb=contain(b,430,1280)
    ya=290+(1220-aa.height)//2; yb=290+(1220-bb.height)//2
    im.paste(aa,(75,ya)); im.paste(bb,(575,yb))
    d.text((500,860),'→',font=font(62,True),fill=ORANGE)
    d.text((80,1625),'Timeline tự nó đã đủ mạnh.',font=font(38,True),fill=WHITE)
    im.save(out,quality=96)

async def synth(path:pathlib.Path):
    await edge_tts.Communicate(VO,VOICE,rate=RATE).save(str(path))

def make_still_clip(src:pathlib.Path,dur:float,out:pathlib.Path):
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-i',str(src),'-t',f'{dur:.3f}',
         '-vf',f'scale={W}:{H},fps={FPS},format=yuv420p','-an','-r',str(FPS),'-c:v','libx264','-preset','veryfast','-crf','18','-video_track_timescale','90000',str(out)])

def make_video_clip(src:pathlib.Path,dur:float,out:pathlib.Path,start:float,label:str='',caption:str=''):
    # Full-bleed REAL footage. Loop input if source is shorter than requested segment.
    # No blur, vignette, glow, or duplicated background layer.
    vf=(f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"fps={FPS},eq=contrast=1.02:saturation=0.95")
    if label:
        safe=label.replace("'","’").replace(':','\\:')
        vf += f",drawbox=x=45:y=70:w=680:h=74:color=black@0.72:t=fill,drawtext=fontfile={BOLD}:text='{safe}':fontcolor=white:fontsize=31:x=72:y=90"
    if caption:
        safe=caption.replace("'","’").replace(':','\\:')
        vf += f",drawbox=x=45:y=1600:w=990:h=130:color=black@0.72:t=fill,drawtext=fontfile={BOLD}:text='{safe}':fontcolor=white:fontsize=34:x=72:y=1638"
    vf += ',format=yuv420p'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-stream_loop','-1','-i',str(src),'-ss',f'{start:.2f}','-t',f'{dur:.3f}',
         '-vf',vf,'-an','-r',str(FPS),'-c:v','libx264','-preset','veryfast','-crf','18','-video_track_timescale','90000',str(out)])

def main():
    if len(sys.argv)<2: raise SystemExit('usage: render_reddit_v10.py OUTDIR')
    out=pathlib.Path(sys.argv[1]); work=out/'work'; clips=work/'clips'; stills=work/'stills'
    for d in (out,work,clips,stills): d.mkdir(parents=True,exist_ok=True)
    assets=pathlib.Path('assets/reddit-v10')
    required=['post1.png','comments.png','profile.png','post2.png','nyc.mp4','laptop.mp4','pills.mp4','hospital.mp4','corridor.mp4','river.mp4']
    for name in required:
        p=assets/name
        if not p.exists(): raise FileNotFoundError(p)
    voice=work/'voice.mp3'; asyncio.run(synth(voice)); D=probe(voice); scale=D/BASE_D
    compose_screenshot(assets/'post1.png','ARCHIVED REDDIT POST',stills/'post1.jpg')
    compose_screenshot(assets/'comments.png','ARCHIVED REDDIT COMMENTS',stills/'comments.jpg')
    compose_screenshot(assets/'profile.png','ARCHIVED REDDIT PROFILE',stills/'profile.jpg')
    compose_screenshot(assets/'post2.png','ARCHIVED REDDIT UPDATE',stills/'post2.jpg')
    compose_timeline(stills/'timeline.jpg')
    compose_compare(assets/'post1.png',assets/'post2.png',stills/'compare.jpg')
    plan=[
      (0.00,2.50,'still','post1.jpg',0,'',''),
      (2.50,5.40,'video','nyc.mp4',1.0,'REAL FOOTAGE • NEW YORK 2009',''),
      (5.40,8.10,'still','profile.jpg',0,'',''),
      (8.10,10.70,'video','laptop.mp4',1.5,'REAL FOOTAGE','Late-night browsing'),
      (10.70,13.50,'still','comments.jpg',0,'',''),
      (13.50,15.10,'video','laptop.mp4',5.0,'REAL FOOTAGE','“Tôi vẫn kiểm soát được.”'),
      (15.10,17.95,'still','timeline.jpg',0,'',''),
      (17.95,21.50,'still','post2.jpg',0,'',''),
      (21.50,24.50,'video','laptop.mp4',8.0,'REAL FOOTAGE','Cùng tài khoản quay lại'),
      (24.50,28.60,'video','pills.mp4',0.0,'REAL FOOTAGE • TREATMENT','Suboxone • withdrawal'),
      (28.60,32.10,'video','hospital.mp4',0.0,'REAL FOOTAGE • 2010','Overdose • hospital'),
      (32.10,36.00,'video','corridor.mp4',0.0,'REAL FOOTAGE • REHAB','Bắt đầu lại'),
      (36.00,40.20,'still','profile.jpg',0,'',''),
      (40.20,44.30,'video','river.mp4',0.0,'REAL FOOTAGE • RECOVERY','2017 → 2021'),
      (44.30,BASE_D,'still','compare.jpg',0,'',''),
    ]
    outputs=[]
    for i,(s,e,typ,name,start,label,caption) in enumerate(plan):
        dur=(e-s)*scale; target=clips/f'c{i:02d}.mp4'
        if typ=='still': make_still_clip(stills/name,dur,target)
        else: make_video_clip(assets/name,dur,target,start,label,caption)
        cd=probe(target)
        if abs(cd-dur)>0.18: raise RuntimeError(f'clip duration mismatch {target}: wanted {dur:.3f}, got {cd:.3f}')
        outputs.append(target)
    lst=work/'concat.txt'; lst.write_text('\n'.join("file '"+str(p.resolve())+"'" for p in outputs)+'\n')
    visual=work/'visual.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(lst),'-an','-vf',f'fps={FPS},format=yuv420p','-r',str(FPS),'-c:v','libx264','-preset','veryfast','-crf','18','-video_track_timescale','90000',str(visual)])
    VD=probe(visual)
    if abs(VD-D)>0.35: raise RuntimeError(f'visual/audio duration mismatch: visual={VD:.3f}, audio={D:.3f}')
    final=out/'final.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(visual),'-i',str(voice),'-map','0:v','-map','1:a',
         '-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(final)])
    FD=probe(final)
    if abs(FD-D)>0.35: raise RuntimeError(f'final duration mismatch: final={FD:.3f}, audio={D:.3f}')
    times=[1,3.5,6.5,9.2,11.8,14.3,16.5,19.5,22.8,26.2,30.0,34.0,38.0,42.2,46.0]
    thumbs=[]
    for j,t in enumerate(times):
        q=work/f'q{j:02d}.jpg'; run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',f'{t*scale:.2f}','-i',str(final),'-frames:v','1','-vf','scale=270:480',str(q)])
        thumbs.append(Image.open(q).convert('RGB'))
    sheet=Image.new('RGB',(1080,1920),(18,19,22))
    for j,im in enumerate(thumbs): sheet.paste(im,((j%4)*270,(j//4)*480))
    sheet.save(out/'qa-contact.jpg',quality=94)
    qa={'version':'V10.2 real footage synced','duration':D,'final_duration':FD,'resolution':[W,H],'real_footage_segments':8,'real_footage_seconds_approx':round(sum((e-s)*scale for s,e,t,*_ in plan if t=='video'),2),'reddit_screenshots':['post1','comments','profile','post2'],'graphics':['timeline','comparison'],'blur_background':False,'vignette':False,'glow_layer':False,'ai_generated_people':False,'av_duration_delta':round(abs(FD-D),3)}
    (out/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(qa,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
