from itertools import cycle
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from discord.ui import Select, View
from flask import Flask
import threading
import requests
import time
from torn import get_user_details, get_user_stats, get_user_profile, get_vitals, get_eta, get_user_stat_history, get_user_work_stats, get_effective_battlestats, get_mentioned_user_stats, get_user_stats_as_percentage
from database import insert_user_key, get_firestore_db
import bot
import pytz
from timezone import TimezoneView

# Define a list of UTC offsets from -12 to +14
UTC_OFFSETS = [f"TCT{n:+}" for n in range(-12, 15)]

# pagination constants
ITEMS_PER_PAGE = 25

# discord UI color constants 
BLUE =  discord.Color.blue()


status = cycle(['with Python','JetHub'])
# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def index():
    return "Discord bot is running!"

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
TOKEN = os.getenv('discord_token')

client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready(): 

    print(f"{client.user.name} is ready")

@tasks.loop(seconds=30)
async def change_status():
    await client.change_presence(activity=discord.Game(next(status)))

# async def create_embed(description, color):
#     # Create the embed
#     embed = discord.Embed(
#         description=description,
#         color=color 
#     )
#     return embed
# Example command using an embed
@client.command(name="test")
async def stats(ctx):
    # This is a placeholder for your stats logic
    discord_id = ctx.author.id
    discord_username = f"{ctx.author.name}#{ctx.author.discriminator}"
    torn_id = 1234567  # Replace with actual Torn ID retrieval logic
    user_stats = "Example stats content here..."

    # Creating the embed
    embed = discord.Embed(
        title=f"Changes to Stats for {discord_username}",
        description=user_stats,
        color=discord.Color.blue()  # Change color as needed
    )

    # Adding a link as an embed field or in the description
    profile_link = f"https://www.torn.com/profiles.php?XID={torn_id}"
    embed.add_field(name="Torn Profile", value=f"[Click here to view profile]({profile_link})", inline=False)

    # Sending the embed
    await ctx.send(embed=embed)

@client.command(name="info")
async def info(ctx):
    info_message = (
        "**Bot Command Information**\n\n"

        "**!addkeys**\n"
        "This command is used to register your Torn ID and API key with the bot. "
        "Use this command in a direct message to the bot for security reasons. "
        "The syntax is `!addkeys <Torn_ID> <Torn_API_Key>`. "
        "The bot will store your Torn ID and API key securely, allowing it to access your "
        "Torn account information and provide personalized data.\n\n"

        "**Note:**\n"
        "- Make sure to send `!addkeys` in a private message (DM) to avoid exposing your API key publicly.\n"
        "- If you encounter any issues, please contact the bot administrator for assistance."

        "**!timezone**\n"
        "Use this command to set your timezone offset from Torn City Time (TCT). "
        "When you call this command, the bot will prompt you to select your offset from TCT. "
        "This helps in adjusting the time-related data based on your local timezone.\n\n"
        

    )

    # Send the information as a message
    await ctx.send(info_message)

@client.command(name="timezone")
async def timezone(ctx):
    view = TimezoneView(current_page=0)
    view.message = await ctx.send("Please select your TCT offset:", view=view)

@client.command(name='addkeys')
async def addkeys(ctx, torn_id: str, torn_api_key: str):
    if isinstance(ctx.channel, discord.DMChannel):  # Ensure the command is used in DMs
        print("discord id = ", ctx.author.id)
        string_ctx_author_id = str(ctx.author.id)
        string_torn_id = str(torn_id)
        string_torn_api_key = str(torn_api_key)
        insert_user_key(string_ctx_author_id, string_torn_id, string_torn_api_key)
        await ctx.send(f"Registered torn ID: {torn_id} and Torn API Key: {torn_api_key}")
    else:
        await ctx.send("Please use this command in a direct message to the bot.")

@client.command(name='user')
async def user(ctx):
    user_details =  get_user_details(discord_id=ctx.author.id)
    print("user details: {}".format(user_details))
    # Create the embed
    embed = discord.Embed(
        #title=f"Stat History For {ctx.author.id}",
        description=user_details,
        color=BLUE 
    )
    # Send the embed
    await ctx.send(embed=embed)
    #await ctx.send(user_details)

