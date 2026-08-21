import discord
from discord.ext import tasks, commands
from rcon.source import rcon
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

STATUS_CHANNEL_ID = os.getenv("STATUS_CHANNEL_ID")
RCON_HOST = os.getenv("RCON_HOST")
RCON_PORT = os.getenv("RCON_PORT", "9002")
RCON_PASS = os.getenv("RCON_PASS")

status_message = None

@tasks.loop(seconds=30)
async def update_status_embed():
    global status_message
    if not STATUS_CHANNEL_ID:
        return
        
    channel = bot.get_channel(int(STATUS_CHANNEL_ID))
    if not channel:
        return

    try:
        response = await rcon(
            'Players', 
            host=RCON_HOST, 
            port=int(RCON_PORT), 
            passwd=RCON_PASS, 
            timeout=5
        )
        
        lines = [line for line in response.split('\n') if line.strip()]
        player_count = len(lines) if "No players" not in response else 0
        
        embed = discord.Embed(title="UBELLION SERVER STATUS", color=0x00FF00)
        embed.add_field(name="🌐 Server Status", value="```ansi\n\x1b[1;32mONLINE\x1b[0m\n```", inline=True)
        embed.add_field(name="📌 IP & Port", value=f"```{RCON_HOST}:9000```", inline=True)
        embed.add_field(name="📊 Players", value=f"```{player_count} / 20```", inline=False)
        embed.set_footer(text="HumanitZ Server Watchdog • Auto-updates every 30s")

    except Exception:
        embed = discord.Embed(title="UBELLION SERVER STATUS", color=0xFF0000)
        embed.add_field(name="🌐 Server Status", value="```ansi\n\x1b[1;31mOFFLINE\x1b[0m\n```", inline=True)
        embed.add_field(name="📌 IP & Port", value=f"```{RCON_HOST}:9000```", inline=True)
        embed.add_field(name="📊 Details", value="```Unable to connect to RCON server.```", inline=False)
        embed.set_footer(text="HumanitZ Server Watchdog • Auto-updates every 30s")

    if status_message:
        try:
            await status_message.edit(embed=embed)
        except discord.NotFound:
            status_message = await channel.send(embed=embed)
    else:
        status_message = await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    update_status_embed.start()

bot.run(os.getenv("DISCORD_TOKEN"))