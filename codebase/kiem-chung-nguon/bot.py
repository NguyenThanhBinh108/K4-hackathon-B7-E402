#!/usr/bin/env python3
"""
bot.py — Bot Discord "Kiểm Chứng Nguồn"

Gan pipeline `source_verify.verify_message()` truc tiep vao Discord, cong them
module `knowledge_index.suggest_reading()` de tra loi "can bo sung kien thuc gi,
doc bai nao".

HAI CHE DO CHAY — DOC KY TRUOC KHI BAT
---------------------------------------
1. SLASH (mac dinh, an toan):  /kiemchung <noi dung>
   Chi chay khi CO NGUOI CHU DONG GOI. Khong doc tin nhan nguoi khac.
   KHONG can quyen "Message Content Intent". Day la che do nen dung khi test
   trong server khoa.

2. AUTO (phai bat co y):  tu quet moi tin nhan trong cac kenh khai bao
   o AUTO_CHANNEL_IDS. Can bat "Message Content Intent" trong Developer Portal.
   CHI bat trong server test cua nhom, hoac trong server khoa khi DA XIN PHEP
   ban to chuc — xem work/huong-dan-discord-bot.md muc "Luat & quyen".

QUYEN RIENG TU — RANG BUOC TU DAT, DUNG BO
--------------------------------------------
- KHONG luu noi dung tin nhan ra dia. Log chi giu: message id, hash cua author
  id, verdict, diem, thoi diem. Du de bao cao so lieu, khong du de doc lai ai
  da noi gi.
- KHONG gui tin nhan cua nguoi that vao API ben thu ba o che do AUTO tru khi
  da xin phep — free tier co the dung data de train (guide §3.4).
- Bot tu bo qua tin nhan cua bot khac va cua chinh no (chong vong lap).

Chay:
    pip install -r requirements.txt
    export DISCORD_BOT_TOKEN=...        # hoac dien vao file .env
    export DISCORD_GUILD_ID=...         # id server test -> slash command hien ngay
    export OPENROUTER_API_KEY=...       # de co AI that
    python3 bot.py
"""

import asyncio
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

try:
    import discord
    from discord import app_commands
