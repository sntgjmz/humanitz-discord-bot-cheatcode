import discord
from discord.ext import tasks, commands
from rcon.source import rcon
import asyncio

# Setup bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

STATUS_CHANNEL_ID = 123456789012345678  # Replace or use os.getenv("STATUS_CHANNEL_ID")
RCON_HOST = "209.102.250.165"
RCON_PORT = 9002
RCON_PASS = "MRsjizNwYue3SQpx"

status_message = None

@tasks.loop(seconds=30)
async def update_status_embed():
    global status_message
    channel = bot.get_channel(int(STATUS_CHANNEL_ID))
    if not channel:
        return

    try:
        # Query player count via RCON
        response = await rcon(
            'Players', 
            host=RCON_HOST, 
            port=int(RCON_PORT), 
            passwd=RCON_PASS, 
            timeout=5
        )
        
        # Calculate active players
        lines = [line for line in response.split('\n') if line.strip()]
        player_count = len(lines) if "No players" not in response else 0
        
        # Create Online Embed Layout
        embed = discord.Embed(color=0x2ecc71)  # Green side bar

        embed.add_field(name="Status", value="🟢 `Online`", inline=True)
        embed.add_field(name="Players", value=f"`{player_count}/20`", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)  # Spacer for alignment

        embed.add_field(
            name="CONNECT COMMAND", 
            value=f"```connect {RCON_HOST}:9000```", 
            inline=False
        )

        embed.add_field(name="Restart Schedule", value="`Every 12 Hours`", inline=True)
        embed.add_field(name="Max Players", value="`20 Slots`", inline=True)

    except Exception:
        # Create Offline Embed Layout
        embed = discord.Embed(color=0xe74c3c)  # Red side bar

        embed.add_field(name="Status", value="🔴 `Offline`", inline=True)
        embed.add_field(name="Players", value="`0/20`", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.add_field(
            name="Connect Command", 
            value=f"```connect {RCON_HOST}:9000```", 
            inline=False
        )

        embed.add_field(name="Notice", value="`Server is Offline`", inline=True)

    # Edit existing message or send a new one
    if status_message:
        try:
            await status_message.edit(embed=embed)
        except discord.NotFound:
            status_message = await channel.send(embed=embed)
    else:
        # Search recent messages to avoid duplicate posts on bot restart
        async for msg in channel.history(limit=10):
            if msg.author == bot.user and msg.embeds:
                status_message = msg
                await status_message.edit(embed=embed)
                break
        if not status_message:
            status_message = await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    update_status_embed.start()