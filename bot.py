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
import random
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks

# Retrieve sensitive information from file
load_dotenv()

TOKEN = os.getenv('TOKEN')

WELCOME_TEXT = """
## Welcome to the Happy Hare Discord server!

Here are a few quick things to know:

🔔 Subscribe to the <#1305216802594361354> channel so you don't miss out on important Happy Hare updates.

🖼️ Post pictures of completed prints in the <#1325809620417249280> channel.

🌐 To install the new Mainsail/Fluidd interface for Happy Hare, read the **PINNED** messages in the <#1306047636117127318> channel. If you don't, I have been programmed to automatically remind you to **READ THE PINNED MESSAGES**. Sorry. This has happened a lot before...

🛠️ Explore the various MMU channels in the "MMU Systems" section.

📜 Have fun, and remember: this is a family-friendly server.
"""

# Used for some commands
ADMIN_USERIDS = list(map(int, os.getenv('ADMIN_USERIDS').split(',')))
UI_CHANNEL_ID = os.getenv('UI_CHANNEL_ID')
LANDING_CHANNELID = os.getenv('LANDING_CHANNELID')

MMUS = '3DChameleon🦎,3MS,Box Turtle🐢,ERCF🥕,Night Owl🦉,Pico MMU,QuattroBox,Tradrack'.strip().split(',')

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
    # print(message.author, message.content)
    if message.content.strip() == '' and len(message.stickers) == 0 and str(message.channel.id) == str(LANDING_CHANNELID):
        print(f'Welcoming {message.author.name}')
        await message.author.send(WELCOME_TEXT)
    elif '!welcome' in message.content and message.author.id in ADMIN_USERIDS:
        print(f'Welcoming {message.author.name}')
        user_id = int(message.content.strip().split()[1][2:-1])
        user = await bot.fetch_user(user_id)
        await message.delete()
        await user.send(WELCOME_TEXT)
    # !code @user command
    elif message.content.startswith('!code'):
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
    # await bot.change_presence(activity=discord.Game(name='Printing with an MMU...'))
    changeStatus.start()


@tasks.loop(seconds=3600)
async def changeStatus():
    mmu = random.choice(MMUS)
    status = f'with the {mmu}'
    print(status)
    await bot.change_presence(activity=discord.Game(name=status))

# Run the bot
bot.run(TOKEN)