except ImportError:
    print(
        "Chua cai discord.py. Chay: pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)

from source_verify import verify_message, format_discord_reply, _load_dotenv  # noqa: E402
import knowledge_index  # noqa: E402

_load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
GUILD_ID = os.environ.get("DISCORD_GUILD_ID", "")
AUTO_CHANNEL_IDS = {
    int(x) for x in os.environ.get("AUTO_CHANNEL_IDS", "").replace(" ", "").split(",") if x.isdigit()
}


def _int_env(name: str, default: int) -> int:
    """Doc bien so nguyen tu moi truong, KHONG chet neu gia tri hong.
    Bot khong duoc phep chet luc khoi dong chi vi mot dong .env go sai."""
    raw = (os.environ.get(name) or "").strip()
    try:
        return int(raw)
    except ValueError:
        if raw:
            print(f"[!] {name}={raw!r} khong phai so — dung mac dinh {default}", file=sys.stderr)
        return default


# Do dai toi thieu de bot tu dong quet — tin ngan kieu "ok", "hihi" khong phai
# claim kien thuc, quet chi ton quota va lam phien kenh.
AUTO_MIN_LEN = _int_env("AUTO_MIN_LEN", 80)
COOLDOWN_SECONDS = _int_env("COOLDOWN_SECONDS", 20)
LOG_PATH = os.path.join(BASE_DIR, "..", "..", "eval", "kiem-chung-nguon", "bot-runs.jsonl")

VERDICT_COLOR = {
    "VERIFIED": 0x23A55A,
    "VERIFIED_SELF_PUBLISHED_TRANSPARENT": 0x23A55A,
    "PARTIALLY_VERIFIED": 0xF0B232,
    "PARTIALLY_CORRECT": 0xF0B232,
    "UNVERIFIED_NO_SOURCE": 0x949BA4,
    "CONTRADICTED": 0xF23F43,
    "OPINION_NOT_APPLICABLE": 0x949BA4,
    "OUT_OF_SCOPE_POLICY_QUESTION": 0x949BA4,
}
VERDICT_LABEL = {
    "VERIFIED": "✅ Đã xác minh",
    "VERIFIED_SELF_PUBLISHED_TRANSPARENT": "✅ Nguồn tự xuất bản, minh bạch",
    "PARTIALLY_VERIFIED": "🟡 Xác minh một phần",
    "PARTIALLY_CORRECT": "🟡 Đúng một phần",
    "UNVERIFIED_NO_SOURCE": "❔ Chưa xác minh được",
    "CONTRADICTED": "❌ Mâu thuẫn với nguồn",
    "OPINION_NOT_APPLICABLE": "💬 Ý kiến cá nhân",
    "OUT_OF_SCOPE_POLICY_QUESTION": "🔒 Ngoài phạm vi — câu hỏi chính sách",
}

_last_call: dict[int, float] = {}


def _anon(user_id: int) -> str:
    """Bam author id — du de dem 'bao nhieu nguoi dung', khong truy nguoc ra ai."""
    return hashlib.sha256(f"kcn:{user_id}".encode()).hexdigest()[:12]


def log_run(message_id: int, user_id: int, result, source: str) -> None:
    """Ghi log KHONG chua noi dung tin nhan. Dung cho bang so lieu trong spec §7."""
    rec = {
        "at": datetime.now(timezone.utc).isoformat(),
        "source": source,                    # "slash" | "auto"
        "message_id": str(message_id),
        "user": _anon(user_id),
        "verdict": result.verdict,
        "score": result.final_credibility_score,
        "risk_flag": result.risk_flag,
        "mode": result.mode,
        "domain_tier": result.domain_tier,
        "content_extracted": result.content_extracted,
    }
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


REFUSALS = [
    "Câu này nằm ngoài phạm vi của mình rồi 😅",
    "Cái này mình chịu thật — ngoài vùng phủ sóng của mình 🙃",
    "Mình tra khắp tài liệu khoá mà không thấy gì về chuyện này 🤔",
]


def build_answer_embed(result) -> discord.Embed:
    """Luong HOI KIEN THUC — tra loi THEO TAI LIEU, kem nguon. Khong co
    'do tin cay' o day: nguoi ta hoi bai chu khong chia se claim de kiem chung."""
    emb = discord.Embed(
        title="📖 Trả lời theo tài liệu của khoá",
        description=result.answer[:2000],
        color=0x5865F2,
    )
    lines = []
    for it in (result.reading or []):
        heading = f" · {it['heading']}" if it.get("heading") else ""
        lines.append(f"**`[{it['code']}]`** {it['lecture']}{heading}\n> {it['quote']}")
    emb.add_field(
        name="Nguồn — mở ra kiểm lại được",
        value="\n\n".join(lines)[:1024] or "—",
        inline=False,
    )
    emb.set_footer(text="Trả lời dựa hoàn toàn trên tài liệu khoá · không có trong tài liệu thì mình nói không biết")
    return emb


def build_refusal_embed(result, query: str) -> discord.Embed:
    """Luong NGOAI PHAM VI — tu choi vui ve + goi y cau hoi khac hoi duoc.
    Tu choi cut lung lam nguoi dung bo di; goi y cho ho biet HOI GI THI DUOC."""
    idx = (len(query) + len(result.message_id)) % len(REFUSALS)   # doi cau, khong ngau nhien
    emb = discord.Embed(
        title=REFUSALS[idx],
        description=(
            "Mình chỉ trả lời được những gì **có trong tài liệu và bài giảng của khoá** "
            "— thông báo, slide, transcript 6 buổi. Ngoài đó thì mình không đoán, "
            "vì đoán sai còn hại hơn không trả lời."
        ),
        color=0xF0B232,
    )
    tops = result.suggested_topics or []
    if tops:
        emb.add_field(
            name="💡 Thử hỏi mình mấy chủ đề này xem",
            value="\n".join(f"• **{t['topic']}**\n  ↳ *{t['lecture']}* · {t['segments']} đoạn"
                            for t in tops)[:1024],
            inline=False,
        )
    emb.add_field(
        name="Hoặc",
        value="Dán một **link** (paper / GitHub / docs) để mình kiểm chứng nguồn giúp bạn.",
        inline=False,
    )
    emb.set_footer(text="Bot kiểm chứng nguồn · prototype hackathon")
    return emb


def build_campus_embed(result) -> discord.Embed:
    """FIX-18 — luong CAMPUS (tich hop tu Campus Companion cua Linh & Liem).
    Ba quyet dinh, moi cai mot mau va mot hanh dong tiep theo khac nhau."""
    dec = result.campus_decision
    src = result.campus_source or {}

    if dec == "answer":
        emb = discord.Embed(title="🏫 Thông tin campus / quy định khoá",
                            description=result.answer[:2000], color=0x23A55A)
        emb.add_field(
            name="Nguồn chính thức",
            value=f"**{src.get('source_title','?')}**\n{src.get('source_location','')}\n"
                  f"`{src.get('id','?')}` · cập nhật {src.get('last_updated','?')}",
            inline=False,
        )
    elif dec == "hoi_lai":
        emb = discord.Embed(title="🤔 Cho mình hỏi lại cho chắc",
                            description=result.answer[:2000], color=0x7C8CFF)
        emb.add_field(
            name="Vì sao mình hỏi lại",
            value="Câu này có thể rơi vào nhiều mục quy định khác nhau. "
                  "Trả lời nhầm mục còn tệ hơn hỏi thêm một câu.",
            inline=False,
        )
    else:   # chuyen_lab_coach
        emb = discord.Embed(
            title="📮 Chuyển Lab Coach",
            description=result.answer[:2000] or
                        "Thông tin này mình chưa có trong nguồn chính thức nên không đoán.",
            color=0xF0B232,
        )
        emb.add_field(
            name="Vì sao không tự trả lời",
            value="Thông tin thay đổi theo ngày, hoặc nằm ngoài nguồn chính thức mình có. "
                  "Sai một chi tiết như giờ giấc/phí/quy định là bạn chịu hậu quả trực tiếp.",
            inline=False,
        )
        emb.add_field(name="Nên hỏi ở đâu", value="`#lab-support` — hoặc nhắn trực tiếp Lab Coach.",
                      inline=False)

    emb.set_footer(text="Campus Companion · trả lời trong phạm vi nguồn chính thức của khoá")
    return emb


def build_embed(result, reading: dict) -> discord.Embed:
    # FIX-17/18 — bốn luồng khác nhau, không nhét tất cả vào khung "kiểm chứng"
    if result.intent == "hoi_campus":
        return build_campus_embed(result)
    if result.intent == "hoi_kien_thuc" and result.answer:
        return build_answer_embed(result)
    if result.intent == "ngoai_pham_vi" and not result.risk_flag:
        return build_refusal_embed(result, result.text)

    color = 0xF23F43 if result.risk_flag else VERDICT_COLOR.get(result.verdict, 0x949BA4)
    label = VERDICT_LABEL.get(result.verdict, "❔ Chưa xác minh được")

    if result.score_applicable:
        title = f"{label} — độ tin cậy {result.final_credibility_score}/100"
    else:
        title = f"{label} — không chấm độ tin cậy"

    emb = discord.Embed(title=title, description=result.explanation[:2000], color=color)

    if result.risk_flag:
        reasons = "\n".join(f"⚠️ {r.split('] ', 1)[-1]}" for r in (result.risk_reasons or [])[:4])
        emb.add_field(
            name="🚨 CẢNH BÁO RỦI RO CAO — đọc trước khi làm theo",
            value=reasons[:1024] or "—",
            inline=False,
        )

    if result.urls:
        src = f"{result.urls[0]}\nloại nguồn: `{result.domain_tier}` · truy cập được: `{result.url_reachable}`"
        if len(result.urls) > 1:
            src += f"\n(+{len(result.urls) - 1} link khác chưa kiểm — chỉ kiểm link đầu tiên)"
        if result.content_extracted:
            src += "\n✅ Đã đối chiếu với nội dung thật trích xuất từ link"
        elif result.extract_reason == "thieu-thu-vien":
            src += "\n⛔ Chưa cài thư viện trích xuất — chỉ đánh giá theo độ uy tín domain"
        else:
            src += "\n⚠️ Không trích xuất được nội dung thật — chỉ đánh giá theo độ uy tín domain"
        emb.add_field(name="Nguồn", value=src[:1024], inline=False)
    else:
        emb.add_field(name="Nguồn", value="Không có link đính kèm", inline=False)

    # "Can bo sung kien thuc gi, doc bai nao" — chi tu tai lieu CUA KHOA
    if reading.get("found"):
        lines = []
        for it in reading["items"][:2]:
            lines.append(f"**`[{it['code']}]`** {it['lecture']}\n> {it['quote']}")
        emb.add_field(name="📚 Nên đọc lại trong bài giảng của khoá", value="\n\n".join(lines)[:1024], inline=False)
    else:
        emb.add_field(
            name="📚 Nên đọc lại trong bài giảng của khoá",
            value="Không tìm thấy đoạn bài giảng nào liên quan — mình không gợi ý bừa.",
            inline=False,
        )

    if result.recommended_action:
        emb.add_field(name="Gợi ý tiếp theo", value=result.recommended_action[:1024], inline=False)

    foot = "Bot kiểm chứng nguồn · prototype hackathon"
    if result.mode == "MOCK":
        foot = "⚠️ MOCK MODE — chưa phải AI thật · " + foot
    emb.set_footer(text=foot)
    return emb


async def run_verification(text: str, msg_id: str) -> tuple[object, dict]:
    """Chay pipeline trong thread rieng — verify_message() goi mang va LLM,
    chay thang trong event loop se treo ca bot.

    FIX-16: khong con goi suggest_reading() rieng o day nua. Tu khoa dua ung
    vien vao ngay trong prompt kiem chung, LLM loc lai — nen `result.reading`
    da la danh sach doan DA DUOC XAC NHAN lien quan."""
    result = await asyncio.to_thread(verify_message, {"id": msg_id, "author": "?", "text": text})
    reading = {"found": bool(result.reading), "items": result.reading or []}
    return result, reading


class KcnBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        # Chi bat message_content khi that su chay che do AUTO. Day la
        # privileged intent — phai bat them trong Developer Portal.
        intents.message_content = bool(AUTO_CHANNEL_IDS)
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        if GUILD_ID.isdigit():
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)   # hien ngay, khong cho 1 tieng
            print(f"Da dong bo slash command vao guild {GUILD_ID}")
        else:
            await self.tree.sync()
            print("Da dong bo slash command toan cuc (co the cho toi 1 gio moi hien)")

    async def on_ready(self) -> None:
        print(f"Bot online: {self.user}", flush=True)
        print(f"Che do AUTO: {'BAT cho kenh ' + str(AUTO_CHANNEL_IDS) if AUTO_CHANNEL_IDS else 'TAT (chi slash command)'}", flush=True)
        try:
            n = len(knowledge_index.get_index())
            print(f"Knowledge index: {n} doan bai giang", flush=True)
        except FileNotFoundError as e:
            print(f"[!] {e}\n    -> tinh nang 'nen doc lai bai nao' se khong chay", file=sys.stderr)

    async def on_message(self, message: discord.Message) -> None:
        if not AUTO_CHANNEL_IDS:
            return
        if message.author.bot or message.author.id == self.user.id:
            return                                    # chong vong lap
        if message.channel.id not in AUTO_CHANNEL_IDS:
            return
        if len(message.content) < AUTO_MIN_LEN:
            return                                    # tin ngan khong phai claim

        now = time.time()
        if now - _last_call.get(message.author.id, 0) < COOLDOWN_SECONDS:
            return                                    # chong spam quota
        _last_call[message.author.id] = now

        async with message.channel.typing():
            try:
                result, reading = await run_verification(message.content, str(message.id))
            except Exception as e:                    # khong bao gio de bot chet vi 1 tin
                print(f"[loi] {type(e).__name__}: {e}", file=sys.stderr)
                return
        log_run(message.id, message.author.id, result, "auto")
        await message.reply(embed=build_embed(result, reading), mention_author=False)


