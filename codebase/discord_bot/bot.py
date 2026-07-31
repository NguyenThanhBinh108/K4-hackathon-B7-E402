"""
VinAI Knowledge Assistant — Discord Bot
Thin client: nhận lệnh Discord → gọi FastAPI backend → trả kết quả
Prefix: /ka hoặc mention @bot

Cách dùng trong Discord:
  /ka hỏi Transformer là gì?
  /ka tóm tắt [reply vào message có attachment PDF]
  /ka tổng hợp [paste đoạn chat]
  /ka kb     — xem danh sách tài liệu
  /ka help   — hướng dẫn
"""
import os
import sys
import asyncio
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# ── Cấu hình ─────────────────────────────────────────────────────────
DISCORD_TOKEN  = os.getenv("DISCORD_BOT_TOKEN", "")
API_BASE       = os.getenv("KB_API_BASE", "http://localhost:8000")
PREFIX         = "!ka"
MAX_MSG_LEN    = 1900  # Discord limit 2000, để buffer

# ── Bot setup ─────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX + " ", intents=intents, help_command=None)


# ══ EVENTS ════════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    print(f"✅ VinAI Knowledge Bot online: {bot.user}")
    print(f"   Prefix: {PREFIX}")
    print(f"   API: {API_BASE}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Knowledge Base · !ka help"
        )
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.reply("❓ Lệnh không hợp lệ. Dùng `!ka help` để xem hướng dẫn.", mention_author=False)
    else:
        await ctx.reply(f"❌ Lỗi: {str(error)[:200]}", mention_author=False)


@bot.event
async def on_message(message: discord.Message):
    """
    Auto-detect file đính kèm khi gửi vào kênh — không cần gõ lệnh `!ka tóm tắt`.
    - PDF/Word/PowerPoint/Text → tự động tóm tắt (giống lệnh tóm tắt thủ công).
    - Video/audio → nhận diện được nhưng KHÔNG xử lý nội dung (non-goal đã khai trong spec.md),
      trả lời từ chối đúng cách kèm hướng dẫn thay vì im lặng hoặc báo lỗi.
    - Định dạng khác (ảnh, gif, zip...) → im lặng bỏ qua, không spam kênh.
    - Tin nhắn có prefix "!ka " vẫn xử lý như lệnh bình thường (không đổi hành vi cũ).
    """
    if message.author == bot.user:
        return

    # Tin nhắn dùng lệnh tường minh (vd "!ka tóm tắt") vẫn xử lý qua command bình thường bên
    # dưới — chỉ auto-detect attachment khi KHÔNG phải lệnh, tránh xử lý trùng 2 lần.
    if not message.content.startswith(PREFIX + " "):
        for attachment in message.attachments:
            name = attachment.filename.lower()
            if name.endswith(PROCESSABLE_EXTENSIONS):
                await _summarize_attachment(message, attachment, silent_on_unsupported=True)
            elif name.endswith(VIDEO_EXTENSIONS):
                await message.reply(
                    "💭 Video/audio chưa hỗ trợ tự động tóm tắt — cần transcript dạng text. "
                    "Xem #tài-nguyên hoặc paste text thủ công, hoặc dùng `!ka tổng hợp`.",
                    mention_author=False
                )
            # Định dạng khác: bỏ qua, không phải trách nhiệm của bot này

    await bot.process_commands(message)


# ══ COMMANDS ══════════════════════════════════════════════════════════

