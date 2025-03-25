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
from dotenv import load_dotenv
import discord
from discord.ext import commands

# Retrieve sensitive information from file
load_dotenv()

TOKEN = os.getenv('TOKEN')

# Used for some commands
ADMIN_USERIDS = list(map(int, os.getenv('ADMIN_USERIDS').split(',')))
UI_CHANNEL_ID = os.getenv('UI_CHANNEL_ID')

intents = discord.Intents.default()
intents.messages = True  # Read messages
intents.message_content = True  # Read message content
bot = commands.Bot(command_prefix='/', intents=intents)

# Code text
CODE_TEXT = '''When posting configs or logs, please surround with code fences (\`\`\`) so that Discord formats them correctly. Example:
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
    await ctx.send("PLEASE don't ask us how to install Mainsail or Fluidd HH Edition. Just check the pinned messages. :smiley:", silent=True)

# /sync command to update / commands (reserved for admin-listed users)
@bot.command()
async def sync(ctx):
    print("sync command")
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
    # !code @user command
    if message.content.startswith('!code'):
        user = message.content.split()[1]
        await message.delete()
        await message.channel.send(f'''{user}{CODE_TEXT}''')
    # !say <text> command
    elif message.content.startswith('!say'):
        if message.author.id in ADMIN_USERIDS:
            msg = message.content[5:]
            await message.delete()
            await message.channel.send(msg)
    # !ui command
    elif message.content.startswith('!ui'):
        await message.delete()
        await send_ui_msg(message.channel)
    # Messages containing "how" AND "?" get a nice message.
    elif ('how' in message.content.lower() and '?' in message.content) and str(message.channel.id) == str(UI_CHANNEL_ID):
        await message.reply("Just check the pinned messages. :smiley:", silent=False)

    await bot.process_commands(message)

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord! {bot.guilds[0].name}')

# Run the bot
bot.run(TOKEN)