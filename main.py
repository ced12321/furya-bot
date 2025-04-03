import discord
from discord.ext.commands import has_role
from discord.ui import Button, View
import logging

from DkpManager import DkpManager
from ConfManager import ConfigManager

logger = logging.getLogger("FuryaBot")
logging.basicConfig(format='%(asctime)s %(message)s', filename='bot.log', level=logging.WARNING)


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
dkp_manager = DkpManager()
conf_manager = ConfigManager()


# Bot-Event beim Start
@bot.event
async def on_ready():
    logger.log(logging.INFO, f"Logged in as {bot.user}")


# @bot.check(lambda ctx: ctx.channel.id == BOT_CHANNEL_ID)
@bot.command(name="mydkp")
@has_role(conf_manager.config_cache.get("roles").get("member", 638795102361354260))
async def dkp(ctx):
    dkp_manager.import_data_if_empty()
    dkp_entry = dkp_manager.find_by_id(ctx.author.id)
    if dkp_entry is None:
        await ctx.respond(f"{ctx.author.display_name}: hat noch keine DKP!", ephemeral=True)
    else:
        await ctx.respond(
            f"{ctx.author.display_name}: DKP insgesamt: {dkp_entry["dkp"]}, DKP weekly: {dkp_entry["weekly_dkp"]}",
            ephemeral=True)


@bot.command(name="weekly")
@has_role(conf_manager.config_cache.get("roles").get("manager", 1307003061369045032))
async def weekly(ctx, args):
    arg_list = args.split()
    logger.warning(f"{ctx.author.display_name}:{ctx.author.id} hat /weekly benutzt mit: {args}")
    if len(arg_list) % 2 != 0 or len(arg_list) < 2:
        await ctx.respond(
            "Value Error: Die Liste muss gleich viele IDs wie Reputation enthalten, damit jeder ID ein Reputation wert zugewiesen werden kann.")
    else:
        reputation_dict = {arg_list[i]: (round((int(arg_list[i + 1])) / 1000)) for i in range(0, len(arg_list), 2)}
        dkp_manager.compute_end_of_week(reputation_dict)
        dkp_manager.export_dkp()
        await ctx.respond("Die wöchtentlichen Dkp wurden erfolgreich übernommen.")


# @bot.check(lambda ctx: ctx.channel.id == BOT_CHANNEL_ID)
@bot.command(name="dkp")
@has_role(conf_manager.config_cache.get("roles").get("manager", 1307003061369045032))
async def dkp(ctx, user: discord.Member):
    dkp_manager.import_data_if_empty()
    dkp_entry = dkp_manager.find_by_id(user.id)
    if dkp_entry is None:
        await ctx.respond(f"{user.display_name}: hat noch keine DKP!")
    else:
        await ctx.respond(
            f"{user.display_name}: DKP insgesamt: {dkp_entry["dkp"]}, DKP weekly: {dkp_entry["weekly_dkp"]}")


@bot.command(name="pay")
@has_role(conf_manager.config_cache.get("roles").get("manager", 1307003061369045032))
async def pay(ctx, user: discord.Member, dkp: int):
    await _decrease_dkp(user.id, dkp)
    await ctx.respond(f"{user.display_name} hat {dkp} DKP bezahlt")
    logger.warning(f"{user.display_name} hat {dkp} DKP bezahlt: by {ctx.author}")


@bot.command(name="adddkp")
@has_role(conf_manager.config_cache.get("roles").get("manager", 1307003061369045032))
async def adddkp(ctx, user: discord.Member, dkp: int, weekly: bool):
    await _add_dkp([user.id], dkp, weekly=weekly)
    _weekly = " weekly" if weekly else ""
    await ctx.respond(f"{user.display_name} hat {dkp} {_weekly} DKP erhalten")
    logger.warning(f"{user.display_name} hat {dkp} {_weekly} DKP erhalten: by {ctx.author}")


