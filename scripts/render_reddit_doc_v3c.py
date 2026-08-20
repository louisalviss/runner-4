from __future__ import annotations
import pathlib, re, subprocess, sys, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import render_reddit_doc_v3 as m

def direct_pexels(url, out):
    match=re.search(r'-(\d+)/?$', url)
    if not match: return False
    vid=match.group(1)
    direct=f'https://www.pexels.com/download/video/{vid}/'
    try:
        subprocess.run(['curl','-fL','--retry','3','--connect-timeout','20','-A','Mozilla/5.0','-o',str(out),direct],check=True)
        if not out.exists() or out.stat().st_size < 100000: return False
        subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name','-of','default=nw=1:nk=1',str(out)],check=True,stdout=subprocess.DEVNULL)
        return True
    except Exception as e:
        print('pexels failed', vid, e)
        return False

m.download_footage=direct_pexels
m.main()

# Repair CFR/timestamps. Some stock inputs carry incompatible timebases and made concat copy expand video duration.
out=pathlib.Path(sys.argv[1])
work=out/'work'; clips=work/'clips'; audio=work/'audio'
fixed=work/'fixed'; fixed.mkdir(exist_ok=True)

def pdur(p):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)],text=True).strip())

durations=[pdur(audio/f'{i:02d}.mp3')+0.12 for i in range(len(m.SEGMENTS))]
fixed_clips=[]
for i,d in enumerate(durations):
    src=clips/f'{i:02d}.mp4'; dst=fixed/f'{i:02d}.mp4'
    subprocess.run([
        'ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(src),'-t',f'{d:.3f}',
        '-vf','fps=30,setpts=N/(30*TB)','-r','30','-fps_mode','cfr','-an',
        '-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-video_track_timescale','90000',str(dst)
    ],check=True)
    fixed_clips.append(dst)

# Re-encode concat, never stream-copy across differing timebases.
lst=fixed/'list.txt'
lst.write_text('\n'.join([f"file '{p.resolve()}'" for p in fixed_clips])+'\n')
visual=fixed/'visual-cfr.mp4'
subprocess.run([
    'ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(lst),
    '-vf','fps=30,setpts=N/(30*TB)','-r','30','-fps_mode','cfr','-an',
    '-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-video_track_timescale','90000',str(visual)
],check=True)

final=out/'final.mp4'; voice=work/'voice.wav'; bed=work/'bed.wav'
subprocess.run([
    'ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(visual),'-i',str(voice),'-i',str(bed),
    '-filter_complex','[1:a]volume=1.0[v];[2:a]volume=0.52[b];[v][b]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]',
    '-map','0:v','-map','[a]','-r','30','-fps_mode','cfr','-c:v','libx264','-preset','medium','-crf','20',
    '-c:a','aac','-b:a','160k','-ar','48000','-pix_fmt','yuv420p','-shortest','-movflags','+faststart',str(final)
],check=True)

# Regenerate QA at the midpoint of every intended beat.
from PIL import Image
cur=0.0; times=[]
for d in durations:
    times.append(cur+d/2); cur+=d
thumbs=[]
for j,t in enumerate(times):
    p=fixed/f'qa{j}.jpg'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',f'{t:.3f}','-i',str(final),'-frames:v','1','-vf','scale=270:480',str(p)],check=True)
    thumbs.append(Image.open(p).convert('RGB'))
sheet=Image.new('RGB',(1080,960),(18,19,22))
for j,im in enumerate(thumbs): sheet.paste(im,((j%4)*270,(j//4)*480))
sheet.save(out/'qa-contact.jpg',quality=93)

fps=subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=r_frame_rate','-of','default=nw=1:nk=1',str(final)],text=True).strip()
q=json.loads((out/'qa.json').read_text())
q.update({
    'duration_seconds':round(pdur(final),3),
    'fps_actual':fps,
    'intended_duration_seconds':round(sum(durations),3),
    'timing_fixed':True,
    'all_beat_midpoints_qa':True
})
(out/'qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2))
print(json.dumps(q,ensure_ascii=False,indent=2))
