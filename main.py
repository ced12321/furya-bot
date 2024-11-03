import discord
from discord.ext import commands
import sys

# Initialisierung des Bots
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.members = True  # Erforderlich, um Mitglieder im Voice-Channel zu sehen

bot = commands.Bot(command_prefix="/", intents=intents)


def get_token():
    token = open("token.txt", "r")
    return token.read().strip()


# Bot-Event beim Start
@bot.event
async def on_ready():
    print(f"Eingeloggt als {bot.user}")


# Befehl, um die Nutzer im Voice-Channel anzuzeigen
@bot.command(name="voice_users")
async def voice_users(ctx, channel_id: int):
    # Versuchen, den Sprachkanal zu holen
    channel = bot.get_channel(channel_id)
    if channel is None or not isinstance(channel, discord.VoiceChannel):
        await ctx.send("Ungültiger Sprachkanal!")
        return

    # Liste der Mitglieder im Sprachkanal
    members = channel.members
    if not members:
        await ctx.send("Der Sprachkanal ist derzeit leer.")
    else:
        member_names = [member.name for member in members]
        user_list = "\n".join(member_names)
        await ctx.send(f"Aktuell verbundene Benutzer im Channel '{channel.name}':\n{user_list}")


# main
orig_stdout = sys.stdout
logfile = open("log.txt", "w")
sys.stdout = logfile


bot.run(get_token())

sys.stdout = orig_stdout
logfile.close()