client = KcnBot()


@client.tree.command(name="kiemchung", description="Kiểm chứng một nội dung/link được chia sẻ")
@app_commands.describe(noi_dung="Dán nội dung hoặc link cần kiểm chứng")
async def kiemchung(interaction: discord.Interaction, noi_dung: str) -> None:
    now = time.time()
    if now - _last_call.get(interaction.user.id, 0) < COOLDOWN_SECONDS:
        await interaction.response.send_message(
            f"Bạn vừa gọi rồi — chờ {COOLDOWN_SECONDS}s giữa hai lượt nhé (tránh cháy quota AI).",
            ephemeral=True,
        )
        return
    _last_call[interaction.user.id] = now

    # Pipeline mat vai giay toi vai chuc giay -> phai defer, khong Discord bao timeout
    await interaction.response.defer(thinking=True)
    try:
        result, reading = await run_verification(noi_dung, str(interaction.id))
    except Exception as e:
        await interaction.followup.send(f"Có lỗi khi kiểm chứng: `{type(e).__name__}`. Thử lại sau nhé.")
        print(f"[loi] {type(e).__name__}: {e}", file=sys.stderr)
        return

    log_run(interaction.id, interaction.user.id, result, "slash")
    await interaction.followup.send(embed=build_embed(result, reading))