@bot.command(name="help", aliases=["h", "hướng dẫn"])
async def cmd_help(ctx):
    """Hiện hướng dẫn sử dụng"""
    embed = discord.Embed(
        title="⚡ VinAI Knowledge Assistant",
        description="Trợ lý kiến thức AI/ML từ tài liệu khoá VinAI Thực Chiến",
        color=0x5865F2
    )
    embed.add_field(
        name="📚 Hỏi về kiến thức",
        value="`!ka hỏi <câu hỏi>`\nVí dụ: `!ka hỏi Transformer là gì?`",
        inline=False
    )
    embed.add_field(
        name="📄 Tóm tắt PDF",
        value="`!ka tóm tắt` + đính kèm file PDF\nhoặc reply vào message có PDF",
        inline=False
    )
    embed.add_field(
        name="🔮 Tổng hợp chat",
        value="`!ka tổng hợp <nội dung chat>`",
        inline=False
    )
    embed.add_field(
        name="📂 Xem tài liệu",
        value="`!ka kb` — danh sách tài liệu trong KB",
        inline=False
    )
    embed.set_footer(text="📌 Phạm vi: Chỉ kiến thức AI/ML từ tài liệu khoá học. Deadline/điểm → hỏi Lab Coach.")
    await ctx.reply(embed=embed, mention_author=False)


@bot.command(name="hỏi", aliases=["ask", "q"])
async def cmd_ask(ctx, *, question: str = ""):
    """Hỏi về kiến thức AI/ML từ Knowledge Base"""
    if not question:
        await ctx.reply("❓ Bạn chưa nhập câu hỏi. Ví dụ: `!ka hỏi Transformer là gì?`", mention_author=False)
        return

    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_BASE}/api/chat",
                    json={"message": question, "session_id": str(ctx.author.id)},
                    timeout=aiohttp.ClientTimeout(total=45)
                ) as resp:
                    data = await resp.json()
        except aiohttp.ClientConnectorError:
            await ctx.reply("❌ Không kết nối được tới backend. Kiểm tra server đang chạy chưa.", mention_author=False)
            return
        except Exception as e:
            await ctx.reply(f"❌ Lỗi: {str(e)[:200]}", mention_author=False)
            return

    # Build embed
    if data.get("is_out_of_scope"):
        embed = discord.Embed(
            description=f"⚠️ **Ngoài phạm vi**\n\n{data['response']}\n\n_Đây là giới hạn thiết kế — mình chỉ trả lời về kiến thức AI/ML._",
            color=0xED4245
        )
    elif not data.get("found_in_kb"):
        embed = discord.Embed(
            description=f"💭 **Câu hỏi chưa rõ**\n\n{data['response']}",
            color=0xFBBF24
        )
    else:
        response_text = data.get("response", "")
        if len(response_text) > 1024:
            response_text = response_text[:1021] + "..."

        embed = discord.Embed(
            description=response_text,
            color=0x5865F2
        )

        # Citations
        citations = data.get("citations", [])
        if citations:
            embed.add_field(
                name="📎 Trích dẫn",
                value=" · ".join(f"`{c}`" for c in citations[:6]),
                inline=False
            )

        # Suggested docs
        suggested = [d for d in data.get("suggested_docs", []) if d]
        if suggested:
            embed.add_field(
                name="📚 Xem thêm",
                value=", ".join(f"**{d}**" for d in suggested[:3]),
                inline=False
            )

        embed.set_footer(text="🤖 Tóm tắt tự động — xem nguyên văn để xác nhận · !ka help")

    embed.set_author(name="VinAI Knowledge Assistant ⚡")
    await ctx.reply(embed=embed, mention_author=False)


# ── Loại file auto-detect được (khớp services/pdf_service.py bên backend) ──
PROCESSABLE_EXTENSIONS = (".pdf", ".docx", ".doc", ".pptx", ".ppt", ".txt", ".md")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".mp3", ".wav", ".m4a")


