import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from torn import get_user_details, get_user_stats, get_user_profile, get_vitals, get_eta
from database import insert_user_key

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
TOKEN = os.getenv('discord_token')
#DISCORD_ID=os.getenv('DISCORD_ID')
# print("DISCORD_ID = ", DISCORD_ID)

client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    print(f"{client.user.name} is ready")

@client.command(name='addkeys')
async def addkeys(ctx, torn_id: str, torn_api_key: str):
    if isinstance(ctx.channel, discord.DMChannel):  # Ensure the command is used in DMs
        print("discord id = ", ctx.author.id)
        insert_user_key(ctx.author.id, torn_id, torn_api_key)
        await ctx.send(f"Registered torn ID: {torn_id} and Torn API Key: {torn_api_key}")
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
    user_stats = get_user_stats(discord_id=ctx.author.id)
    await ctx.send(user_stats)

# Get user profile with command !p
@client.command(name="p")
async def p(ctx):
    user_profile = get_user_profile()
    await ctx.send(user_profile)

@client.command(name="v")
async def v(ctx):
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
