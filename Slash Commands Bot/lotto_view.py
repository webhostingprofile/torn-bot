from discord.ui import Button, View
import discord
from torn import join_lotto_logic
import time

# Global dictionary to store lotto data
lotto_data = {
    "participants": {},  # Format: {discord_id: ticket_count}
    "jackpot": 0,
    "start_time": time.time(),
    "end_time": time.time() + 86400  # Example: 24 hours from start
}



# Define a new view with a Join Button
class LottoView(View):



    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Join Lotto", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global active_lotto, lotto_participants

        # Check if a lotto is active
        if not active_lotto:
            await interaction.response.send_message("No active lotto! Start one using `!sl`.", ephemeral=True)
            return

        # Check if user is already a participant
        if interaction.user.id in [participant["id"] for participant in lotto_participants]:
            await interaction.response.send_message("You have already joined the lotto!", ephemeral=True)
            return

        # Add user to participants
        lotto_participants.append({"id": interaction.user.id, "name": interaction.user.name})
        
        await interaction.response.send_message(
            f"{interaction.user.name} has joined the lotto! Total participants: {len(lotto_participants)}.",
            ephemeral=False
        )
