from __future__ import annotations

import asyncio
import json
import math
import os
import pathlib
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import edge_tts

W, H, FPS = 1080, 1920, 30
VOICE = "vi-VN-NamMinhNeural"
RATE = "+6%"

SCENES = [
    {
        "date": "13 NGÀY",
        "title": "Từ “chỉ thử một lần”\nđến mũi tiêm đầu tiên",
        "body": "Một chuỗi bài Reddit kéo dài hơn một thập kỷ.",
        "narration": "Mười ba ngày. Đó là khoảng thời gian từ chỉ thử heroin một lần đến đã dùng kể từ đó và vừa tiêm lần đầu, trong chuỗi bài của một tài khoản Reddit.",
        "kind": "hook",
    },
    {
        "date": "14.09.2009",
        "title": "Bài đăng đầu tiên",
        "body": "24 tuổi • bằng thạc sĩ • công việc tốt • gần như không dùng ma túy trước đó",
        "narration": "Ngày 14 tháng 9 năm 2009, Spontaneous H viết rằng mình 24 tuổi, có bằng thạc sĩ, công việc tốt và trước đó gần như không dùng ma túy. Anh vừa thử heroin vì tò mò.",
        "kind": "source",
    },
    {
        "date": "BÀI ĐẦU",
        "title": "Anh tin mình vẫn\nkiểm soát được",
        "body": "Nhiều bình luận cảnh báo. Anh vẫn cho rằng mình hiểu rủi ro.",
        "narration": "Trong bài đầu, anh tin mình có thể dừng lại sau một lần. Nhiều người cảnh báo, nhưng anh cho rằng mình hiểu rủi ro và vẫn kiểm soát được.",
        "kind": "quote",
    },
    {
        "date": "27.09.2009",
        "title": "13 ngày sau",
        "body": "Đã dùng heroin kể từ bài đầu • vừa tiêm lần đầu",
        "narration": "Ngày 27 tháng 9, tài khoản này đăng tiếp: kể từ bài đầu anh đã tiếp tục dùng heroin, và hôm đó vừa tiêm lần đầu.",
        "kind": "turn",
    },
    {
        "date": "2009 → 2010",
        "title": "Nghiện, điều trị,\nrồi suýt chết",
        "body": "Suboxone • nhập viện • nhiều lần cận kề tử vong theo lời tài khoản",
        "narration": "Tháng 10 năm 2009, anh nói mình đã nghiện và bắt đầu điều trị bằng Suboxone. Đến năm 2010, tài khoản còn mô tả một lần suýt chết và phải nằm viện tâm thần.",
        "kind": "down",
    },
    {
        "date": "09.01.2017",
        "title": "Gần 6 năm sạch",
        "body": "“Life is good.” — cập nhật năm 2017",
        "narration": "Tháng 1 năm 2017, sau nhiều năm, Spontaneous H quay lại: gần sáu năm không dùng ma túy hay rượu, và nói cuộc sống đang tốt.",
        "kind": "recover",
    },
    {
        "date": "25.09.2021",
        "title": "Vẫn sống. Vẫn sạch.\nVẫn ổn.",
        "body": "Một cập nhật ngắn sau hơn một thập kỷ từ bài đầu tiên.",
        "narration": "Năm 2021, anh cập nhật thêm: vẫn sống, vẫn sạch và vẫn ổn.",
        "kind": "recover",
    },
    {
        "date": "LƯU Ý",
        "title": "Đây là lời kể ẩn danh",
        "body": "Không thể xác minh độc lập toàn bộ câu chuyện.",
        "narration": "Đây là lời kể của một tài khoản ẩn danh, không thể xác minh độc lập. Nhưng chuỗi bài hơn một thập kỷ là một hồ sơ hiếm về việc mất kiểm soát có thể diễn ra nhanh đến mức nào.",
        "kind": "caveat",
    },
]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def ffprobe_duration(path: pathlib.Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path)
    ], text=True).strip()
    return float(out)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = pathlib.Path("/usr/share/fonts/truetype/dejavu") / name
    return ImageFont.truetype(str(path), size=size)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> str:
    lines: list[str] = []
    for para in text.split("\n"):
        words = para.split()
        cur = ""
        for word in words:
            test = (cur + " " + word).strip()
            if draw.textbbox((0, 0), test, font=fnt)[2] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return "\n".join(lines)


def draw_timeline(draw: ImageDraw.ImageDraw, idx: int) -> None:
    y = 1640
    x0, x1 = 110, 970
    draw.line((x0, y, x1, y), fill=(78, 78, 82), width=4)
    for i in range(len(SCENES)):
        x = int(x0 + (x1 - x0) * i / (len(SCENES) - 1))
        r = 12 if i == idx else 8
        fill = (242, 98, 73) if i <= idx else (112, 112, 118)
        draw.ellipse((x-r, y-r, x+r, y+r), fill=fill)


