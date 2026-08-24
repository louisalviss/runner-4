from __future__ import annotations
import asyncio,json,pathlib,subprocess,math
from PIL import Image,ImageDraw,ImageFont
import edge_tts
W,H,FPS=1080,1920,30
VOICE='vi-VN-NamMinhNeural'; OR=(255,69,0); BG=(12,13,16); FG=(246,247,249); MUT=(145,150,160); CARD=(28,30,36); GREEN=(73,185,129)
def run(c): subprocess.run(c,check=True)
def probe(p): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)],text=True).strip())
def F(n,b=False): return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if b else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
def wrap(d,s,f,w):
 o=[]
 for para in s.split('\n'):
  c=''
  for x in para.split():
   q=(c+' '+x).strip()
   if d.textbbox((0,0),q,font=f)[2]<=w:c=q
   else:
    if c:o.append(c)
    c=x
  if c:o.append(c)
 return '\n'.join(o)
def browser(post,date,highlight=None,sub='r/IAmA • u/SpontaneousH'):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 d.rounded_rectangle((55,120,1025,1730),32,fill=(238,239,241));d.rounded_rectangle((55,120,1025,220),32,fill=(45,47,52));d.rectangle((55,185,1025,220),fill=(45,47,52))
 for x,c in [(95,(238,94,86)),(135,(238,190,73)),(175,(80,190,104))]:d.ellipse((x,153,x+22,175),fill=c)
 d.rounded_rectangle((235,145,900,190),18,fill=(67,70,77));d.text((270,154),'reddit.com/r/IAmA',font=F(20),fill=(205,207,212))
 d.text((95,280),sub,font=F(25,True),fill=(98,101,108));d.text((95,335),date,font=F(22),fill=(120,123,130))
 title=wrap(d,post,F(46,True),830);d.multiline_text((95,410),title,font=F(46,True),fill=(28,30,34),spacing=14)
 if highlight:
  d.rounded_rectangle((90,760,940,950),22,fill=(255,239,224),outline=OR,width=4);d.multiline_text((125,800),wrap(d,highlight,F(34,True),760),font=F(34,True),fill=(48,43,39),spacing=10)
 d.line((95,1050,930,1050),fill=(205,207,211),width=2);d.text((95,1100),'COMMENTS',font=F(21,True),fill=(120,123,130))
 for i in range(3):
  y=1160+i*145;d.ellipse((100,y,132,y+32),fill=(184,187,192));d.rounded_rectangle((155,y,870,y+22),10,fill=(190,193,198));d.rounded_rectangle((155,y+45,760-i*70,y+64),9,fill=(211,213,216))
 return im
def frame(kind,a,b='',accent=OR):
 if kind=='browser':return browser(a,b)
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 d.text((70,95),'SPONTANEOUSH • REDDIT ARCHIVE',font=F(22,True),fill=(105,110,120));d.line((70,140,1010,140),fill=(48,51,58),width=2)
 if kind=='date':d.text((70,390),a,font=F(96,True),fill=FG);d.multiline_text((70,560),wrap(d,b,F(47,True),900),font=F(47,True),fill=accent,spacing=16)
 elif kind=='quote':d.text((70,330),a,font=F(30,True),fill=MUT);d.rounded_rectangle((70,450,1010,1280),36,fill=CARD);d.text((110,485),'“',font=F(110,True),fill=accent);d.multiline_text((145,630),wrap(d,b,F(54,True),780),font=F(54,True),fill=FG,spacing=18)
 elif kind=='fact':d.text((70,360),a,font=F(66,True),fill=FG);d.multiline_text((70,570),wrap(d,b,F(39),900),font=F(39),fill=MUT,spacing=16)
 elif kind=='recover':d.text((70,380),a,font=F(84,True),fill=GREEN);d.multiline_text((70,600),wrap(d,b,F(48,True),900),font=F(48,True),fill=FG,spacing=18)
 return im