async def _summarize_attachment(reply_target, attachment, silent_on_unsupported: bool = False):
    """Tải attachment + gọi /api/summarize + reply embed.
    Dùng chung cho lệnh `!ka tóm tắt` và auto-detect trong on_message.
    reply_target: Context hoặc Message — cả hai đều có .reply() và .channel.
    silent_on_unsupported: True khi gọi từ auto-detect (không phải lệnh tường minh) —
        bỏ qua lặng lẽ nếu backend báo 400 (định dạng không hỗ trợ), không spam kênh.
    """
    async with reply_target.channel.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as r:
                    file_bytes = await r.read()

                form = aiohttp.FormData()
                form.add_field("file", file_bytes, filename=attachment.filename,
                                content_type="application/octet-stream")

                async with session.post(
                    f"{API_BASE}/api/summarize",
                    data=form,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    data = await resp.json()

                    if resp.status == 422:
                        # Video/audio hoặc lỗi đọc file — từ chối đúng cách, không phải lỗi hệ thống
                        await reply_target.reply(f"💭 {data.get('detail', 'Không xử lý được file này.')}",
                                                  mention_author=False)
                        return
                    if resp.status == 400:
                        # Định dạng không hỗ trợ — auto-detect thì im lặng bỏ qua, lệnh tường minh thì báo rõ
                        if not silent_on_unsupported:
                            await reply_target.reply(f"❌ {data.get('detail', 'Định dạng không hỗ trợ.')}",
                                                      mention_author=False)
                        return
                    if not resp.ok:
                        raise Exception(data.get("detail", "Lỗi không xác định"))

        except aiohttp.ClientConnectorError:
            if not silent_on_unsupported:
                await reply_target.reply("❌ Không kết nối được backend.", mention_author=False)
            return
        except Exception as e:
            if not silent_on_unsupported:
                await reply_target.reply(f"❌ {str(e)[:300]}", mention_author=False)
            return

    s = data.get("summary", {})
    concepts = (s.get("key_concepts") or [])[:5]
    takeaways = (s.get("key_takeaways") or [])[:3]
    citations = (s.get("citations") or [])[:4]

    embed = discord.Embed(
        title=f"📄 {s.get('title', attachment.filename)}",
        color=0x5865F2
    )
    embed.add_field(name="Module", value=s.get("module", "—"), inline=True)
    embed.add_field(name="Cấp độ", value=s.get("level", "—"), inline=True)
    embed.add_field(name="Số trang", value=str(data.get("page_count", "—")), inline=True)

    if concepts:
        embed.add_field(name="Khái niệm chính", value=", ".join(f"`{c}`" for c in concepts), inline=False)

    if takeaways:
        embed.add_field(
            name="Key Takeaways",
            value="\n".join(f"• {t[:150]}" for t in takeaways),
            inline=False
        )

    if citations:
        embed.add_field(name="Citations", value=" · ".join(f"`{c}`" for c in citations), inline=False)

    if s.get("note"):
        embed.add_field(name="Ghi chú", value=s["note"][:200], inline=False)

    conf = s.get("reliability_score", 88)
    embed.set_footer(text=f"🤖 Độ tin cậy: {conf}% · Tóm tắt tự động — xem nguyên văn để xác nhận")
    embed.set_author(name="VinAI Knowledge Assistant ⚡")

    await reply_target.reply(embed=embed, mention_author=False)


@bot.command(name="tóm tắt", aliases=["tomtat", "summary", "pdf"])
async def cmd_summarize(ctx):
    """Tóm tắt file đính kèm (PDF/Word/PowerPoint/Text)"""
    # Check attachments (current message or replied message)
    attachments = ctx.message.attachments

    if not attachments and ctx.message.reference:
        try:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            attachments = ref_msg.attachments
        except Exception:
            pass

    doc_attachment = None
    for att in attachments:
        if att.filename.lower().endswith(PROCESSABLE_EXTENSIONS + VIDEO_EXTENSIONS):
            doc_attachment = att
            break

    if not doc_attachment:
        await ctx.reply(
            "📎 **Cách dùng:** Đính kèm file (PDF/Word/PowerPoint/Text) kèm lệnh `!ka tóm tắt`\n"
            "hoặc reply vào message có file và gõ `!ka tóm tắt`",
            mention_author=False
        )
        return

    await _summarize_attachment(ctx, doc_attachment, silent_on_unsupported=False)


@bot.command(name="tổng hợp", aliases=["tonghop", "synthesize", "synth"])
async def cmd_synthesize(ctx, *, chat_text: str = ""):
    """Tổng hợp đoạn chat Discord"""
    if not chat_text:
        await ctx.reply(
            "🔮 **Cách dùng:** `!ka tổng hợp <paste đoạn chat vào đây>`\n"
            "Cần ít nhất 50 ký tự.",
            mention_author=False
        )
        return

    if len(chat_text) < 50:
        await ctx.reply("❌ Cần ít nhất 50 ký tự để tổng hợp.", mention_author=False)
        return

    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_BASE}/api/synthesize",
                    json={"chat_text": chat_text},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    data = await resp.json()
                    if not resp.ok:
                        raise Exception(data.get("detail", "Lỗi"))
        except Exception as e:
            await ctx.reply(f"❌ {str(e)[:200]}", mention_author=False)
            return

    if data.get("error"):
        await ctx.reply(f"❌ {data['error']}", mention_author=False)
        return

    embed = discord.Embed(title="🔮 Tổng hợp Chat", color=0x5865F2)

    if data.get("summary"):
        embed.description = data["summary"][:500]

    topics = data.get("main_topics", [])
    if topics:
        embed.add_field(
            name="📊 Chủ đề nổi bật",
            value="\n".join(f"• **{t['topic']}** ({t['count']} lần)" for t in topics[:5]),
            inline=False
        )

    stuck = data.get("stuck_points", [])
    if stuck:
        embed.add_field(
            name="🚧 Điểm học viên đang stuck",
            value="\n".join(f"⚠️ {p[:100]}" for p in stuck[:4]),
            inline=False
        )

    resources = data.get("suggested_resources", [])
    if resources:
        embed.add_field(
            name="📚 Tài liệu gợi ý",
            value=", ".join(f"**{r}**" for r in resources[:3]),
            inline=False
        )

    embed.set_footer(text="🤖 Tổng hợp tự động · !ka help")
    embed.set_author(name="VinAI Knowledge Assistant ⚡")
    await ctx.reply(embed=embed, mention_author=False)