@client.tree.command(name="kcn-status", description="Bot đang chạy ở chế độ nào")
async def status(interaction: discord.Interaction) -> None:
    has_key = any(
        os.environ.get(k) for k in ("OPENROUTER_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY")
    )
    try:
        n_seg = len(knowledge_index.get_index())
    except Exception:
        n_seg = 0
    await interaction.response.send_message(
        f"**Chế độ AI:** {'AI thật' if has_key else '⚠️ MOCK (chưa cắm API key)'}\n"
        f"**Tự động quét:** {'bật ở ' + str(len(AUTO_CHANNEL_IDS)) + ' kênh' if AUTO_CHANNEL_IDS else 'tắt — chỉ chạy khi gọi /kiemchung'}\n"
        f"**Bài giảng đã nạp:** {n_seg} đoạn\n"
        f"**Ghi log:** chỉ verdict + điểm + id đã băm, **không lưu nội dung tin nhắn**",
        ephemeral=True,
    )


if __name__ == "__main__":
    if not TOKEN:
        print(
            "Thieu DISCORD_BOT_TOKEN.\n"
            "  cp .env.example .env  roi dien token, hoac: export DISCORD_BOT_TOKEN=...",
            file=sys.stderr,
        )
        sys.exit(1)
    client.run(TOKEN)