def source_panel(base: Image.Image, source_path: pathlib.Path) -> None:
    if not source_path.exists():
        return
    src = Image.open(source_path).convert("RGB")
    # crop toward the upper portion where title and post list live
    crop_h = min(src.height, int(src.width * 1.25))
    src = src.crop((0, 0, src.width, crop_h))
    src.thumbnail((820, 760), Image.Resampling.LANCZOS)
    panel = Image.new("RGB", (860, 800), (245, 245, 245))
    px = (panel.width - src.width) // 2
    py = (panel.height - src.height) // 2
    panel.paste(src, (px, py))
    panel = panel.filter(ImageFilter.UnsharpMask(radius=1, percent=115, threshold=3))
    base.paste(panel, (110, 720))


def render_scene(idx: int, scene: dict, source_path: pathlib.Path, out: pathlib.Path) -> None:
    bg = (14, 15, 17)
    im = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(im)

    # subtle editorial grid
    for y in range(0, H, 120):
        draw.line((0, y, W, y), fill=(20, 21, 24), width=1)
    for x in range(0, W, 120):
        draw.line((x, 0, x, H), fill=(20, 21, 24), width=1)

    draw.rounded_rectangle((70, 70, 1010, 1850), radius=44, outline=(52, 53, 58), width=2, fill=(18, 19, 22))
    draw.text((110, 112), "REDDIT ARCHIVE  •  2009—2021", font=font(28, True), fill=(176, 178, 184))
    draw.rounded_rectangle((110, 190, 370, 250), radius=24, fill=(242, 98, 73))
    draw.text((137, 202), scene["date"], font=font(27, True), fill=(18, 19, 22))

    title_font = font(76 if idx != 0 else 72, True)
    title = wrap_text(draw, scene["title"], title_font, 835)
    draw.multiline_text((110, 320), title, font=title_font, fill=(244, 244, 246), spacing=13)

    body_font = font(37, False)
    body = wrap_text(draw, scene["body"], body_font, 835)

    if scene["kind"] == "source":
        source_panel(im, source_path)
        draw = ImageDraw.Draw(im)
        draw.multiline_text((110, 1540), body, font=body_font, fill=(190, 192, 198), spacing=10)
    elif scene["kind"] == "quote":
        draw.rounded_rectangle((110, 770, 970, 1200), radius=32, fill=(29, 30, 35), outline=(58, 60, 66), width=2)
        draw.text((160, 825), "“", font=font(130, True), fill=(242, 98, 73))
        quote = wrap_text(draw, "Mình hiểu rủi ro. Mình vẫn kiểm soát được.", font(54, True), 690)
        draw.multiline_text((225, 860), quote, font=font(54, True), fill=(242, 242, 244), spacing=14)
        draw.multiline_text((110, 1350), body, font=body_font, fill=(190, 192, 198), spacing=10)
    else:
        draw.multiline_text((110, 760), body, font=body_font, fill=(190, 192, 198), spacing=12)
        # visual marker
        if scene["kind"] in {"turn", "down"}:
            draw.line((160, 1090, 160, 1390), fill=(242, 98, 73), width=10)
            draw.ellipse((128, 1058, 192, 1122), fill=(242, 98, 73))
            draw.text((225, 1100), "MẤT KIỂM SOÁT", font=font(44, True), fill=(244, 244, 246))
        elif scene["kind"] == "recover":
            draw.line((160, 1090, 900, 1090), fill=(92, 180, 140), width=8)
            draw.text((160, 1140), "RECOVERY UPDATE", font=font(44, True), fill=(214, 236, 226))
        elif scene["kind"] == "caveat":
            draw.rounded_rectangle((110, 1040, 970, 1315), radius=28, fill=(28, 29, 33), outline=(92, 94, 100), width=2)
            cave = wrap_text(draw, "Tự thuật ẩn danh ≠ hồ sơ y khoa được xác minh.", font(45, True), 760)
            draw.multiline_text((160, 1100), cave, font=font(45, True), fill=(232, 232, 235), spacing=10)
        elif scene["kind"] == "hook":
            draw.text((110, 840), "14.09", font=font(98, True), fill=(242, 98, 73))
            draw.text((440, 840), "→", font=font(98, True), fill=(118, 120, 126))
            draw.text((620, 840), "27.09", font=font(98, True), fill=(242, 98, 73))
            draw.multiline_text((110, 1110), body, font=body_font, fill=(190, 192, 198), spacing=10)

    draw_timeline(draw, idx)
    draw.text((110, 1730), f"{idx+1:02d} / {len(SCENES):02d}", font=font(28, True), fill=(126, 128, 134))
    draw.text((770, 1730), "Nguồn: Reddit archive", font=font(26), fill=(126, 128, 134))
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, quality=95)


async def synthesize(text: str, path: pathlib.Path) -> None:
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
    await communicate.save(str(path))


