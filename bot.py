# SPDX-License-Identifier: GPL-3.0-only
"""
Happy Hare Bot v2
by 3DCoded

Copyright (C) 2025 3DCoded (Christopher Mattar)

The bot supports the following commands:
- !ui
    Sends a reminder to check the pinned messages for Mainsail/Fluidd installation.
    This command outputs the following:
        PLEASE don't ask us how to install Mainsail or Fluidd HH Edition. Just check the pinned messages. 😃
- !code @user
    Tells the user how to properly format code blocks.
    This command outputs the following:
        @user When posting configs or logs, please surround with code fences (```) so that Discord formats them correctly. Example:
        ```ini
        [mcu]
        serial: /dev/serial/by-id/usb-klipper-12345-if00
        ```
        [mcu]
        serial: /dev/serial/by-id/usb-klipper-12345-if00
- /code @user
    Same function as !code @user, but this is restricted to admins.
- !say <text>
    Reserved for admin-listed users. Sends a message containing <text>.

Other features:
- When a message is sent in the #mainsail-fluidd channel containing both "how" AND "?", the UI message is sent, but frendlier.
"""

import os
import sys
import random
import json
import time
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from discord.utils import get as dget

# Retrieve sensitive information from file
load_dotenv()

TOKEN = os.getenv('TOKEN')

MESSAGE_TRACKER = {}
SPAM_THRESHOLD = 5  # number of channels
SPAM_TIMEFRAME = 60  # seconds
MOD_CHANNEL_ID = int(os.getenv('MOD_CHANNEL_ID'))  # new env var for mod channel
MOD_PING = os.getenv('MOD_PING')  # e.g. '@moderators'

WELCOME_TEXT = """
## Welcome to the Happy Hare Discord server!

Here are a few quick things to know:

🔔 Subscribe to the <#1305216802594361354> channel so you don't miss out on important Happy Hare updates.

🖼️ Post pictures of completed multimaterial prints in the <#1325809620417249280> channel.

🌐 To view the MMU panel for Happy Hare in Mainsail/Fluidd, simply update your Mainsail/Fluidd version to the latest version! (This was released as of November 27, 2025)

🛠️ Explore the various MMU channels in the "MMU Systems" section.

📜 Have fun, and remember: this is a family-friendly server.

❤️ React to this message with the emojis for your favorite MMU's to receive update notifications from their designers.
"""

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def log(text):
    with open('log.txt', 'a+') as file:
        file.write(text + '\n')

# Used for some commands
ADMIN_USERIDS = list(map(int, os.getenv('ADMIN_USERIDS').split(',')))
UI_CHANNEL_ID = os.getenv('UI_CHANNEL_ID')
LANDING_CHANNELID = os.getenv('LANDING_CHANNELID')
GUILD_ID = int(os.getenv('GUILD_ID'))

if not os.path.exists('messages.txt'):
    with open('messages.txt', 'w+') as file:
        file.write('')

MMUS = '3DChameleon🦎,3MS,Box Turtle🐢,ERCF🥕,Night Owl🦉,Pico MMU,QuattroBox,Tradrack'.strip().split(',')

intents = discord.Intents.default()
intents.messages = True  # Read messages
intents.reactions = True
intents.members = True
intents.guild_reactions = True
intents.message_content = True  # Read message content
intents.guild_messages = True
bot = commands.Bot(command_prefix='/', intents=intents)

def intenv(name):
    return int(os.getenv(name))

async def attempt_to_delete(message):
    try:
        await message.delete()
    except discord.errors.Forbidden:
        pass

ROLES = {}

# Code text
CODE_TEXT = '''

When posting configs or logs, please surround with code fences (\`\`\`) so that Discord formats them correctly. Example:
\`\`\`ini
[mcu]
serial: /dev/serial/by-id/usb-klipper-12345-if00
\`\`\`
```ini
[mcu]
serial: /dev/serial/by-id/usb-klipper-12345-if00
```'''

# Invoked with !ui or the timeout
async def send_ui_msg(ctx):
    await ctx.send("You can now update Mainsail/Fluidd to the latest version to view the MMU panel! <:mainsail:1346960310300315855><:fluidd:1346960443310080010>:tada: ", silent=True)

# /sync command to update / commands (reserved for admin-listed users)
@bot.command()
async def sync(ctx):
    log("sync command")
    if ctx.author.id in ADMIN_USERIDS:
        await bot.tree.sync()
        await ctx.send('Command tree synced.')
    else:
        await ctx.send('You must be the owner to use this command!')

# /code @user command (reserved for admins)
@bot.tree.command(name='code')
async def tell_code(ctx, arg: discord.Member):
    await ctx.response.send_message(f'''{arg.mention}{CODE_TEXT}''')

