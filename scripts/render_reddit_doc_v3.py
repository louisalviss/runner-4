from __future__ import annotations
import asyncio, json, math, pathlib, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import edge_tts

W,H,FPS=1080,1920,30
VOICE='vi-VN-NamMinhNeural'
RATE='+18%'
BG=(9,10,13); WHITE=(246,247,249); MUTED=(156,161,170); ORANGE=(255,69,0); RED=(231,72,60); GREEN=(75,181,132)

SEGMENTS=[
('hook','Mười ba ngày. Đó là khoảng cách giữa hai bài đăng của cùng một tài khoản Reddit: “Tôi vừa thử heroin” và “hôm nay tôi vừa tiêm lần đầu”.','13 NGÀY','Từ lần thử đầu tiên\nđến mũi tiêm đầu tiên.'),
('setup','Ngày 14 tháng 9 năm 2009, Spontaneous H nói mình 24 tuổi, có bằng thạc sĩ, công việc tốt và gần như chưa dùng ma túy. Anh thử heroin vì tò mò.','14.09.2009','“Tôi vừa thử heroin.”'),
('confidence','Trong bài đầu, anh nhấn mạnh đây chỉ là một trải nghiệm và tin mình có thể kiểm soát. Nhiều người cảnh báo. Anh vẫn nghĩ mình hiểu rủi ro.','BÀI ĐẦU','Tự tin rằng\nmình kiểm soát được.'),
('turn','Ngày 27 tháng 9, anh quay lại. Anh nói đã tiếp tục dùng kể từ bài đầu, và hôm đó vừa tiêm lần đầu.','27.09.2009','13 ngày sau.'),
('fall','Sau đó là nghiện, điều trị bằng Suboxone, relapse và một lần overdose nghiêm trọng theo lời tài khoản. Đến năm 2010, anh đã phải vào rehab.','2009 → 2010','Nghiện. Điều trị.\nOverdose. Rehab.'),
('recovery','Năm 2017, anh xuất hiện lại và nói đã gần sáu năm không dùng ma túy hay rượu. Câu ngắn nhất trong saga cũng là câu nhẹ nhõm nhất: cuộc sống đang tốt.','09.01.2017','Gần 6 năm sạch.'),
('later','Năm 2021, anh cập nhật thêm: vẫn sống, vẫn sạch và vẫn ổn.','25.09.2021','Vẫn sống.\nVẫn sạch. Vẫn ổn.'),
('caveat','Đây vẫn là lời tự thuật của một tài khoản ẩn danh, không phải hồ sơ y khoa được xác minh độc lập. Không cần phóng đại câu chuyện: timeline đã đủ mạnh.','LƯU Ý','Tự thuật ẩn danh.\nTimeline là phần đáng chú ý.')]

PEXELS={
'hook':'https://www.pexels.com/video/new-york-streets-19332988/',
'setup':'https://www.pexels.com/video/new-york-subway-18600295/',
'confidence':'https://www.pexels.com/video/video-of-a-road-in-new-york-6755998/',
'fall':'https://www.pexels.com/video/an-empty-hospital-hallway-5203510/',
'recovery':'https://www.pexels.com/video/a-person-opening-a-window-5835695/',
'later':'https://www.pexels.com/video/the-morning-sky-during-sunrise-5631108/'
}

def run(cmd):
    print('+',' '.join(map(str,cmd)),flush=True); subprocess.run(list(map(str,cmd)),check=True)

def dur(p):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)],text=True).strip())