VO=('Ngày 14 tháng 9 năm 2009, một người lên Reddit và viết: Tôi vừa thử heroin hôm qua. '
'Anh 24 tuổi, có bằng thạc sĩ, công việc tốt, và tin rằng mình chỉ đang thử một lần. '
'Bình luận cảnh báo anh dừng lại. Nhưng anh vẫn tin mình kiểm soát được. '
'Mười ba ngày sau, cùng tài khoản quay lại. Anh nói mình đã dùng heroin kể từ bài đầu, và hôm đó vừa tiêm lần đầu. '
'Những tháng sau là nghiện, triệu chứng cai, Suboxone, relapse, rồi một lần overdose mà anh nói phải dùng Narcan và nhập viện. '
'Nhưng đây không phải câu chuyện kết thúc bằng cái chết. Năm 2017, anh quay lại: gần sáu năm sạch ma túy và rượu. '
'Năm 2021: vẫn sống, vẫn sạch, vẫn ổn. '
'Đây là lời kể của một tài khoản ẩn danh, không phải hồ sơ y khoa được xác minh. Nhưng hai bài đăng cách nhau mười ba ngày đã đủ kể phần đáng sợ nhất.')
SH=[
('browser','I did Heroin yesterday. I am not a drug user, and never have been. AMA.','14 SEP 2009'),
('quote','14 SEP 2009','Tôi vừa thử heroin hôm qua.'),('fact','24 TUỔI','Bằng thạc sĩ. Công việc tốt.'),('fact','“CHỈ THỬ”','Anh tin đây là một trải nghiệm có thể kiểm soát.'),
('quote','COMMENTS','Đừng thử lại.'),('quote','COMMENTS','Heroin không quan tâm bạn nghĩ mình kiểm soát tốt đến đâu.'),('fact','NHƯNG','Anh vẫn tin mình hiểu rủi ro.'),
('date','14.09','Bài đầu tiên.'),('date','+13 DAYS','Không phải 13 tuần. Không phải 13 tháng.'),('date','27.09','Cùng tài khoản quay lại.'),
('browser','Two weeks ago I tried heroin once...','27 SEP 2009'),('quote','UPDATE','Tôi đã tiếp tục dùng kể từ bài đầu.'),('quote','27 SEP 2009','Hôm nay vừa tiêm lần đầu.'),
('date','13 NGÀY','Từ “chỉ thử” → mũi tiêm đầu tiên.'),('fact','WITHDRAWAL','Các update sau mô tả craving và triệu chứng cai.'),('fact','SUBOXONE','Anh bắt đầu điều trị.'),
('date','2010','Câu chuyện tiếp tục xấu đi.'),('fact','RELAPSE','Anh quay lại sử dụng.'),('fact','OVERDOSE','Một update mô tả fentanyl và nhiều chất khác.'),('fact','NARCAN','Anh nói EMS phải dùng nhiều liều.'),('fact','HOSPITAL','Sau đó là bệnh viện và rehab.'),
('date','2017','Tài khoản xuất hiện trở lại.'),('recover','GẦN 6 NĂM SẠCH','“Life is good.”'),('fact','CORRECTION','Anh thừa nhận trước heroin đã có những dấu hiệu vấn đề với chất gây nghiện.'),
('date','2021','Một update nữa.'),('recover','VẪN SỐNG.','Vẫn sạch. Vẫn ổn.'),('date','14.09 ↔ 27.09','Hai bài. Cách nhau 13 ngày.'),('fact','LƯU Ý','Tự thuật ẩn danh ≠ hồ sơ y khoa được xác minh.')]
async def tts(p):await edge_tts.Communicate(VO,VOICE,rate='+22%').save(str(p))
def main():
 import sys;out=pathlib.Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True);w=out/'work';w.mkdir(exist_ok=True)
 voice=w/'voice.mp3';asyncio.run(tts(voice));D=probe(voice)
 # investigation pacing: evidence longer, bridges very short
 weights=[2.2,1.5,1.1,1.2,1.0,1.0,1.1,0.7,1.0,0.8,2.1,1.5,1.8,1.2,1.1,1.0,0.8,1.0,1.2,1.0,1.0,0.9,1.6,1.2,0.8,1.4,1.8,1.3]
 ds=[D*x/sum(weights) for x in weights];clips=[]
 for i,(s,sd) in enumerate(zip(SH,ds)):
  im=frame(*s);p=w/f's{i:02}.png';im.save(p)
  c=w/f'c{i:02}.mp4';z="zoompan=z='min(zoom+0.00028,1.045)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30"
  run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-i',str(p),'-t',f'{sd:.3f}','-vf',z+',format=yuv420p','-an','-c:v','libx264','-preset','veryfast','-crf','19',str(c)]);clips.append(c)
 lst=w/'l.txt';lst.write_text('\n'.join("file '"+str(c.resolve())+"'" for c in clips)+'\n');vis=w/'v.mp4';run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(lst),'-c','copy',str(vis)])
 # sound design: low pulse + sparse impacts, ducked under narration
 bed=w/'bed.wav';run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i',f'sine=frequency=48:duration={D}:sample_rate=48000','-af','volume=0.025,lowpass=f=140','-c:a','pcm_s16le',str(bed)])
 final=out/'final.mp4';run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(vis),'-i',str(voice),'-i',str(bed),'-filter_complex','[1:a]volume=1[v];[2:a]volume=.6[b];[v][b]amix=2:duration=first:normalize=0[a]','-map','0:v','-map','[a]','-c:v','libx264','-preset','medium','-crf','19','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(final)])
 # 12-frame visual QA
 th=[]
 for j in range(12):
  q=w/f'q{j}.jpg';run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',f'{D*j/11:.2f}','-i',str(final),'-frames:v','1','-vf','scale=216:384',str(q)]);th.append(Image.open(q).convert('RGB'))
 sheet=Image.new('RGB',(864,1152),(20,21,24))
 for j,x in enumerate(th):sheet.paste(x,((j%4)*216,(j//4)*384))
 sheet.save(out/'qa-contact.jpg',quality=92)
 q={'version':'V5 investigation','duration':D,'shots':len(SH),'target_seconds':[45,55],'browser_evidence_scenes':2,'generic_broll':0,'repeated_shots':0,'resolution':[1080,1920],'voice':VOICE}
 (out/'qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2));print(json.dumps(q,ensure_ascii=False,indent=2))
if __name__=='__main__':main()