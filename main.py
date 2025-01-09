import discord
from discord.ext.commands import has_role
from discord.ui import Button, View
import logging

from DkpManager import DkpManager

DKP_MANAGER_ROLE_ID = 1307003061369045032
TL_MEMBER_ROLE_ID = 638795102361354260

PVP_CHANNEL_ID = 1289970145002913802
PVE_CHANNEL_ID = 1290095676679655476
ALLI_EVENT_CHANNEL_ID = 1297222312478904320

BOT_CHANNEL_ID = 1280588930382565499

FURYA_GUILD_ID = 395072012181045260
ALLI_GUILD_ID = 1296531345203265647

GUILD_NAME_POSTFIX = "POLARIS"

logger = logging.getLogger("FuryaBot")
logging.basicConfig(format='%(asctime)s %(message)s', filename='bot.log', level=logging.WARNING)

dkp_rewards = (
    ("PVE Gildenbosse", 5, PVE_CHANNEL_ID, True), ("Boonstone Kampf", 10, PVP_CHANNEL_ID, True),
    ("Allianz PVP", 5, PVP_CHANNEL_ID, True),
    ("Steuertransport", 10, PVP_CHANNEL_ID, False), ("Castle Siege", 30, PVP_CHANNEL_ID, False))


def get_token():
    token = open("token", "r")
    return token.read().strip()


# Initialisierung des Bots
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.message_content = True
intents.members = True  # Erforderlich, um Mitglieder im Voice-Channel zu sehen
bot = discord.Bot(intents=intents)
manager = DkpManager()


# Bot-Event beim Start
@bot.event
async def on_ready():
    logger.log(logging.INFO, f"Logged in as {bot.user}")


# @bot.check(lambda ctx: ctx.channel.id == BOT_CHANNEL_ID)
@bot.command(name="mydkp")
@has_role(TL_MEMBER_ROLE_ID)
async def dkp(ctx):
    await _get_dkp(ctx, ctx.author)


@bot.command(name="weekly")
@has_role(DKP_MANAGER_ROLE_ID)
async def weekly(ctx, args):
    arg_list = args.split()
    logger.warning(f"{ctx.author.display_name}:{ctx.author.id} hat /weekly benutzt mit: {args}")
    if len(arg_list) % 2 != 0 or len(arg_list) < 2:
        await ctx.respond(
            "Value Error: Die Liste muss gleich viele IDs wie Reputation enthalten, damit jeder ID ein Reputation wert zugewiesen werden kann.")
    else:
        reputation_dict = {arg_list[i]: (round((int(arg_list[i + 1])) / 1000)) for i in range(0, len(arg_list), 2)}
        manager.compute_end_of_week(reputation_dict)
        manager.export_dkp()
        await ctx.respond("Die wöchtentlichen Dkp wurden erfolgreich übernommen.")


# @bot.check(lambda ctx: ctx.channel.id == BOT_CHANNEL_ID)
@bot.command(name="dkp")
@has_role(TL_MEMBER_ROLE_ID)
async def dkp(ctx, user: discord.Member):
    await _get_dkp(ctx, user)


@bot.command(name="pay")
@has_role(DKP_MANAGER_ROLE_ID)
async def pay(ctx, user: discord.Member, dkp: int):
    await _decrease_dkp(user.id, dkp)
    await ctx.respond(f"{user.display_name} hat {dkp} DKP bezahlt")
    logger.warning(f"{user.display_name} hat {dkp} DKP bezahlt: by {ctx.author}")


@bot.command(name="adddkp")
@has_role(DKP_MANAGER_ROLE_ID)
async def adddkp(ctx, user: discord.Member, dkp: int, weekly: bool):
    await _add_dkp([user.id], dkp, weekly=weekly)
    _weekly = " weekly" if weekly else ""
    await ctx.respond(f"{user.display_name} hat {dkp} {_weekly} DKP erhalten")
    logger.warning(f"{user.display_name} hat {dkp} {_weekly} DKP erhalten: by {ctx.author}")


@bot.command(name="managedkp")
@has_role(DKP_MANAGER_ROLE_ID)
async def manage_dkp(ctx):
    if _verify_manager_role(ctx.author):
        await _send_management_msg(ctx)
    else:
        await ctx.respond(f"Du hast keine Berechtigung diesen Befehl zu benutzen")


@bot.command(name="list")
@has_role(DKP_MANAGER_ROLE_ID)
async def list_member(ctx):
    members1 = await get_members_from_two_channels()
    members2 = await _get_member_of_channel(ctx, PVP_CHANNEL_ID)
    msg = f"Member beide {list(dict.fromkeys(members1))} \n Member furya {members2}"
    await ctx.respond(msg)


async def _get_dkp(ctx, user):
    manager.import_data_if_empty()
    dkp_entry = manager.find_by_id(user.id)
    if dkp_entry is None:
        await ctx.respond(f"{user.display_name}: hat noch keine DKP!")
    else:
        await ctx.respond(
            f"{user.display_name}: DKP insgesamt: {dkp_entry["dkp"]}, DKP weekly: {dkp_entry["weekly_dkp"]}")


