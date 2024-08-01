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
from torn import get_user_details, get_user_stats, get_user_profile, get_vitals, get_eta, get_user_stat_history, get_user_work_stats
from database import insert_user_key, get_firestore_db
import bot
import pytz
from timezone import TimezoneView

# Define a list of UTC offsets from -12 to +14
UTC_OFFSETS = [f"TCT{n:+}" for n in range(-12, 15)]

# pagination constants
ITEMS_PER_PAGE = 25


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
    user_details = get_user_details(discord_id=ctx.author.id)
    print("user details: {}".format(user_details))
    await ctx.send(user_details)

@client.command(name="s")
async def s(ctx):

    user_stats = get_user_stats(discord_id=ctx.author.id, discord_username=ctx.author.name)
    await ctx.send(user_stats)

@client.command(name="sh")
async def sh(ctx, days_ago: int):
    discord_id = ctx.author.id
    stat_history = get_user_stat_history(discord_id, days_ago)
    await ctx.send(stat_history)

@client.command(name="p")
async def p(ctx):
    user_profile = get_user_profile(discord_id=ctx.author.id)
    await ctx.send(user_profile)

@client.command(name="v")
async def v(ctx):
    user_vitals = get_vitals(discord_id=ctx.author.id)
    await ctx.send(user_vitals)

@client.command(name="eta")
async def eta(ctx):
    user_eta = get_eta()
    await ctx.send(user_eta)

@client.command(name="ws") # work stats command 
async def ws(ctx):
    user_ws = get_user_work_stats(discord_id=ctx.author.id)
    await ctx.send(user_ws)

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
