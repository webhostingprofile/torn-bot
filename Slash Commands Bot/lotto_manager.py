import time

# Global lotto data
_lotto_data = {
    "is_active": False,
    "participants": [],  # List of participants
    "jackpot": 0,
    "start_time": None,
    "end_time": None,
    "creator": None
}

# Getter for lotto data
def get_lotto_data():
    return _lotto_data

# Setter for lotto data
def set_lotto_data(key, value):
    global _lotto_data
    if key in _lotto_data:
        _lotto_data[key] = value
    else:
        raise KeyError(f"Invalid key: {key}")

# Reset lotto data
def reset_lotto_data():
    global _lotto_data
    _lotto_data = {
        "is_active": False,
        "participants": [],
        "jackpot": 0,
        "start_time": None,
        "end_time": None,
        "creator": None
    }


# Shared logic for joining the lotto
async def handle_join_lotto(ctx):
    # Fetch active lotto data
    lotto_data = get_lotto_data()

    # Check if a lotto is active
    if not lotto_data["is_active"]:
        await ctx.send("No active lotto! Start one using `!sl`.")
        return

    # Check if user is already a participant
    if ctx.author.id in [participant["id"] for participant in lotto_data["participants"]]:
        await ctx.send(f"{ctx.author.name}, you have already joined the lotto!")
        return

    # Add user to participants
    participants = lotto_data["participants"]
    participants.append({"id": ctx.author.id, "name": ctx.author.name})
    set_lotto_data("participants", participants)

    # Respond to the user
    await ctx.send(f"{ctx.author.name} has joined the lotto! Total participants: {len(participants)}.")