def chunks(words: list[str], max_words: int = 8) -> list[list[str]]:
    out: list[list[str]] = []
    cur: list[str] = []
    for word in words:
        cur.append(word)
        if len(cur) >= max_words and (word.endswith((".", ",", ":", ";")) or len(cur) >= max_words + 2):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def make_srt(durations: list[float], out: pathlib.Path) -> None:
    entries: list[str] = []
    n = 1
    base = 0.0
    for scene, dur in zip(SCENES, durations):
        parts = chunks(scene["narration"].split(), 7)
        weights = [max(1, len(p)) for p in parts]
        total = sum(weights)
        cur = base
        for p, w in zip(parts, weights):
            seg = dur * w / total
            start = cur
            end = min(base + dur, cur + seg)
            entries.append(f"{n}\n{srt_time(start)} --> {srt_time(end)}\n{' '.join(p)}\n")
            n += 1
            cur = end
        base += dur
    out.write_text("\n".join(entries), encoding="utf-8")


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("job_dir")
    ap.add_argument("out_dir")
    args = ap.parse_args()

    job = pathlib.Path(args.job_dir)
    out = pathlib.Path(args.out_dir)
    work = out / "work"
    frames = work / "frames"
    audio = work / "audio"
    clips = work / "clips"
    for d in (out, work, frames, audio, clips):
        d.mkdir(parents=True, exist_ok=True)

    source = job / "source.png"

    durations: list[float] = []
    for i, scene in enumerate(SCENES):
        frame_path = frames / f"{i:02d}.png"
        audio_path = audio / f"{i:02d}.mp3"
        render_scene(i, scene, source, frame_path)
        asyncio.run(synthesize(scene["narration"], audio_path))
        dur = ffprobe_duration(audio_path)
        durations.append(dur)

        clip_path = clips / f"{i:02d}.mp4"
        # restrained 3% push-in; no flashy transitions
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-loop", "1", "-i", str(frame_path), "-t", f"{dur:.3f}",
            "-vf", f"scale=1112:1978,zoompan=z='min(zoom+0.00012,1.03)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},format=yuv420p",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-movflags", "+faststart", str(clip_path)
        ])

    total = sum(durations)
    print("Narration duration:", total)

    (work / "video_list.txt").write_text("\n".join([f"file '{(clips / f'{i:02d}.mp4').resolve()}'" for i in range(len(SCENES))]) + "\n")
    (work / "audio_list.txt").write_text("\n".join([f"file '{(audio / f'{i:02d}.mp3').resolve()}'" for i in range(len(SCENES))]) + "\n")

    visual = work / "visual.mp4"
    voice = work / "voice.wav"
    ambient = work / "ambient.wav"
    captions = work / "captions.srt"
    make_srt(durations, captions)

    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "video_list.txt"), "-c", "copy", str(visual)])
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "audio_list.txt"), "-c:a", "pcm_s16le", "-ar", "48000", str(voice)])
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", f"sine=frequency=55:sample_rate=48000:duration={total:.3f}",
        "-f", "lavfi", "-i", f"sine=frequency=110:sample_rate=48000:duration={total:.3f}",
        "-filter_complex", "[0:a]volume=0.018[a0];[1:a]volume=0.007[a1];[a0][a1]amix=inputs=2:normalize=0,lowpass=f=230[a]",
        "-map", "[a]", "-c:a", "pcm_s16le", str(ambient)
    ])

    final = out / "final.mp4"
    style = "FontName=DejaVu Sans,FontSize=42,PrimaryColour=&H00FFFFFF,OutlineColour=&H90000000,BackColour=&H74000000,BorderStyle=3,Outline=1,Shadow=0,MarginL=80,MarginR=80,MarginV=170,Alignment=2"
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(visual), "-i", str(voice), "-i", str(ambient),
        "-filter_complex", f"[0:v]subtitles={captions}:force_style='{style}'[v];[1:a]volume=1.0[voice];[2:a]volume=0.55[music];[voice][music]amix=inputs=2:duration=first:normalize=0[a]",
        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "22",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(final)
    ])

    final_dur = ffprobe_duration(final)
    qa = {
        "job": "reddit-heroin-doc",
        "voice": VOICE,
        "voice_rate": RATE,
        "duration_seconds": round(final_dur, 3),
        "target_range_seconds": [45, 60],
        "duration_pass": 45 <= final_dur <= 60,
        "resolution": [W, H],
        "fps": FPS,
        "scene_count": len(SCENES),
        "source_screenshot_present": source.exists(),
        "editorial_caveat_present": True,
        "audio": "NamMinh narration + synthetic ambient bed",
    }
    (out / "qa.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    if not qa["duration_pass"]:
        raise SystemExit(f"duration out of target range: {final_dur:.3f}s")
    print(json.dumps(qa, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
