from discord.ui import Button, View
import discord

# Define a new view with a Join Button
class LottoView(View):
    def __init__(self):
        super().__init__()
        self.add_item(Button(label="Join Lotto", style=discord.ButtonStyle.green, custom_id="join_lotto"))
