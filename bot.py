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

Other features:
- When a message is sent in the #mainsail-fluidd channel containing both "how" AND "?", the UI message is sent, but frendlier.
"""

import os
import sys
import random
import time
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("log.txt"),  # optional for file-based logging
    ]
)

# Retrieve sensitive information from file
load_dotenv()

TOKEN = os.getenv('TOKEN')

MESSAGE_TRACKER = {}
SPAM_THRESHOLD = 5  # maximum messages in timeframe
SPAM_TIMEFRAME = 60  # seconds per window
MOD_CHANNEL_ID = int(os.getenv('MOD_CHANNEL_ID'))
MOD_PING = os.getenv('MOD_PING')

WELCOME_TEXT = """
## Welcome to the Happy Hare Discord server!

Here are a few quick things to know:

🔔 Subscribe to the <#1305216802594361354> channel so you don't miss out on important Happy Hare updates.

🖼️ Post pictures of completed multimaterial prints in the <#1325809620417249280> channel.

🌐 To view the MMU panel for Happy Hare in Mainsail/Fluidd, simply update your Mainsail/Fluidd version to the latest version! (This was released as of November 27, 2025)

🛠️ Explore the various MMU channels in the "MMU Systems" section.

📜 Have fun, and remember: this is a family-friendly server.

"""

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Used for some commands
ADMIN_USERIDS = list(map(int, os.getenv('ADMIN_USERIDS').split(',')))
LANDING_CHANNELID = os.getenv('LANDING_CHANNELID')

MMUS = '3DChameleon🦎,3MS,Box Turtle🐢,ERCF🥕,Night Owl🦉,Pico MMU,QuattroBox,Tradrack'.strip().split(',')

IMAGES = {
    'rollover': 'rollover.png'
}

def get_image_path(image_name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', IMAGES[image_name])

intents = discord.Intents.default()
intents.messages = True  # Read messages
intents.message_content = True  # Read message content
intents.guild_messages = True
bot = commands.Bot(command_prefix='/', intents=intents)

async def attempt_to_delete(message):
    try:
        await message.delete()
    except discord.errors.Forbidden:
        pass

# Code text
CODE_TEXT = '''

When posting configs or logs, please surround with code fences (```) so that Discord formats them correctly. Example:
```ini
[mcu]
serial: /dev/serial/by-id/usb-klipper-12345-if00
```
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
    logging.info("sync command")
    if ctx.author.id in ADMIN_USERIDS:
        await bot.tree.sync()
        await ctx.send('Command tree synced.')
    else:
        await ctx.send('You must be the owner to use this command!')

# /code @user command (reserved for admins)
@bot.tree.command(name='code')
async def tell_code(ctx, arg: discord.Member):
    await ctx.response.send_message(f'''{arg.mention}{CODE_TEXT}''')

# Event: Message received
@bot.event
async def on_message(message):
    # logging.info(message.author, message.content)
    now = time.time()
    attachments = str(len(message.attachments)) if message.attachments else ''
    content_key = f"{message.content.strip()}|{attachments}"
    MESSAGE_TRACKER.setdefault(content_key, [])
    MESSAGE_TRACKER[content_key] = [entry for entry in MESSAGE_TRACKER[content_key] if now - entry['time'] < SPAM_TIMEFRAME]
    MESSAGE_TRACKER[content_key].append({'channel': message.channel.id, 'time': now, 'message': message})
    unique_channels = {entry['channel'] for entry in MESSAGE_TRACKER[content_key]}
    if len(unique_channels) > 1:
        logging.warning(f'Spam #{len(unique_channels)}: {content_key}')
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
        logging.info(f'Welcoming {message.author.name}')
        await message.author.send(WELCOME_TEXT)
    elif message.content.startswith('!welcome') and message.author.id in ADMIN_USERIDS:
        logging.info(f'Welcoming {message.author.name}')
        user_id_str = message.content.strip().split()[1]
        try:
            user_id = int(user_id_str)
        except:
            user_id = int(user_id_str[1:])
        user = await bot.fetch_user(user_id)
        await attempt_to_delete(message)
        await user.send(WELCOME_TEXT)

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
            user = param
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
    # !rollover command
    elif message.content.startswith('!rollover'):
        channel = message.channel
        if len(message.content.split()) == 2:
            channel_id = int(message.content.split()[1][1:])
            channel = await bot.fetch_channel(channel_id)
        await attempt_to_delete(message)
        image_path = get_image_path('rollover')
        with open(image_path, 'rb') as f:
            picture = discord.File(f)
            await channel.send(file=picture)
    
    await bot.process_commands(message)

# Event: Bot is ready
@bot.event
async def on_ready():
    logging.info(f'{bot.user} has connected to Discord! {bot.guilds[0].name}')
    changeStatus.start()

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
    logging.info(f'Changing status to {status}')
    await bot.change_presence(activity=discord.Game(name=status))

# Run the bot
bot.run(TOKEN)