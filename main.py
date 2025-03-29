import discord
from discord.ext import commands
import yt_dlp
import asyncio
import random
from youtubesearchpython import VideosSearch

import os
from dotenv import load_dotenv

load_dotenv()  # Load biến môi trường từ file .env
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ Không tìm thấy BOT_TOKEN! Kiểm tra lại file .env.")

OWNER_ID = 741648403515310171
VOICE_CHANNEL_ID = 1355347950309478530  # ID kênh thoại bot sẽ vào
TEXT_CHANNEL_ID = 1245993933511593988  # ID kênh bot nhận lệnh

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

queue = []
current_song = None
previous_song = None
volume_level = 1.0  # Mặc định âm lượng là 100%

@bot.event
async def on_ready():
    print(f"✅ {bot.user} đã online!")
    channel = bot.get_channel(TEXT_CHANNEL_ID)
    if channel:
        await channel.send(
            "> 🟢🎵 **BOT MUSIC [BETA] - MAKE BY DNN HOẠT ĐỘNG!** 🎶\n"
            "> 🚀 **Trải nghiệm âm nhạc cực chill, chất lượng cao ngay!**\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "> 🟣 **🌟 TÍNH NĂNG** | 🎼 **Kho nhạc đa dạng** | ✍ **`!hd` Để xem hướng dẫn**\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "> 🎧 **🔥 VÀO KÊNH 🎵 NGHE NHẠC NGAY! 🔥**\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "> 🟡 **💡 HỖ TRỢ?** | 📩 **Inbox Nguyên** | 💖 **Cảm ơn mọi người!**\n"
            "> 🎶 **\"Âm nhạc kết nối cảm xúc - Bot Music DNN đồng hành cùng bạn!\"** 🎶"
        )


@bot.event
async def on_message(message):
    if message.channel.id == 1245993933511593988:
        # Kiểm tra nếu lệnh là các lệnh không được phép trong kênh này
        restricted_commands = ["!play", "!skip", "!vol", "!phatlai", "!danhsach", "!leave", "!stop", "!tt", "!nhacchill", "!dung"]
        if any(command in message.content for command in restricted_commands):
            await message.delete()  # Xóa tin nhắn chứa lệnh không hợp lệ
            # Gửi thông báo vào kênh
            await message.channel.send(f"❌ **Lệnh không thể sử dụng trong kênh này! Vui lòng sử dụng các lệnh tại kênh 'dùng-lệnh-bot'.**")
            return

    await bot.process_commands(message)  # Tiếp tục xử lý các lệnh hợp lệ khác

@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == VOICE_CHANNEL_ID:  # Kiểm tra xem người tham gia có vào đúng kênh thoại không
        # Chỉnh sửa kênh nhận tin nhắn tại đây
        channel = bot.get_channel(1355442717664088176)  # Kênh 1355442717664088176
        if channel:
            # Gửi tin nhắn thông báo cho người vừa tham gia
            await channel.send(f"{member.mention} Bạn Muốn Nghe Nhạc Nào? Hoặc gõ `!hd` để biết cách dùng bot!")

@bot.command()
async def join(ctx):
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if channel:
        await channel.connect()
        await ctx.send("✅ **Bot đã tham gia kênh thoại!**")
    else:
        await ctx.send("❌ **Không tìm thấy kênh thoại!**")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("📤 **Bot đã rời kênh thoại!**")
    else:
        await ctx.send("❌ **Bot không ở trong kênh thoại!**")

@bot.command()
async def play(ctx, *, search: str):
    global current_song, previous_song
    if ctx.voice_client is None:
        await join(ctx)

    await ctx.send(f"🔍 **Đang tìm kiếm bài hát:** `{search}`...")

    # Tìm kiếm các video YouTube với từ khóa search
    results = VideosSearch(search, limit=5).result()["result"]  # Trả về 5 kết quả
    if not results:
        await ctx.send("❌ **Không tìm thấy bài hát!**")
        return

    search_results = ""
    for i, video in enumerate(results):
        search_results += f"{i+1}. {video['title']} ({video['duration']})\n"

    await ctx.send(f"🔎 **Chọn bài hát bằng cách nhập số (1-5):**\n{search_results}")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

    try:
        response = await bot.wait_for("message", check=check, timeout=7.0)
        choice = int(response.content)
        if 1 <= choice <= 5:
            video = results[choice - 1]
            video_url = video['link']
            video_title = video['title']
            queue.append((video_title, video_url))

            await ctx.send(f"📥 **Đã thêm vào hàng chờ:** `{video_title}`")

            if not ctx.voice_client.is_playing():
                await play_next(ctx)
        else:
            await ctx.send("❌ **Vui lòng chọn số từ 1 đến 5!**")

    except asyncio.TimeoutError:
        # Nếu hết thời gian chọn, bot sẽ chọn bài ngẫu nhiên
        random_choice = random.choice(results)  # Chọn ngẫu nhiên một bài từ kết quả
        video_url = random_choice['link']
        video_title = random_choice['title']
        queue.append((video_title, video_url))

        await ctx.send(f"⏳ **Hết thời gian chọn bài! Đang phát bài nhạc ngẫu nhiên:** `{video_title}`")

        if not ctx.voice_client.is_playing():
            await play_next(ctx)


