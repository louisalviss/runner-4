from __future__ import annotations
import pathlib, re, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import render_reddit_doc_v3 as m

def download_footage(url, out):
    match=re.search(r'-(\d+)/?$', url)
    if not match:
        print('no pexels id', url); return False
    vid=match.group(1)
    direct=f'https://www.pexels.com/download/video/{vid}/'
    try:
        subprocess.run(['curl','-fL','--retry','3','--connect-timeout','20','-A','Mozilla/5.0','-o',str(out),direct],check=True)
        if not out.exists() or out.stat().st_size < 100000:
            return False
        subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name','-of','default=nw=1:nk=1',str(out)],check=True,stdout=subprocess.DEVNULL)
        print('downloaded pexels',vid,out.stat().st_size)
        return True
    except Exception as e:
        print('pexels direct failed',vid,e)
        return False

m.download_footage=download_footage
m.main()