@bot.event
async def on_raw_reaction_add(payload):
    # Skip bots
    if payload.user_id == bot.user.id:
        return

    # Fetch the user (works even if they're not cached)
    user = await bot.fetch_user(payload.user_id)

    with open('messages.txt') as file:
        if str(payload.message_id) not in file.read():
            return
    emoji_label = payload.emoji.name
    for role_name, info in ROLES.items():
        if info['emoji'] == emoji_label or getattr(info['emoji'], 'name', None) == emoji_label:
            guild = bot.get_guild(GUILD_ID)
            member = await guild.fetch_member(user.id)
            role = guild.get_role(info['roleid'])
            log(role.name)
            await member.add_roles(role)
            log(f'Added {user.display_name} to {role_name}')
            await user.send(f'You have successfully subscribed to {role.name}.')
            break

@bot.event
async def on_raw_reaction_remove(payload):
    # Skip bots
    if payload.user_id == bot.user.id:
        return

    # Fetch the user (works even if they're not cached)
    with open('messages.txt') as file:
        if str(payload.message_id) not in file.read():
            return
    user = await bot.fetch_user(payload.user_id)
    emoji_label = payload.emoji.name
    for role_name, info in ROLES.items():
        if info['emoji'] == emoji_label or getattr(info['emoji'], 'name', None) == emoji_label:
            guild = bot.get_guild(GUILD_ID)
            member = await guild.fetch_member(user.id)
            role = guild.get_role(info['roleid'])
            log(role.name)
            await member.remove_roles(role)
            log(f'Removed {member.display_name} from {role_name}')
            await user.send(f'You have successfully unsubscribed from {role.name}.')
            break

# Event: Message received
@bot.event
async def on_message(message):
    # log(message.author, message.content)
    now = time.time()
    attachments = ','.join([a.filename for a in message.attachments]) if message.attachments else ''
    content_key = f"{message.content.strip()}|{attachments}"
    MESSAGE_TRACKER.setdefault(content_key, [])
    MESSAGE_TRACKER[content_key] = [entry for entry in MESSAGE_TRACKER[content_key] if now - entry['time'] < SPAM_TIMEFRAME]
    MESSAGE_TRACKER[content_key].append({'channel': message.channel.id, 'time': now, 'author': message.author.id, 'message': message})
    unique_channels = {entry['channel'] for entry in MESSAGE_TRACKER[content_key]}
    if len(unique_channels) >= SPAM_THRESHOLD:
        mod_channel = await bot.fetch_channel(MOD_CHANNEL_ID)
        await mod_channel.send(f"🚨 Possible spam detected from {message.author.mention} in multiple channels:\n{MOD_PING}\n\nMessage:\n{message.content}")
        for a in message.attachments:
            await mod_channel.send(a.url)
        # Delete all tracked messages
        for entry in MESSAGE_TRACKER[content_key]:
            try:
                await entry['message'].delete()
            except discord.errors.Forbidden:
                pass
        MESSAGE_TRACKER.pop(content_key, None)
    if message.content.strip() == '' and len(message.stickers) == 0 and str(message.channel.id) == str(LANDING_CHANNELID):
        log(f'Welcoming {message.author.name}')
        msg = await message.author.send(WELCOME_TEXT)
        for role_name in ROLES:
            emoji = ROLES[role_name]['emoji']
            await msg.add_reaction(emoji)
        with open('messages.txt', 'a') as file:
            file.write(f'\n{msg.id}')
    elif message.content.startswith('!welcome') and message.author.id in ADMIN_USERIDS:
        log(f'Welcoming {message.author.name}')
        user_id_str = message.content.strip().split()[1]
        try:
            user_id = int(user_id_str)
        except:
            user_id = int(user_id_str[1:])
        user = await bot.fetch_user(user_id)
        await attempt_to_delete(message)
        msg = await user.send(WELCOME_TEXT)
        for role_name in ROLES:
            emoji = ROLES[role_name]['emoji']
            await msg.add_reaction(emoji)
        with open('messages.txt', 'a') as file:
            file.write(f'\n{msg.id}')

    # !code @user command
    # !code #channelid command
    # !code #channelid @user command
    elif message.content.startswith('!code'):
        param = str(' '.join(message.content.split()[1:]))
        await attempt_to_delete(message) # Delete message
        channel = message.channel
        user = ''
        if param.startswith('#') and not ' ' in param:
            channel_id = int(param[1:])
            channel = await bot.fetch_channel(channel_id)
        elif param.startswith('@') and not ' ' in param:
            user = '<@'+param[1:]+'>'
        elif param.startswith('<@') and not ' ' in param:
            user = param[2:-1]
        elif len(param.split()) == 2:
            channel_id = int(param.split()[0][1:])
            channel = await bot.fetch_channel(channel_id)
            user = '<@'+param.split()[1][1:]+'>'
        nline = '\n'
        await channel.send(f'''{user+nline if user != '' else ''}{CODE_TEXT}''')
    # !say <text> command
    # !say #channelid <text> command
    elif message.content.startswith('!say'):
        # Make sure it's an approved user
        if message.author.id in ADMIN_USERIDS:
            msg = str(message.content[5:])
            channel = message.channel
            # If using !say <#channel> <text> format
            if msg.startswith('#'):
                channel_id = int(msg.split()[0][1:]) # Get channel id
                msg = ' '.join(msg.split()[1:]) # Remove channel id from message
                channel = await bot.fetch_channel(channel_id) # Fetch channel from id
            elif msg.isnumeric():
                channel_id = int(msg)
                msg = ' '.join(msg.split()[1:])
                channel = await bot.fetch_channel(channel_id)
            await attempt_to_delete(message) # Delete user message
            await channel.send(msg) # Send the bot message
    # !ui command
    # !ui #channelid command
    elif message.content.startswith('!ui'):
        channel = message.channel
        if len(message.content.split()) == 2:
            channel_id = int(message.content.split()[1][1:])
            channel = await bot.fetch_channel(channel_id)
        await attempt_to_delete(message)
        await send_ui_msg(channel)
    # !roles command
    elif message.content.startswith('!roles') and message.author.id in ADMIN_USERIDS:
        await attempt_to_delete(message)
        # if len(message.content.split()) > 1:
        #     channel_id = int(message.content.split()[1][2:-1])
        #     channel = await bot.fetch_channel(channel_id)
        # else:
        channel = message.channel
        msg = await channel.send('React to this message to subscribe to notifications for your MMU!')
        with open('messages.txt', 'a') as file:
            file.write(f'\n{msg.id}')
        for role_name in ROLES:
            emoji = ROLES[role_name]['emoji']
            await msg.add_reaction(emoji)
    elif message.content.startswith('!rolecount') and message.author.id in ADMIN_USERIDS:
        await message.reply('Counting role users')
        for role_name in ROLES:
            role_id = ROLES[role_name]['roleid']
            count = await count_members_with_role(bot, role_id=role_id)
            await message.channel.send(f'{role_name}: {count}')

    await bot.process_commands(message)

