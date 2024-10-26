import discord
from discord.ext import commands
from discord.ui import Button, View
import random
import string
from PIL import Image, ImageDraw, ImageFont
import os
import math
import datetime
import pytz 

TOKEN = 'token'
SERVER_ID = id
ROLE_ID = id
LOG_CHANNEL_ID = id

poland_tz = pytz.timezone('Europe/Warsaw')
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
intents.members = True

bot = commands.Bot(command_prefix=",", intents=intents)
current_code = None

@bot.event
async def on_ready():
    print(f'Loggin: {bot.user}')

@bot.event
async def on_message(message):
    global current_code

    if message.author == bot.user:
        return
    
    if isinstance(message.channel, discord.DMChannel):
        guild = bot.get_guild(SERVER_ID)
        member = guild.get_member(message.author.id)  

        if member:
            role = guild.get_role(ROLE_ID) 
            if current_code and message.content == current_code:
                if role in member.roles: 
                    await message.channel.send("You are already verified")
                else:
                    await member.add_roles(role) 
                    await message.channel.send("The code is correct the role has been assigned")
                    await log_verification(member, current_code, True)
                current_code = None 
            elif current_code:
                await message.channel.send("The code is incorrect. Type ,auth to start again")
                await log_verification(member, current_code, False) 
                current_code = None 
        else:
            await message.channel.send("User not found.")

    if isinstance(message.channel, discord.DMChannel) and message.content == ',auth':
        button = Button(label="Get auth code", style=discord.ButtonStyle.primary)

        async def button_callback(interaction):
            global current_code

            characters = string.ascii_letters + string.digits
            current_code = ''.join(random.choice(characters) for _ in range(12))

            img_width = 800
            img_height = 400
            img = Image.new('RGB', (img_width, img_height), color=(73, 109, 137)) 
            d = ImageDraw.Draw(img)

            try:
                font_size = 60
                font = ImageFont.truetype("arial.ttf", font_size) 
            except IOError:
                font = ImageFont.load_default() 

            text_bbox = d.textbbox((0, 0), current_code, font=font)  
            text_width = text_bbox[2] - text_bbox[0]  
            text_height = text_bbox[3] - text_bbox[1]  
            text_x = (img_width - text_width) // 2  
            text_y = (img_height - text_height) // 2 
            d.text((text_x, text_y), current_code, fill=(255, 255, 255), font=font)  

            line_y = text_y + text_height // 2 
            amplitude = 5 
            frequency = 0.1

            for x in range(0, img_width):
                y = line_y + amplitude * math.sin(frequency * x)
                if x == 0:
                    last_y = y
                d.line((x - 1, last_y, x, y), fill=(255, 255, 255), width=3)  
                last_y = y  
            img_path = 'code_image.png'
            img.save(img_path)
            embed = discord.Embed(
                title="Auth Code",
                description=(
                    "Enter the correct code. You have only 1 attempt. "
                    "If the code is incorrect, you will have to enter ,auth to start again"
                ),
                color=0x007bff
            )
            embed.set_image(url="attachment://code_image.png")

            await interaction.response.send_message(embed=embed, file=discord.File(img_path), ephemeral=True)
            os.remove(img_path)

        button.callback = button_callback
        view = View()
        view.add_item(button)

        await message.channel.send(view=view)
    else:
        await bot.process_commands(message)

async def log_verification(member, code, successful):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    embed = discord.Embed(
        title="",
        color=0x00ff00 if successful else 0xff0000
    )
    
    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    embed.set_author(name=str(member), icon_url=avatar_url)
    embed.add_field(name="User ID", value=member.id, inline=False)
    embed.add_field(name="Date of account creation", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Code", value=code, inline=False)
    embed.add_field(name="Date of verification", value=datetime.datetime.now(poland_tz).strftime("%Y-%m-%d %H:%M:%S"), inline=False) 
    embed.add_field(name="Verification status:", value="Udana" if successful else "Nieudana", inline=False)

    await log_channel.send(embed=embed)

bot.run(TOKEN)