@bot.command(name="kb", aliases=["tài liệu", "docs"])
async def cmd_kb(ctx):
    """Xem danh sách tài liệu trong Knowledge Base"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE}/api/knowledge-base", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
    except Exception as e:
        await ctx.reply(f"❌ Không lấy được KB: {str(e)[:100]}", mention_author=False)
        return

    docs = data.get("documents", [])
    if not docs:
        await ctx.reply("📂 Knowledge Base trống.", mention_author=False)
        return

    embed = discord.Embed(
        title=f"📂 Knowledge Base ({len(docs)} tài liệu)",
        color=0x5865F2
    )

    day1 = [d for d in docs if d.get("module") == "Day 1"]
    day2 = [d for d in docs if d.get("module") == "Day 2"]

    if day1:
        embed.add_field(
            name="📚 Day 1 — LLM Foundation",
            value="\n".join(f"`{d['id']}` {d['title'][:40]}" for d in day1),
            inline=False
        )
    if day2:
        embed.add_field(
            name="🔧 Day 2 — AI Product",
            value="\n".join(f"`{d['id']}` {d['title'][:40]}" for d in day2),
            inline=False
        )

    embed.set_footer(text="Dùng '!ka hỏi <câu hỏi>' để tra cứu kiến thức · !ka help")
    embed.set_author(name="VinAI Knowledge Assistant ⚡")
    await ctx.reply(embed=embed, mention_author=False)


# ══ RUN ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ Chưa có DISCORD_BOT_TOKEN trong .env")
        print("   Tạo bot tại: https://discord.com/developers/applications")
        print("   Thêm vào .env: DISCORD_BOT_TOKEN=your_token_here")
        sys.exit(1)

    print(f"🚀 Khởi động VinAI Knowledge Bot...")
    print(f"   API Backend: {API_BASE}")
    bot.run(DISCORD_TOKEN)