@bot.command(name="managedkp")
@has_role(conf_manager.config_cache.get("roles").get("manager", 1307003061369045032))
async def manage_dkp(ctx):
    await _send_management_msg(ctx)


@bot.command(name="event")
@has_role(conf_manager.config_cache.get("roles").get("manager", 1307003061369045032))
async def event_dkp(ctx, server: int, channel, dkp: int, weekly: bool):
    _server = bot.get_guild(server)
    if not _server or not isinstance(_server, discord.Guild):
        logger.error(f"Server id:{server} konnte nicht gefunden werden.")
    _channel = _server.get_channel(channel)
    if not _channel or not isinstance(_channel, discord.VoiceChannel):
        logger.error(
            f"Channel: {channel} in Server: {_server.id} nicht gefunden oder Channel ist kein Voice Channel!")

    member = _channel.members
    await _add_dkp(member, dkp, weekly=weekly)
    channel_mention = f"<#{channel}>"
    await ctx.respond(f"Mitglieder des Kanals {channel_mention} haben {dkp} {"weekly" if weekly else ""} DKP erhalten")
    await log_members(ctx, member)


@bot.command(name="conf")
@has_role(conf_manager.get("roles").get("manager", 1307003061369045032))
async def get_dkp_conf(ctx):
    embed = discord.Embed(title="DKP-Konfiguration",
                          description="Dies ist die aktuelle Konfiguration des DKP-Bots",
                          colour=0x329a39)

    embed.set_author(name="Onke",
                     icon_url="https://media.discordapp.net/attachments/939140952533123075/1015554166938161162/onke88-01_1.jpg?ex=67e66c05&is=67e51a85&hm=2dab96628d61601964e04b67853c2a7b45a159ebb9b3d3b5044811b88c004780")

    for server in conf_manager.get("server"):
        pve_channel_formatted = [f"<#{str(channel)}>" for channel in server.get("channel").get("pve")]
        pvp_channel_formatted = [f"<#{str(channel)}>" for channel in server.get("channel").get("pvp")]
        embed.add_field(name=f"Server: {server.get('name')}",
                        value=f"Channel PVE:\n{pve_channel_formatted}\nChannel PVP\n{pvp_channel_formatted}",
                        inline=False)
    embed.set_footer(text="Alle Angaben wie immer ohne Gewähr",
                     icon_url="https://slate.dan.onl/slate.png")

    await ctx.respond(embed=embed)


@bot.command(name="addserver")
@has_role(conf_manager.get("roles").get("manager", 1307003061369045032))
async def add_server(ctx, server_id, name: str):
    conf_manager.add_server(server_id, name)
    await ctx.respond(
        f"Server {name} ID: {server_id} wurde registriert. \nBitte ladet den Bot auf den Server ein:\nhttps://discord.com/oauth2/authorize?client_id=1343690892451778671")


@bot.command(name="removeserver")
@has_role(conf_manager.get("roles").get("manager", 1307003061369045032))
async def remove_server(ctx, server_id):
    conf_manager.delete_server(server_id)
    await ctx.respond(f"Server mit id {server_id} wird entfernt!")


@bot.command(name="addchannel")
@has_role(conf_manager.get("roles").get("manager", 1307003061369045032))
async def add_channel(ctx, server, channel_id, pvp: bool):
    conf_manager.add_channel(server, channel_id, pvp)
    await ctx.respond(f"Channel <#{channel_id}> wurde registriert.")


@bot.command(name="removechannel")
@has_role(conf_manager.get("roles").get("manager", 1307003061369045032))
async def remove_channel(ctx, server, channel_id):
    conf_manager.delete_channel(server, channel_id)
    await ctx.respond(f"Channel <#{channel_id}> wurde entfernt!")


async def _add_dkp(user_ids, amount, weekly: bool):
    dkp_manager.import_data_if_empty()
    for user_id in user_ids:
        dkp_manager.add_weekly(user_id, amount) if weekly else dkp_manager.add_dkp(user_id, amount)
    dkp_manager.export_dkp()


