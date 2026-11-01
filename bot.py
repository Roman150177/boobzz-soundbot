
import os
import re
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
SOUND_DIR = "sounds"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot online: {bot.user}")


@bot.tree.command(name="sounds", description="List sound effects")
async def sounds(interaction: discord.Interaction):
    if not os.path.isdir(SOUND_DIR):
        await interaction.response.send_message("Sounds folder is empty.")
        return

    files = [
        f[:-4] for f in os.listdir(SOUND_DIR)
        if f.lower().endswith(".mp3")
    ]

    await interaction.response.send_message(
        ", ".join(files) if files else "No MP3 sounds found."
    )


@bot.tree.command(name="play", description="Play a sound effect")
@app_commands.describe(sound="Sound filename without .mp3")
async def play(interaction: discord.Interaction, sound: str):
    await interaction.response.defer()

    if not re.fullmatch(r"[a-zA-Z0-9_-]+", sound):
        await interaction.followup.send("Invalid sound name.")
        return

    if not interaction.user.voice:
        await interaction.followup.send("Join a voice channel first.")
        return

    path = os.path.join(SOUND_DIR, sound + ".mp3")

    if not os.path.isfile(path):
        await interaction.followup.send("Sound not found. Use /sounds.")
        return

    channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client

    if vc is None:
        vc = await channel.connect()
    elif vc.channel != channel:
        await vc.move_to(channel)

    if vc.is_playing():
        vc.stop()

    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(path),
        volume=0.8
    )

    vc.play(source)
    await interaction.followup.send(f"Playing {sound} 🔊")


@bot.tree.command(name="stop", description="Stop sound")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client

    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("Sound stopped.")
    else:
        await interaction.response.send_message("Nothing playing.")


@bot.tree.command(name="volume", description="Set volume")
@app_commands.describe(level="Volume from 0 to 100")
async def volume(
    interaction: discord.Interaction,
    level: app_commands.Range[int, 0, 100]
):
    vc = interaction.guild.voice_client

    if vc and vc.is_playing():
        if isinstance(vc.source, discord.PCMVolumeTransformer):
            vc.source.volume = level / 100
            await interaction.response.send_message(
                f"Volume: {level}%"
            )
            return

    await interaction.response.send_message("No sound playing.")


@bot.tree.command(name="leave", description="Disconnect bot")
async def leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client

    if vc:
        await vc.disconnect()
        await interaction.response.send_message("Disconnected.")
    else:
        await interaction.response.send_message("Not connected.")


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")

bot.run(TOKEN)