def font(size,bold=False):
    candidates=['/usr/share/fonts/truetype/inter/Inter-Bold.ttf' if bold else '/usr/share/fonts/truetype/inter/Inter-Regular.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for p in candidates:
        if pathlib.Path(p).exists(): return ImageFont.truetype(p,size)
    raise RuntimeError('font missing')

def wrap(d,text,fnt,width):
    lines=[]
    for para in text.split('\n'):
        cur=''
        for w in para.split():
            t=(cur+' '+w).strip()
            if d.textbbox((0,0),t,font=fnt)[2] <= width: cur=t
            else:
                if cur: lines.append(cur)
                cur=w
        if cur: lines.append(cur)
    return '\n'.join(lines)

async def synth(text,path):
    await edge_tts.Communicate(text,VOICE,rate=RATE).save(str(path))

def make_overlay(label,title,out,accent=ORANGE,small=''):
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    # cinematic top/bottom falloff
    for i in range(520):
        a=int(205*(1-i/520)); d.rectangle((0,i,W,i+1),fill=(5,6,8,a))
    for i in range(620):
        a=int(235*(i/620)); y=H-620+i; d.rectangle((0,y,W,y+1),fill=(5,6,8,a))
    d.rounded_rectangle((68,100,344,158),radius=29,fill=accent+(255,))
    d.text((96,112),label,font=font(25,True),fill=(10,10,12,255))
    tf=font(70 if len(title)<35 else 58,True); tt=wrap(d,title,tf,900)
    box=d.multiline_textbbox((0,0),tt,font=tf,spacing=10); th=box[3]-box[1]
    y=1325-th
    d.multiline_text((72,y),tt,font=tf,fill=WHITE+(255,),spacing=10)
    if small:
        sf=font(27); st=wrap(d,small,sf,890); d.multiline_text((74,1500),st,font=sf,fill=MUTED+(255,),spacing=8)
    d.line((72,1748,1008,1748),fill=(82,86,96,180),width=2)
    d.text((72,1774),'REDDIT ARCHIVE  •  2009—2021',font=font(22),fill=(127,132,141,255))
    im.save(out)

def make_reddit_card(kind,out):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.rounded_rectangle((58,170,1022,1540),radius=38,fill=(244,245,247))
    d.rectangle((58,170,1022,272),fill=ORANGE)
    d.text((96,200),'reddit  /  r/IAmA',font=font(34,True),fill='white')
    if kind=='setup':
        date='14 SEP 2009  •  u/SpontaneousH'; title='I did heroin yesterday. I am not a drug user… AMA'
        bullets=['24 years old','Master’s degree','Well-paying full-time job','Said he had almost no prior drug use']
    else:
        date='27 SEP 2009  •  u/SpontaneousH'; title="2 weeks ago I tried heroin ‘once for fun’… I have been using since and shot up for the first time today"
        bullets=['Continued using after first post','First injection that day','Said he wanted to stop before it got worse']
    d.text((96,320),date,font=font(28),fill=(91,95,102)); tf=font(50,True); d.multiline_text((96,390),wrap(d,title,tf,840),font=tf,fill=(31,33,37),spacing=13)
    yy=820
    for b in bullets:
        d.ellipse((100,yy+10,118,yy+28),fill=ORANGE); d.text((146,yy),b,font=font(31),fill=(54,57,63)); yy+=86
    d.text((72,1615),'RECONSTRUCTED FROM PUBLIC REDDIT ARCHIVE',font=font(23,True),fill=ORANGE)
    d.text((72,1660),'Anonymous self-report; not independently verified.',font=font(25),fill=MUTED)
    im.save(out,quality=96)

def download_footage(url,out):
    # yt-dlp handles the Pexels page; fallback handled by caller.
    cmd=['yt-dlp','--no-playlist','-f','best[height<=1080]/best','-o',str(out),url]
    try: run(cmd); return out.exists() and out.stat().st_size>100000
    except Exception as e: print('footage fallback',url,e); return False

def synth_bed(seconds,out):
    sr=48000; n=int(sr*seconds); t=np.arange(n)/sr; rng=np.random.default_rng(7)
    # evolving low drone + very soft filtered noise + sparse pulses
    x=.018*np.sin(2*np.pi*55*t)+.010*np.sin(2*np.pi*82.4*t)+.006*np.sin(2*np.pi*110*t)
    noise=rng.normal(0,1,n)
    kernel=np.ones(500)/500; noise=np.convolve(noise,kernel,mode='same')
    x+=.025*noise
    for sec in [0,7.5,17,25,34,43,51]:
        i=int(sec*sr); m=min(int(.55*sr),n-i)
        if m>0:
            env=np.exp(-np.linspace(0,7,m)); x[i:i+m]+=0.10*env*np.sin(2*np.pi*68*np.arange(m)/sr)
    # short transition ticks
    for sec in [4.2,12,20,27.5,37,45,51.5]:
        i=int(sec*sr); m=min(int(.12*sr),n-i)
        if m>0: x[i:i+m]+=0.045*rng.normal(0,1,m)*np.hanning(m)
    x=np.clip(x,-.45,.45); pcm=(x*32767).astype(np.int16)
    with wave.open(str(out),'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('out'); args=ap.parse_args()
    out=pathlib.Path(args.out); work=out/'work'; audio=work/'audio'; clips=work/'clips'; assets=work/'assets'; overlays=work/'overlays'
    for p in [out,work,audio,clips,assets,overlays]: p.mkdir(parents=True,exist_ok=True)

    # narration per beat -> exact editorial timing
    durations=[]
    for i,(_,text,_,_) in enumerate(SEGMENTS):
        p=audio/f'{i:02d}.mp3'; asyncio.run(synth(text,p)); durations.append(dur(p)+0.12)
    total=sum(durations)

    # source cards
    make_reddit_card('setup',assets/'reddit_first.jpg'); make_reddit_card('turn',assets/'reddit_second.jpg')

    # footage acquisition
    footage={}
    for key,url in PEXELS.items():
        p=assets/f'{key}.mp4'; footage[key]=p if download_footage(url,p) else None

    # fallback backgrounds are still editorial cards, never blank slides
    for i,(kind,_,label,title) in enumerate(SEGMENTS):
        ov=overlays/f'{i:02d}.png'
        accent=GREEN if kind in {'recovery','later'} else RED if kind=='fall' else ORANGE
        small=''
        if kind=='hook': small='Hai tiêu đề được đăng bởi cùng một tài khoản.'
        elif kind=='confidence': small='Cộng đồng cảnh báo; anh vẫn tin mình hiểu rủi ro.'
        elif kind=='fall': small='Các chi tiết y tế sau đây là lời tự thuật của tài khoản.'
        elif kind=='caveat': small='Không biến một tài khoản ẩn danh thành bằng chứng y khoa.'
        make_overlay(label,title,ov,accent,small)

        # background selection
        if kind=='setup': bg=assets/'reddit_first.jpg'; is_img=True
        elif kind=='turn': bg=assets/'reddit_second.jpg'; is_img=True
        elif footage.get(kind): bg=footage[kind]; is_img=False
        elif kind in {'confidence','caveat'}: bg=assets/'reddit_first.jpg'; is_img=True
        else: bg=assets/'reddit_second.jpg'; is_img=True

        clip=clips/f'{i:02d}.mp4'; d=durations[i]
        if is_img:
            vf=f"scale=1180:2098,zoompan=z='min(zoom+0.00018,1.055)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},eq=brightness=-0.13:saturation=0.72,format=yuv420p"
            run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-i',bg,'-i',ov,'-t',f'{d:.3f}','-filter_complex',f"[0:v]{vf}[b];[b][1:v]overlay=0:0:format=auto[v]",'-map','[v]','-an','-c:v','libx264','-preset','veryfast','-crf','19','-movflags','+faststart',clip])
        else:
            start=1.0 + (i%3)*0.8
            vf=f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},eq=brightness=-0.16:contrast=1.05:saturation=0.70,format=yuv420p"
            run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(start),'-stream_loop','-1','-i',bg,'-i',ov,'-t',f'{d:.3f}','-filter_complex',f"[0:v]{vf}[b];[b][1:v]overlay=0:0:format=auto[v]",'-map','[v]','-an','-c:v','libx264','-preset','veryfast','-crf','19','-movflags','+faststart',clip])

    # concat video and narration
    (work/'v.txt').write_text('\n'.join([f"file '{(clips/f'{i:02d}.mp4').resolve()}'" for i in range(len(SEGMENTS))])+'\n')
    (work/'a.txt').write_text('\n'.join([f"file '{(audio/f'{i:02d}.mp3').resolve()}'" for i in range(len(SEGMENTS))])+'\n')
    visual=work/'visual.mp4'; voice=work/'voice.wav'; bed=work/'bed.wav'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',work/'v.txt','-c','copy',visual])
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',work/'a.txt','-ar','48000','-ac','1','-c:a','pcm_s16le',voice])
    synth_bed(total,bed)

    final=out/'final.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',visual,'-i',voice,'-i',bed,'-filter_complex','[1:a]volume=1.0[v];[2:a]volume=0.52[b];[v][b]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]','-map','0:v','-map','[a]','-c:v','libx264','-preset','medium','-crf','20','-c:a','aac','-b:a','160k','-pix_fmt','yuv420p','-movflags','+faststart',final])

    # visual QA contact sheet: first/mid/end and each beat midpoint
    times=[]; cur=0.0
    for d in durations: times.append(cur+d/2); cur+=d
    thumbs=[]
    for j,t in enumerate(times):
        p=work/f'qa{j}.jpg'; run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',f'{t:.2f}','-i',final,'-frames:v','1','-vf','scale=270:480',p]); thumbs.append(Image.open(p).convert('RGB'))
    sheet=Image.new('RGB',(1080,960),(18,19,22))
    for j,im in enumerate(thumbs): sheet.paste(im,((j%4)*270,(j//4)*480))
    sheet.save(out/'qa-contact.jpg',quality=92)
    q={'duration_seconds':round(dur(final),3),'resolution':[W,H],'fps':FPS,'voice':VOICE,'voice_rate':RATE,'beats':len(SEGMENTS),'footage_downloaded':{k:bool(v) for k,v in footage.items()},'creative_qa':['real motion footage where available','two reconstructed source cards','no full transcript subtitles','beat-specific visual hierarchy','sound bed + transition impacts','contact sheet extracted from final']}
    (out/'qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2))
    print(json.dumps(q,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
