from __future__ import annotations
import asyncio, json, pathlib, subprocess, textwrap, math
from PIL import Image, ImageDraw, ImageFont
import edge_tts

W,H,FPS=1080,1920,30
BG=(11,12,15); FG=(245,246,248); MUT=(155,160,168); OR=(255,69,0); CARD=(24,26,31); GREEN=(83,184,135)
VOICE='vi-VN-NamMinhNeural'

def run(x): subprocess.run(x,check=True)
def dur(p): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)],text=True).strip())
def font(n,b=False):
 p='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if b else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; return ImageFont.truetype(p,n)
def wrap(d,s,f,w):
 out=[]
 for para in s.split('\n'):
  cur=''
  for word in para.split():
   q=(cur+' '+word).strip()
   if d.textbbox((0,0),q,font=f)[2]<=w: cur=q
   else:
    if cur: out.append(cur)
    cur=word
  if cur: out.append(cur)
 return '\n'.join(out)
def card(kind,head,body,tag='REDDIT ARCHIVE',small=''):
 im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
 d.text((70,80),tag,font=font(24,True),fill=OR); d.line((70,130,1010,130),fill=(48,51,58),width=2)
 if kind=='post':
  d.rounded_rectangle((65,235,1015,1425),36,fill=(242,243,245)); d.rectangle((65,235,1015,330),fill=OR); d.text((105,260),'reddit  •  r/IAmA',font=font(31,True),fill='white')
  d.multiline_text((105,400),wrap(d,head,font(50,True),820),font=font(50,True),fill=(28,30,34),spacing=14)
  d.multiline_text((105,820),wrap(d,body,font(31),820),font=font(31),fill=(65,68,73),spacing=14)
 elif kind=='quote':
  d.text((70,300),head,font=font(35,True),fill=MUT); d.rounded_rectangle((70,430,1010,1260),36,fill=CARD,outline=(63,67,76),width=2)
  d.text((110,475),'“',font=font(110,True),fill=OR); d.multiline_text((150,610),wrap(d,body,font(54,True),760),font=font(54,True),fill=FG,spacing=18)
 elif kind=='date':
  d.text((70,330),head,font=font(95,True),fill=FG); d.multiline_text((70,520),wrap(d,body,font(48,True),880),font=font(48,True),fill=OR,spacing=16)
 elif kind=='fact':
  d.text((70,330),head,font=font(60,True),fill=FG); d.multiline_text((70,560),wrap(d,body,font(42),880),font=font(42),fill=MUT,spacing=18)
 elif kind=='recover':
  d.text((70,330),head,font=font(78,True),fill=GREEN); d.multiline_text((70,540),wrap(d,body,font(48,True),880),font=font(48,True),fill=FG,spacing=18)
 d.text((70,1735),small,font=font(23),fill=(105,109,118)); d.text((70,1790),'Anonymous self-report • source-driven reconstruction',font=font(20),fill=(86,90,98))
 return im

