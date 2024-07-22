from itertools import cycle
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from flask import Flask
import threading
import requests
import time
from torn import get_user_details, get_user_stats, get_user_profile, get_vitals, get_eta
from database import insert_user_key
import bot
import torn


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
    user_details = get_user_details()
    print("user details: {}".format(user_details))
    await ctx.send(user_details)

@client.command(name="s")
async def s(ctx):
    user_stats = get_user_stats(discord_id=ctx.author.id)
    await ctx.send(user_stats)

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