async def _add_dkp(user_ids, amount, weekly: bool):
    manager.import_data_if_empty()
    for user_id in user_ids:
        manager.add_weekly(user_id, amount) if weekly else manager.add_dkp(user_id, amount)
    manager.export_dkp()


async def _decrease_dkp(user_id, dkp):
    manager.import_data_if_empty()
    manager.add_dkp(user_id, abs(dkp) * -1)
    manager.export_dkp()


def _verify_manager_role(author):
    return any(role.id == DKP_MANAGER_ROLE_ID for role in author.roles)


async def _get_member_of_channel(ctx, channel_id):
    voice_channel = ctx.guild.get_channel(int(channel_id))

    # Überprüfen, ob der Kanal existiert und ob es ein Sprachkanal ist
    if not voice_channel or not isinstance(voice_channel, discord.VoiceChannel):
        await ctx.respond("Dieser Kanal ist kein gültiger Sprachkanal.")

    # Alle Benutzer im Sprachkanal abrufen
    members_in_channel = [member.id for member in voice_channel.members]

    if not members_in_channel:
        await ctx.respond("Der Sprachkanal ist derzeit leer.")
    return members_in_channel


async def get_members_from_two_channels():
    furya_server = bot.get_guild(FURYA_GUILD_ID)
    alli_server = bot.get_guild(ALLI_GUILD_ID)

    if not furya_server or not alli_server:
        logger.error(f"Server konnte nicht gefunden werden. Furya-Discord: {furya_server}, Alli-Discord: {alli_server}")

    members_furya = await _get_members_of_channel(furya_server, PVP_CHANNEL_ID, lambda name: True)
    members_alli = await _get_members_of_channel(alli_server, ALLI_EVENT_CHANNEL_ID,
                                                 name_filter=lambda display_name: display_name.upper().endswith(
                                                     GUILD_NAME_POSTFIX))

    return members_alli + members_furya


async def _get_members_of_channel(guild, channel_id, name_filter):
    voice_channel = guild.get_channel(channel_id)

    # Überprüfen, ob der Kanal existiert und ob es ein Sprachkanal ist
    if not voice_channel or not isinstance(voice_channel, discord.VoiceChannel):
        logger.error(f"Channel: {channel_id} in Server: {guild} nicht gefunden oder Channel ist kein Voice Channel!")

    # Alle Benutzer im Sprachkanal abrufen
    # if name_filter:
    members_in_channel = [member.id for member in voice_channel.members if name_filter(member.display_name)]
    # else:
    #    members_in_channel = [member.id for member in voice_channel.members]

    return members_in_channel


async def _send_management_msg(ctx):
    # Erstelle die Embed-Nachricht
    embed = discord.Embed(
        title="DKP-Manager",
        description="""Hierüber können die DKP von events verteilt werden. Wenn du den entsprechenden Knopf drückst werden den aktuell verbundenen Membern der PVE/PVP Channel die DKP gutgeschrieben""",
        color=discord.Color.blue()  # Farbe der Embed-Nachricht
    )

    for i in range(5):
        embed.add_field(name=dkp_rewards[i][0], value=f"{dkp_rewards[i][1]} DKP", inline=False)

    # Erstelle die Buttons
    button1 = Button(label=dkp_rewards[0][0], style=discord.ButtonStyle.primary, custom_id=str(0))  # Blau
    button2 = Button(label=dkp_rewards[1][0], style=discord.ButtonStyle.danger, custom_id=str(1))  # Blau
    button3 = Button(label=dkp_rewards[2][0], style=discord.ButtonStyle.danger, custom_id=str(2))  # Rot
    button4 = Button(label=dkp_rewards[3][0], style=discord.ButtonStyle.danger, custom_id=str(3))  # Rot
    button5 = Button(label=dkp_rewards[4][0], style=discord.ButtonStyle.success, custom_id=str(4))  # Grün

    async def button_callback(interaction: discord.Interaction):
        reward = dkp_rewards[int(interaction.custom_id)]

        if int(interaction.custom_id) != 0:
            participants = await get_members_from_two_channels()
        else:
            participants = await _get_member_of_channel(ctx, reward[2])
        await _add_dkp(participants, reward[1], reward[3])

        await interaction.response.send_message(
            f"Du hast das Event '{dkp_rewards[int(interaction.custom_id)][0]}' gewählt!",
            ephemeral=True)
        logger.warning(
            f"{interaction.user.display_name}:{interaction.user.id} hat das Event {dkp_rewards[int(interaction.custom_id)][0]} aktiviert")

    for button in [button1, button2, button3, button4, button5]:
        button.callback = button_callback

    # Erstelle eine View und füge die Buttons hinzu
    view = View()
    for button in [button1, button2, button3, button4, button5]:
        view.add_item(button)

    # Sende die Embed-Nachricht mit der View
    await ctx.respond(embed=embed, view=view)


bot.run(get_token())