@client.command(name="s")
async def s(ctx, user: discord.User = None):
    if user is None:
        user_stats = get_user_stats(discord_id=ctx.author.id, discord_username=ctx.author.name)
        print("User without @ ")
    else:
        print("user being atted ")
        discord_id = user.id
        discord_username = user.name
        user_stats = get_mentioned_user_stats(discord_id, discord_username)

    # Create the embed
    embed = discord.Embed(
        description=user_stats,
        color=discord.Color.blue(),  # You can choose other colors
        #thumbnail=ctx.author.avatar_url,
        #title=ctx.author,
    )

    # # Set the user's profile picture as the thumbnail on the right hand side 
    # #embed.set_thumbnail(url=user.avatar_url)
    # embed.setImage(ctx.author.avatarURL())
    # Send the embed
    await ctx.send(embed=embed)

@client.command(name="sp")
async def sp(ctx):
    discord_id = ctx.author.id
    user_stats_as_percentage = get_user_stats_as_percentage(discord_id, ctx.author.name )
    # Create the embed
    embed = discord.Embed(
        #title=f"Stat History For {ctx.author.id}",
        description=user_stats_as_percentage,
        color=BLUE 
    )
    # Send the embed
    await ctx.send(embed=embed)

@client.command(name="sh")
async def sh(ctx, days_ago: int):
    discord_id = ctx.author.id
    stat_history = get_user_stat_history(discord_id, ctx.author.name ,days_ago)
    # Create the embed
    embed = discord.Embed(
        #title=f"Stat History For {ctx.author.id}",
        description=stat_history,
        color=BLUE 
    )
    # Send the embed
    await ctx.send(embed=embed)

@client.command(name="fs")
async def fs(ctx):
    user_effective_battle_stats = get_effective_battlestats(ctx.author.id, ctx.author.name)
    # Create the embed
    embed = discord.Embed(
        #title=f"Stat History For {ctx.author.id}",
        description=user_effective_battle_stats,
        color=BLUE 
    )

    # Send the embed
    await ctx.send(embed=embed)
@client.command(name="p")
async def p(ctx):
    user_profile = get_user_profile(ctx.author.id, ctx.author.name)
    # Create the embed
    embed = discord.Embed(
        #title=f"Stat History For {ctx.author.id}",
        description=user_profile,
        color=BLUE 
    )
    # Send the embed
    await ctx.send(embed=embed)

@client.command(name="v")
async def v(ctx):
    user_vitals =  get_vitals(discord_id=ctx.author.id)
    # Create the embed
    embed = discord.Embed(
        #title=f"Stat History For {ctx.author.id}",
        description=user_vitals,
        color=BLUE 
    )
    # Send the embed
    await ctx.send(embed=embed)

@client.command(name="eta")
async def eta(ctx):
    user_eta =  get_eta()
    # Create the embed
    embed = discord.Embed(
        #title=f"Stat History For {ctx.author.id}",
        description=user_eta,
        color=BLUE 
    )
    # Send the embed
    await ctx.send(embed=embed)

@client.command(name="ws") # work stats command 
async def ws(ctx):
    user_ws =  get_user_work_stats(discord_id=ctx.author.id)
    # Create the embed
    embed = discord.Embed(
        #title=f"Stat History For {ctx.author.id}",
        description=user_ws,
        color=BLUE 
    )
    # Send the embed
    await ctx.send(embed=embed)
@client.hybrid_command(name='sync')
async def sync(ctx: commands.Context):
    await ctx.send("Syncing...")
    await client.tree.sync()

# Function to run Flask server
def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Function to keep the server alive
def keep_alive():
    while True:
        try:
            requests.get("http://localhost:8080")
        except requests.exceptions.RequestException as e:
            print(f"Keep-alive request failed: {e}")
        time.sleep(5 * 60)  # Ping every 5 minutes

# Run Flask server in a separate thread
if __name__ == "__main__":
    # Start the Flask server in a background thread
    print("Trying to run the bot")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Start the keep-alive function in a background thread
    keep_alive_thread = threading.Thread(target=keep_alive)
    keep_alive_thread.daemon = True  # Daemon thread will exit when the main thread exits
    keep_alive_thread.start()

    try:
        # Start the Discord bot
        client.run(TOKEN)
    except Exception as e:
        print(f"Failed to start Discord client: {e}")