SHOTS=[
 ('post','14 SEP 2009','I did Heroin yesterday. I am not a drug user... AMA','Original post'),
 ('date','14.09.2009','Một bài Reddit bắt đầu câu chuyện.',''),
 ('quote','CÂU MỞ ĐẦU','“Tôi vừa thử heroin hôm qua.”',''),
 ('fact','24 tuổi','Theo chính bài đăng đầu tiên.',''),
 ('fact','Bằng thạc sĩ','Anh dùng chi tiết này để mô tả một cuộc sống “bình thường”.',''),
 ('fact','Công việc lương tốt','Và nói mình gần như không dùng ma túy trước đó.',''),
 ('quote','PHẦN BÌNH LUẬN','Nhiều người bảo anh đừng thử lại.',''),
 ('quote','NHƯNG','Anh tin mình hiểu rủi ro.',''),
 ('quote','VÀ','Anh tin mình có thể dừng.',''),
 ('date','13 NGÀY','14.09 → 27.09',''),
 ('post','27 SEP 2009','Two weeks ago I tried heroin once...','Update 13 days later'),
 ('quote','UPDATE','“Tôi đã tiếp tục dùng kể từ bài đầu.”',''),
 ('quote','CÙNG NGÀY','“Hôm nay vừa tiêm lần đầu.”',''),
 ('date','13 NGÀY','Không phải “nghiện tức thì sau một liều”.',''),
 ('fact','Điểm chính xác','Anh thử → tiếp tục dùng → mất kiểm soát rất nhanh.',''),
 ('fact','Withdrawal','Các bài sau mô tả triệu chứng cai và craving.',''),
 ('fact','Điều trị','Anh nói mình bắt đầu Suboxone.',''),
 ('date','2010','Câu chuyện tiếp tục xấu đi.',''),
 ('fact','Relapse','Các cập nhật mô tả việc quay lại sử dụng.',''),
 ('fact','Overdose','Một cập nhật kể về fentanyl và nhiều chất khác.',''),
 ('fact','Narcan','Anh nói nhân viên cấp cứu đã dùng nhiều liều.',''),
 ('fact','Bệnh viện','Sau đó là nhập viện và cai nghiện.',''),
 ('fact','Rehab','Hai ngày sau, theo update, anh đi residential rehab.',''),
 ('date','7 NĂM SAU','Tài khoản xuất hiện trở lại.',''),
 ('recover','2017','“Gần 6 năm sạch. Life is good.”',''),
 ('fact','Một correction quan trọng','Anh thừa nhận trước heroin đã có những dấu hiệu vấn đề với chất gây nghiện.',''),
 ('date','2021','Một update nữa.',''),
 ('recover','Vẫn sống.','Vẫn sạch. Vẫn ổn.',''),
 ('post','14 SEP 2009  ↔  27 SEP 2009','Hai bài đăng. Cách nhau 13 ngày.','Timeline'),
 ('fact','Lưu ý','Đây là lời kể của một tài khoản ẩn danh; không thể xác minh độc lập toàn bộ như hồ sơ y khoa.','')
]
VO=[
 'Ngày 14 tháng 9 năm 2009, một tài khoản Reddit đăng: Tôi vừa thử heroin hôm qua.',
 'Anh nói mình 24 tuổi, có bằng thạc sĩ, công việc lương tốt, và gần như không dùng ma túy trước đó.',
 'Trong phần bình luận, nhiều người cảnh báo. Nhưng điểm đáng chú ý là sự tự tin: anh tin mình hiểu rủi ro và có thể dừng lại.',
 'Mười ba ngày sau, ngày 27 tháng 9, cùng tài khoản quay lại. Anh nói mình đã tiếp tục dùng heroin kể từ bài đầu, và hôm đó vừa tiêm lần đầu.',
 'Đây không phải câu chuyện một liều chắc chắn khiến mọi người nghiện. Chính xác hơn: sau lần thử đầu, anh tiếp tục dùng, rồi mất kiểm soát rất nhanh.',
 'Các cập nhật sau mô tả nghiện, điều trị, relapse, overdose, Narcan, bệnh viện và rehab.',
 'Nhưng câu chuyện không kết thúc ở đó. Năm 2017, anh quay lại và nói mình đã gần sáu năm sạch ma túy và rượu. Anh cũng thừa nhận cuộc sống trước lần thử đầu tiên có nhiều dấu hiệu cảnh báo hơn mình từng nghĩ.',
 'Năm 2021, anh đăng thêm một câu ngắn: vẫn sống, vẫn sạch, và vẫn ổn.',
 'Đây là lịch sử tự thuật của một tài khoản ẩn danh, không phải hồ sơ y khoa được xác minh độc lập. Nhưng chỉ cần đặt hai bài đăng cách nhau 13 ngày cạnh nhau, timeline đã đủ mạnh.'
]
async def tts(txt,p): await edge_tts.Communicate(txt,VOICE,rate='+16%').save(str(p))
def main():
 import sys; out=pathlib.Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=True); work=out/'work'; work.mkdir(exist_ok=True)
 voice=work/'voice.mp3'; asyncio.run(tts(' '.join(VO),voice)); D=dur(voice)
 # shot weights deliberately vary; evidence gets longer, bridge cards shorter
 weights=[2.8,1.2,1.8,1.0,1.0,1.2,1.4,1.3,1.2,1.6,2.8,1.8,2.1,1.5,1.8,1.2,1.2,1.2,1.1,1.3,1.2,1.2,1.3,1.4,2.1,2.0,1.2,2.0,2.8,2.4]
 scale=D/sum(weights); ds=[x*scale for x in weights]
 clips=[]
 for i,(spec,sd) in enumerate(zip(SHOTS,ds)):
  im=card(*spec); png=work/f's{i:02d}.png'; im.save(png)
  mp4=work/f'c{i:02d}.mp4'; motion="zoompan=z='min(zoom+0.00018,1.035)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30"
  run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-i',str(png),'-t',f'{sd:.3f}','-vf',motion+',format=yuv420p','-an','-c:v','libx264','-preset','veryfast','-crf','20',str(mp4)]); clips.append(mp4)
 lst=work/'list.txt'; lst.write_text('\n'.join("file '"+str(x.resolve())+"'" for x in clips)+'\n')
 vis=work/'visual.mp4'; run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(lst),'-c','copy',str(vis)])
 final=out/'final.mp4'; run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(vis),'-i',str(voice),'-map','0:v','-map','1:a','-c:v','libx264','-preset','medium','-crf','20','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(final)])
 # QA contact sheet, 12 temporal samples
 thumbs=[]
 for j in range(12):
  t=max(0,min(D-.1,D*j/11)); p=work/f'q{j}.jpg'; run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',f'{t:.2f}','-i',str(final),'-frames:v','1','-vf','scale=216:384',str(p)]); thumbs.append(Image.open(p).convert('RGB'))
 sh=Image.new('RGB',(864,1152),(20,21,24))
 for j,x in enumerate(thumbs): sh.paste(x,((j%4)*216,(j//4)*384))
 sh.save(out/'qa-contact.jpg',quality=90)
 qa={'duration':D,'shots':len(SHOTS),'unique_shot_assets':len(SHOTS),'repeated_shots':0,'source_driven':True,'generic_broll':0,'resolution':[1080,1920],'voice':VOICE}
 (out/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
 print(json.dumps(qa,ensure_ascii=False,indent=2))
if __name__=='__main__': main()