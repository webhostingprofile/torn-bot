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
from torn import get_user_details, get_user_stats, get_user_profile, get_vitals, get_eta, get_user_stat_history, get_user_work_stats, get_effective_battlestats, get_mentioned_user_stats, get_user_stats_as_percentage, join_lotto_logic, get_lotto_status_logic
from database import insert_user_key, get_firestore_db
import bot
import pytz
from timezone import TimezoneView
from lotto_view import LottoView
from lotto_manager import get_lotto_data, set_lotto_data, reset_lotto_data, handle_join_lotto
import asyncio 

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
    embed.set_thumbnail(url=ctx.author.avatar.url)
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
    embed.set_thumbnail(url=ctx.author.avatar.url)
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
    embed.set_thumbnail(url=ctx.author.avatar.url)
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
    embed.set_thumbnail(url=ctx.author.avatar.url)
    # Send the embed
    await ctx.send(embed=embed)

@client.command(name="fs")
async def fs(ctx, user: discord.User = None):
    if user is None: 
        user_effective_battle_stats = get_effective_battlestats(ctx.author.id, ctx.author.name)
    else: 
        discord_id = user.id
        discord_username = user.name
        user_effective_battle_stats = get_effective_battlestats(discord_id, discord_username) 
    #user_effective_battle_stats = get_effective_battlestats(ctx.author.id, ctx.author.name)
    # Create the embed
    embed = discord.Embed(
        #title=f"Stat History For {ctx.author.id}",
        description=user_effective_battle_stats,
        color=BLUE 
    )

    embed.set_thumbnail(url=ctx.author.avatar.url)

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
    embed.set_thumbnail(url=ctx.author.avatar.url)
    # Send the embed
    await ctx.send(embed=embed)

@client.command(name="v")
async def v(ctx):
    user_vitals =  get_vitals(discord_id=ctx.author.id, discord_username=ctx.author.name)#, discord_username=ctx.author.name)
    # Create the embed
    embed = discord.Embed(
        #title=f"Stat History For {ctx.author.id}",
        description=user_vitals,
        color=BLUE 
    )
    embed.set_thumbnail(url=ctx.author.avatar.url)
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
    embed.set_thumbnail(url=ctx.author.avatar.url)
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
    embed.set_thumbnail(url=ctx.author.avatar.url)
    # Send the embed
    await ctx.send(embed=embed)


    # Global dictionary to store lotto data
lotto_data = {
    "participants": {},  # Format: {discord_id: ticket_count}
    "jackpot": 0,
    "start_time": time.time(),
    "end_time": time.time() + 86400  # Example: 24 hours from start
}

TICKET_PRICE = 1000  # Example ticket price

@client.command(name="lotto")
async def lotto(ctx, action: str, tickets: int = 1):
    discord_id = ctx.author.id
    username = ctx.author.name

    if action == "buy":
        if tickets < 1:
            await ctx.send("You need to buy at least 1 ticket!")
            return

        # Deduct currency (integration with user currency system needed)
        ticket_cost = tickets * TICKET_PRICE

        # Check if user exists in participants and update
        if discord_id in lotto_data["participants"]:
            lotto_data["participants"][discord_id] += tickets
        else:
            lotto_data["participants"][discord_id] = tickets

        lotto_data["jackpot"] += ticket_cost

        await ctx.send(f"{username} bought {tickets} tickets for {ticket_cost}! Current jackpot: {lotto_data['jackpot']}")


@client.command(name="lottostatus")
async def lottostatus(ctx):
    participants = lotto_data["participants"]
    jackpot = lotto_data["jackpot"]

    if not participants:
        await ctx.send("No participants yet!")
        return

    participant_list = "\n".join([f"<@{user}>: {count} tickets" for user, count in participants.items()])
    await ctx.send(f"**Current Lotto Status:**\nJackpot: {jackpot}\nParticipants:\n{participant_list}")


import random

@client.command(name="lottodraw")
@commands.has_permissions(administrator=True)  # Restrict to admins
async def lottodraw(ctx):
    participants = lotto_data["participants"]
    jackpot = lotto_data["jackpot"]

    if not participants:
        await ctx.send("No participants to draw from!")
        return

    # Create a weighted list of tickets
    weighted_pool = [user for user, tickets in participants.items() for _ in range(tickets)]
    winner = random.choice(weighted_pool)

    await ctx.send(f"🎉 Congratulations <@{winner}>! You won the jackpot of {jackpot} 🎉")

    # Reset lotto
    lotto_data["participants"] = {}
    lotto_data["jackpot"] = 0


