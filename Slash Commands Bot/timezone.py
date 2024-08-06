import discord
from discord.ui import Select, View, Button
from database import get_firestore_db

UTC_OFFSETS = [f"TCT{n:+}" for n in range(-12, 15)]
ITEMS_PER_PAGE = 25

def get_paginated_options(page): 
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return UTC_OFFSETS[start:end]

class TimezoneView(View):
    def __init__(self, current_page=0):
        super().__init__(timeout=60)
        self.current_page = current_page
        self.message = None  # To store the reference to the message with the interactive component
        self.update_select_options()

    def update_select_options(self):
        self.clear_items()
        options = get_paginated_options(self.current_page)
        select = Select(
            placeholder="Choose your TCT offset...",
            options=[discord.SelectOption(label=tz, value=tz) for tz in options]
        )
        select.callback = self.select_callback
        self.add_item(select)

        # Add pagination buttons if needed
        if self.current_page > 0:
            self.add_item(Button(label='Previous', style=discord.ButtonStyle.secondary, custom_id='previous'))
        if (self.current_page + 1) * ITEMS_PER_PAGE < len(UTC_OFFSETS):
            self.add_item(Button(label='Next', style=discord.ButtonStyle.secondary, custom_id='next'))

    async def select_callback(self, interaction):
        selected_tz = interaction.data['values'][0]
        discord_id = str(interaction.user.id)
        db = get_firestore_db()

        converted_to_utc_TZ = convert_tct_to_utc_offset(selected_tz)
        db.collection('user_keys').document(discord_id).set({
            'time_zone': converted_to_utc_TZ
        }, merge=True)

        await interaction.response.send_message(f"Time zone set to {selected_tz}", ephemeral=True)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, custom_id='previous')
    async def previous(self, button, interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_select_options()
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, custom_id='next')
    async def next(self, button, interaction):
        if (self.current_page + 1) * ITEMS_PER_PAGE < len(UTC_OFFSETS):
            self.current_page += 1
            self.update_select_options()
            await interaction.response.edit_message(view=self)

# Function to convert TCT offset to UTC offset
def convert_tct_to_utc_offset(tct_str):
    if tct_str.startswith("TCT"):
        offset_str = tct_str[3:]  # Get the part after "TCT"
        if offset_str == "0":
            return "UTC+0"
        else:
            return "UTC" + offset_str
    return "UTC+0"  # Default to UTC+0 if something goes wrong
