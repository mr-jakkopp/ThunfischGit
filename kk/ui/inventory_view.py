import discord

from ..config import CATEGORY_EMOJIS
from ..data_store import load_stats, save_stats, load_shop

class InventoryView(discord.ui.View):
    def __init__(self, user_id: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        shop = load_shop()
        for category, emoji in CATEGORY_EMOJIS.items():
            if category in shop:
                self.add_item(_CategoryButton(category, emoji, user_id))

    def make_embed(self):
        embed = discord.Embed(
            title="🎒 Inventar",
            description="Wähle eine Kategorie, um deine Items zu sehen und auszurüsten.",
            color=discord.Color.blue()
        )
        for cat, emoji in CATEGORY_EMOJIS.items():
            embed.add_field(name=f"{emoji} {cat}", value="Klicken zum Öffnen", inline=True)
        return embed

class _CategoryButton(discord.ui.Button):
    def __init__(self, category: str, emoji: str, user_id: str):
        super().__init__(label=f"{emoji} {category}", style=discord.ButtonStyle.primary)
        self.category = category
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        new_view = CategoryInventoryView(self.user_id, self.category)
        await interaction.response.edit_message(embed=new_view.make_embed(), view=new_view)

class CategoryInventoryView(discord.ui.View):
    def __init__(self, user_id: str, category: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.category = category

        stats = load_stats()
        shop = load_shop()
        owned = stats.get(user_id, {}).get("owned", {}).get(category, [])
        equipped = stats.get(user_id, {}).get("equipped", {}).get(category, [])

        for item_id in owned:
            item = shop.get(category, {}).get(item_id)
            if not item:
                continue

            label = item.get("name", item_id)
            style = discord.ButtonStyle.primary
            disabled = False

            if item_id in equipped:
                label = f"⭐ {label}"
                style = discord.ButtonStyle.secondary
                disabled = True

            self.add_item(_EquipButton(label, style, disabled, category, item_id, user_id))

        self.add_item(_BackToInventoryButton(user_id))

    def make_embed(self):
        from ..config import CATEGORY_EMOJIS
        emoji = CATEGORY_EMOJIS.get(self.category, "📦")
        embed = discord.Embed(
            title=f"{emoji} {self.category}",
            description="Klicke auf ein Item, um es auszurüsten.",
            color=discord.Color.green()
        )
        return embed

class _EquipButton(discord.ui.Button):
    def __init__(self, label, style, disabled, category, item_id, user_id):
        super().__init__(label=label, style=style, disabled=disabled)
        self.category = category
        self.item_id = item_id
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        stats = load_stats()
        user_id = str(interaction.user.id)

        if user_id != self.user_id:
            await interaction.response.send_message("❌ Das ist nicht dein Inventar.", ephemeral=True)
            return

        stats[user_id]["equipped"][self.category] = [self.item_id]
        save_stats(stats)

        await interaction.response.send_message(f"✅ {self.item_id} ausgerüstet!", ephemeral=True)

        new_view = CategoryInventoryView(self.user_id, self.category)
        await interaction.message.edit(embed=new_view.make_embed(), view=new_view)

class _BackToInventoryButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(label="⬅️ Zurück", style=discord.ButtonStyle.danger)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        new_view = InventoryView(self.user_id)
        await interaction.response.edit_message(embed=new_view.make_embed(), view=new_view)