async def play_next(ctx):
    global current_song, previous_song
    if queue:
        previous_song = current_song
        current_song = queue.pop(0)
        video_title, video_url = current_song

        await ctx.send(f"🎶 **Đang phát:** `{video_title}`\n🔗 {video_url}")

        ctx.voice_client.stop()
        FFMPEG_OPTIONS = {'options': '-vn', 'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}
        YDL_OPTIONS = {'format': 'bestaudio'}

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(video_url, download=False)
            url2 = info['url']

        source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        ctx.voice_client.source.volume = volume_level  # Áp dụng âm lượng hiện tại ngay khi phát bài mới
    else:
        # Nếu không có bài hát nào trong hàng chờ, tự động tìm "nhạc tiktok" và phát
        await play(ctx, search="nhạc tiktok")
        await ctx.send("🎶 **Không còn nhạc trong hàng chờ! Đang tìm nhạc TikTok để phát!**")

@bot.command()
async def skip(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ **Bài hát đã được bỏ qua!**")
    else:
        await ctx.send("❌ **Không có bài hát nào đang phát!**")

@bot.command()
async def phatlai(ctx):
    if previous_song:
        queue.insert(0, previous_song)
        await play_next(ctx)
    else:
        await ctx.send("❌ **Không có bài hát trước đó!**")

@bot.command()
async def danhsach(ctx):
    if queue:
        queue_text = '\n'.join([f"{i+1}. {song[0]}" for i, song in enumerate(queue)])
        await ctx.send(f"📜 **Danh sách chờ:**\n{queue_text}")
    else:
        await ctx.send("❌ **Hàng chờ trống!**")

@bot.command()
async def vol(ctx, level: int):
    global volume_level
    if 0 <= level <= 100:
        volume_level = level / 100
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = volume_level  # Áp dụng ngay lập tức
        await ctx.send(f"🔊 **Âm lượng đã được đặt thành {level}%**")
    else:
        await ctx.send("❌ **Vui lòng nhập giá trị từ 0 đến 100!**")

@bot.command()
async def dung(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸ **Nhạc đã tạm dừng!**")
    else:
        await ctx.send("❌ **Không có nhạc đang phát!**")

@bot.command()
async def tt(ctx):
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶ **Nhạc tiếp tục phát!**")
    else:
        await ctx.send("❌ **Không có nhạc bị tạm dừng!**")

@bot.command()
async def stop(ctx):
    if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
        ctx.voice_client.stop()
        await ctx.send("⏹ **Đã dừng nhạc!**")
    else:
        await ctx.send("❌ **Không có nhạc đang phát!**")

@bot.command()
@commands.is_owner()
async def clear(ctx):
    await ctx.channel.purge()
    await ctx.send("🧹 **Đã xóa tin nhắn trong kênh!**")

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(f"**Phải chủ đéo đâu đòi dùng clear😂, {ctx.author.mention}!**")

@bot.command()
async def nhacchill(ctx):
    # Tìm kiếm nhạc chill (lofi) từ YouTube hoặc một nguồn nào đó
    search = "lofi chill music"
    await play(ctx, search=search)  # Dùng lệnh play để phát nhạc chill
    await ctx.send("🎶 **Đang phát nhạc lofi chill!**")

@bot.command()
async def hd(ctx):
    embed = discord.Embed(title="📖 **Hướng Dẫn Sử Dụng Bot**", color=discord.Color.blue())
    embed.add_field(name="🎧 **Tham gia kênh thoại**", value="`!join` - Bot vào kênh thoại", inline=False)
    embed.add_field(name="🎶 **Phát nhạc**", value="`!play <tên bài>` - Bot tìm và phát nhạc", inline=False)
    embed.add_field(name="⏸ **Tạm dừng**", value="`!dung` - Tạm dừng nhạc", inline=False)
    embed.add_field(name="▶ **Tiếp tục**", value="`!tt` - Tiếp tục phát nhạc", inline=False)
    embed.add_field(name="⏹ **Dừng nhạc**", value="`!stop` - Dừng nhạc ngay lập tức", inline=False)
    embed.add_field(name="🧹 **Xóa tin nhắn**", value="`!clear` - Xóa sạch tin nhắn trong kênh (Chỉ chủ bot)", inline=False)
    embed.add_field(name="📤 **Rời khỏi kênh**", value="`!leave` - Bot rời khỏi kênh thoại", inline=False)
    embed.add_field(name="📜 **Danh sách chờ**", value="`!danhsach` - Xem danh sách bài hát trong hàng chờ", inline=False)
    embed.add_field(name="⏮ **Phát lại bài trước**", value="`!phatlai` - Phát lại bài hát trước đó", inline=False)
    embed.add_field(name="🔊 **Điều chỉnh âm lượng**", value="`!vol <mức>` - Điều chỉnh âm lượng (0-100%)", inline=False)
    embed.add_field(name="▶▶ **Bài Tiếp Theo**", value="`!skip` - Chuyển đến bài tiếp theo luôn ", inline=False)
    embed.add_field(name="😴 **Mở nhạc lofi**", value="`!nhacchill` - Tự tìm và mở nhạc lofi", inline=False)
    embed.set_footer(text="Make By DNN")
    await ctx.send(embed=embed)

bot.run(BOT_TOKEN)