# @tasks.loop(hours=24)  # Draw every 24 hours
# async def auto_draw():
#     channel = client.get_channel(YOUR_CHANNEL_ID)  # Replace with your channel ID
#     participants = lotto_data["participants"]
#     jackpot = lotto_data["jackpot"]

#     if not participants:
#         await channel.send("No participants this round. Better luck next time!")
#         return

#     # Weighted draw
#     weighted_pool = [user for user, tickets in participants.items() for _ in range(tickets)]
#     winner = random.choice(weighted_pool)

#     await channel.send(f"🎉 Congratulations <@{winner}>! You won the jackpot of {jackpot} 🎉")

#     # Reset lotto
#     lotto_data["participants"] = {}
#     lotto_data["jackpot"] = 0

# Start the task when the bot is ready
# @client.event
# async def on_ready():
#     auto_draw.start()

# Command to start a lotto
@client.command(name="sl")
async def sl(ctx, name):
    lotto_data = get_lotto_data()

    # Check if a lotto is already active
    if lotto_data["is_active"]:
        await ctx.send("A lotto is already active! Finish it before starting a new one.")
        return

    # Initialize the lotto
    reset_lotto_data()
    set_lotto_data("is_active", True)
    set_lotto_data("creator", ctx.author.name)
    set_lotto_data("start_time", time.time())
    set_lotto_data("end_time", time.time() + 86400)

    embed = discord.Embed(
        title="Lotto Time!",
        description=(
            "Click the button below to join the lotto and stand a chance to win the jackpot!\n\n"
            f"🎟 !j and !join to join lotto\n"
            f"@lotto {ctx.author.name} started a lotto for {name}\n"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Lotto started by {ctx.author.name}")

    # Pass lotto_data to LottoView
    await ctx.send(embed=embed, view=LottoView(lotto_data))
# Command to join the lotto
@client.command(name="j")
async def join_lotto(ctx):
    await handle_join_lotto(ctx)

@client.command(name="join")
async def join_lotto_alias(ctx):
    await handle_join_lotto(ctx)

# Command to check lotto status
@client.command(name="status")
async def lotto_status(ctx):
    global active_lotto, lotto_participants

    # Check if a lotto is active
    if not active_lotto:
        await ctx.send("No active lotto!")
        return

    # Generate participant list
    participant_list = "\n".join([participant["name"] for participant in lotto_participants])
    if not participant_list:
        participant_list = "No participants yet."

    embed = discord.Embed(
        title="Lotto Status",
        description=(
            f"💰 **Jackpot**: {active_lotto['jackpot']} coins\n"
            f"👑 **Started by**: {active_lotto['creator']}\n\n"
            "**Participants:**\n" + participant_list
        ),
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@client.command(name="cd")
async def countdown(ctx):
    countdown_time = 5 # set the countdown duration in seconds

    # send the countdown messages
    for remaining in range(countdown_time, 0, -1):
        await ctx.send(f"⏳ The lotto will be drawn in {remaining} seconds ⏳")
        await asyncio.sleep(1)  # Wait for 1 second

        # Notify when countdown ends
    await ctx.send("🎉 The lotto is being drawn now! 🎉")
    await draw_lotto(ctx)
    reset_lotto_data(ctx)


# Function to draw the lotto winner
async def draw_lotto(ctx):
    print("lotto data", lotto_data)
    lotto_data = get_lotto_data()
    # Check if participants joined the lotto
    if not lotto_data["participants"]:
        await ctx.send("No participants joined the lotto!")
        return 
    
    # pick a random winner 
    lotto_data = get_lotto_data()
    winner_id = random.choice(lotto_data["participants"])
    winner = ctx.guild.get_member(winner_id) # Get the discord member object 
        # Announce the winner
    await ctx.send(f"🎉 Congratulations {winner.mention}! You have won the jackpot of {lotto_data['jackpot']} coins! 🎉")

    # Reset lotto data for the next round
    lotto_data["participants"] = []
    lotto_data["jackpot"] = 0



    # Add the Lotto View with the Join Button
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



