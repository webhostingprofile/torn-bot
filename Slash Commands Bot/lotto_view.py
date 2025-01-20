from discord.ui import Button, View
import discord
from lotto_manager import get_lotto_data, set_lotto_data

class LottoView(View):
    def __init__(self, active_lotto):
        super().__init__(timeout=None)
        self.active_lotto = active_lotto  # Pass active lotto info

    @discord.ui.button(label="Join Lotto", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Fetch active lotto data
        lotto_data = get_lotto_data()

        # Check if a lotto is active
        if not lotto_data["is_active"]:
            await interaction.response.send_message("No active lotto! Start one using `!sl`.", ephemeral=True)
            return

        # Check if user is already a participant
        if interaction.user.id in [participant["id"] for participant in lotto_data["participants"]]:
            await interaction.response.send_message("You have already joined the lotto!", ephemeral=True)
            return

        # Add user to participants
        participants = lotto_data["participants"]
        participants.append({"id": interaction.user.id, "name": interaction.user.name})
        set_lotto_data("participants", participants)

        # Respond to the user
        await interaction.response.send_message(
            f"{interaction.user.name} has joined the lotto! Total participants: {len(participants)}.",
            ephemeral=False
        )