async def _decrease_dkp(user_id, dkp):
    dkp_manager.import_data_if_empty()
    dkp_manager.add_dkp(user_id, abs(dkp) * -1)
    dkp_manager.export_dkp()


async def get_member_of_channel(event_type):
    participants = []
    for server_obj in conf_manager.config_cache.get("server"):
        for channel_id in server_obj.get("channel").get(event_type.lower()):
            server = bot.get_guild(server_obj.get("id"))
            if not server or not isinstance(server, discord.Guild):
                logger.error(f"Server {server_obj.get("id")} konnte nicht gefunden werden.")
            channel = server.get_channel(channel_id)
            if not channel or not isinstance(channel, discord.VoiceChannel):
                logger.error(
                    f"Channel: {channel_id} in Server: {server_obj.get("id")} nicht gefunden oder Channel ist kein Voice Channel!")
            participants = list(set(participants).union([member.id for member in channel.members]))
            #participants.extend([member.id for member in channel.members])
    return participants


async def _send_management_msg(ctx):
    # Erstelle die Embed-Nachricht
    embed = discord.Embed(
        title="DKP-Manager",
        description="""Hierüber können die DKP von events verteilt werden. Wenn du den entsprechenden Knopf drückst werden den aktuell verbundenen Membern der PVE/PVP Channel die DKP gutgeschrieben""",
        color=discord.Color.blue()  # Farbe der Embed-Nachricht
    )

    events = conf_manager.get("events")
    for i in range(5):
        embed.add_field(name=events[i].get("name"), value=f"{events[i].get("reward")} DKP", inline=False)

    # Erstelle die Buttons
    button1 = Button(label=events[0].get("name"), style=discord.ButtonStyle.primary,
                     custom_id=str(events[0].get("id")))  # Blau
    button2 = Button(label=events[1].get("name"), style=discord.ButtonStyle.danger,
                     custom_id=str(events[1].get("id")))  # Blau
    button3 = Button(label=events[2].get("name"), style=discord.ButtonStyle.danger,
                     custom_id=str(events[2].get("id")))  # Rot
    button4 = Button(label=events[3].get("name"), style=discord.ButtonStyle.danger,
                     custom_id=str(events[3].get("id")))  # Rot
    button5 = Button(label=events[4].get("name"), style=discord.ButtonStyle.success,
                     custom_id=str(events[4].get("id")))  # Grün

    async def button_callback(interaction: discord.Interaction):
        _events = conf_manager.get("events")
        event = [event for event in _events if event.get("id") == int(interaction.custom_id)][0]
        logger.warning(f"interactionId: {interaction.custom_id} event: {event}")

        if int(interaction.custom_id) != 0:
            """PVP-EVENT"""
            participants = await get_member_of_channel("PVP")
        else:
            """PVE-EVENT"""
            participants = await get_member_of_channel("PVE")
        await _add_dkp(participants, event.get("reward"), event.get("weekly"))

        await interaction.response.send_message(
            f"{interaction.user.mention} hat das Event '{event.get("name", "UNKNOWN EVENT")}' gewählt!",
            ephemeral=False)
        logger.warning(
            f"{interaction.user.display_name}:{interaction.user.id} hat das Event {event.get("name", "UNKNOWN EVENT")} aktiviert")
        await log_members(interaction, participants)

    for button in [button1, button2, button3, button4, button5]:
        button.callback = button_callback

    # Erstelle eine View und füge die Buttons hinzu
    view = View()
    for button in [button1, button2, button3, button4, button5]:
        view.add_item(button)

    # Sende die Embed-Nachricht mit der View
    await ctx.respond(embed=embed, view=view)


async def log_members(ctx, members):
    msg = f"Folgende {len(members)} Member haben DKP erhalten: {[bot.get_user(member).mention for member in members]} | User IDs:{members}"
    await ctx.followup.send(msg)
    logger.warning(msg)


bot.run(get_token())