# Event: Bot is ready
@bot.event
async def on_ready():
    global ROLES
    log(f'{bot.user} has connected to Discord! {bot.guilds[0].name}')
    ROLES = {
        '3DChameleon': {
            'emoji': bot.get_emoji(intenv('3DCHAMELEON_EMOJI')),
            'roleid': intenv('3DCHAMELEON_ROLE')
        },
        '3MS': {
            'emoji': bot.get_emoji(intenv('3MS_EMOJI')),
            'roleid': intenv('3MS_ROLE')
        },
        'Angry Beaver': {
            'emoji': '🦫',
            'roleid': intenv('ANGRYBEAVER_ROLE')
        },
        'Box Turtle': {
            'emoji': '🐢',
            'roleid': intenv('BOXTURTLE_ROLE')
        },
        'ERCF': {
            'emoji': '🥕',
            'roleid': intenv('ERCF_ROLE')
        },
        'Night Owl': {
            'emoji': '🦉',
            'roleid': intenv('NIGHTOWL_ROLE')
        },
        'Pico MMU': {
            'emoji': bot.get_emoji(intenv('PICO_EMOJI')),
            'roleid': intenv('PICO_ROLE')
        },
        'QuattroBox': {
            'emoji': bot.get_emoji(intenv('QUATTROBOX_EMOJI')),
            'roleid': intenv('QUATTROBOX_ROLE')
        },
        'Tradrack': {
            'emoji': bot.get_emoji(intenv('TRADRACK_EMOJI')),
            'roleid': intenv('TRADRACK_ROLE')
        },
    }
    changeStatus.start()


async def count_members_with_role(bot: discord.Client, role_id: int) -> int:
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print("Guild not found.")
        return 0

    role = guild.get_role(role_id)
    if role is None:
        print("Role not found.")
        return 0

    count = 0
    async for member in guild.fetch_members(limit=None):
        if role in member.roles:
            count += 1

    return count

@tasks.loop(seconds=10)
async def changeStatus():
    mmu = random.choice(MMUS)
    verb = random.choice([
        'Printing with',
        'Tinkering with',
        'Calibrating',
        'Building',
        'Fixing',
        'Screaming at',
    ])
    status = f'{verb} the {mmu}'
    log(status)
    await bot.change_presence(activity=discord.Game(name=status))

# Run the bot
bot.run(TOKEN)