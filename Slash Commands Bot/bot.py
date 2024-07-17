import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from torn import get_user_details, get_user_stats, get_user_profile, get_vitals, get_eta
from database import insert_user_discord_id, insert_user_torn_api_key, fetch_user_info

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
TOKEN = os.getenv('discord_token')
DISCORD_ID=os.getenv('DISCORD_ID')
print("DISCORD_ID = ", DISCORD_ID)


client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    print(f"{client.user.name} is ready")

# @client.command(name='hello')
# async def hello(ctx):
#     await ctx.send("Hey there boyo!")

@client.command(name='addid')
async def addid(ctx, discord_id: str):
    insert_user_discord_id(discord_id)
    await ctx.send(f"Registered Discord ID: {discord_id}")

@client.command(name='addapi')
async def addapi(ctx, torn_api_key: str):
    if isinstance(ctx.channel, discord.DMChannel): # Ensure the command is used in DMs
        discord_id = str(ctx.author.id)
        print("discord_id: {discord_id}")
        print("ctx.author:", ctx.author)
        insert_user_torn_api_key(torn_api_key)
        await ctx.send(f"Registered Torn API Key: {torn_api_key}")
    else:
        await ctx.send("Please use this command in a direct message to the bot.")

@client.command(name='user')
async def user(ctx):
    user_details = get_user_details()
    print("user details: {}".format(user_details))
    await ctx.send(user_details)
    
# Command to fetch user stats
@client.command(name="s")
async def s(ctx):
    user_stats = get_user_stats(discord_id=DISCORD_ID)
    await ctx.send(user_stats)
# get user profile with command !p
@client.command(name="p")
async def p(ctx):
    user_profile = get_user_profile()
    await ctx.send(user_profile)

@client.command(name="v")
async def p(ctx):
    user_vitals = get_vitals()
    await ctx.send(user_vitals)

@client.command(name="eta")
async def eta(ctx):
    user_eta = get_eta()
    await ctx.send(user_eta)
@client.hybrid_command(name='sync')
async def sync(ctx: commands.Context):
    await ctx.send("Syncing...")
    await client.tree.sync()

client.run(TOKEN)
