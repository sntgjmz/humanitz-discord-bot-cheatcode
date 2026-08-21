import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
from rcon.source import rcon

# Set up intents
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Fetch secrets from Railway environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RCON_HOST = os.getenv("RCON_HOST")
RCON_PORT = int(os.getenv("RCON_PORT", 25575))
RCON_PASS = os.getenv("RCON_PASS")
STATUS_CHANNEL_ID = int(os.getenv("STATUS_CHANNEL_ID", 0))

async def run_rcon(cmd: str):
    """Executes an RCON command safely."""
    try:
        return await rcon(cmd, host=RCON_HOST, port=RCON_PORT, passwd=RCON_PASS)
    except Exception as e:
        return f"Error: {e}"

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    
    if STATUS_CHANNEL_ID and not update_status_embed.is_running():
        update_status_embed.start()

# Slash Command: Announcement / Broadcast
@bot.tree.command(name="announce", description="Broadcast a message in-game")
@app_commands.checks.has_permissions(administrator=True)
async def announce(interaction: discord.Interaction, message: str):
    await interaction.response.defer()
    res = await run_rcon(f"admin {message}")
    await interaction.followup.send(f"📢 Broadcast sent: `{res}`")

# Slash Command: Kick Player
@bot.tree.command(name="kick", description="Kick a player by Steam ID")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, steam_id: str):
    await interaction.response.defer()
    res = await run_rcon(f"kick {steam_id}")
    await interaction.followup.send(f"🦵 Kick result: `{res}`")

# Auto-Status Embed Loop
@tasks.loop(seconds=60)
async def update_status_embed():
    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if not channel:
        return

    players = await run_rcon("Players")
    embed = discord.Embed(title="🎮 HumanitZ Server Status", color=0x00ff00)
    embed.add_field(name="Server IP", value=f"`{RCON_HOST}`", inline=True)
    embed.add_field(name="Player List", value=f"```\n{players}\n```", inline=False)

    # Re-use or send status message
    async for msg in channel.history(limit=5):
        if msg.author == bot.user:
            await msg.edit(embed=embed)
            return
    await channel.send(embed=embed)

bot.run(DISCORD_TOKEN)