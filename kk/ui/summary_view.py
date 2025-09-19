import discord

from ..config import CATEGORY_EMOJIS
from ..data_store import load_stats, save_stats, load_shop

class ClearSummaryView(discord.ui.View):
    def __init__(self, uid):
        self.uid = str(uid)
        super().__init__(timeout=60)  # button works for 60s

    @discord.ui.button(label="🗑️ Log leeren", style=discord.ButtonStyle.danger)
    async def clear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        stats = load_stats()
        stats[self.uid]['summary'] = []
        save_stats(stats)
        await interaction.response.edit_message(content="✅ Zusammenfassung wurde geleert.", embed=None, view=None)
