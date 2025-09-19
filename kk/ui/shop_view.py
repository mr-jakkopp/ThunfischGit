import discord
from typing import List

from ..config import CATEGORY_EMOJIS, SHOP_VIEW_TIMEOUT
from ..data_store import load_shop, load_stats, save_stats
from ..shop import group_items, get_item

class ShopView(discord.ui.View):
    """3 levels:
    - [] root: show categories
    - [category]: show groups within category
    - [category, group]: show items in group
    """
    def __init__(self, user_id: str, path: List[str] | None = None, display_name: str = ""):
        super().__init__(timeout=SHOP_VIEW_TIMEOUT)
        self.user_id = user_id
        self.path = path or []
        self.display_name = display_name
        self.message: discord.Message | None = None
        self._build()

    # ---------- UI construction ----------
    def _build(self):
        shop = load_shop()
        if len(self.path) == 0:
            # root: categories
            for cat in shop.keys():
                emoji = CATEGORY_EMOJIS.get(cat, "📦")
                self.add_item(_NavButton(f"{emoji} {cat}", self.path + [cat], self.user_id, self.display_name))
        elif len(self.path) == 1:
            # groups
            cat = self.path[0]
            grouped = group_items(shop, cat)
            for grp in grouped.keys():
                self.add_item(_NavButton(f"📂 {grp}", self.path + [grp], self.user_id, self.display_name))
            self.add_item(_BackButton(self.path[:-1], self.user_id))
        else:
            # items in group
            cat, grp = self.path[0], self.path[1]
            grouped = group_items(shop, cat)
            for item_id, item in grouped.get(grp, []):
                self.add_item(_ItemButton(item_id, item, cat, self.user_id, self.path))
            self.add_item(_BackButton(self.path[:-1], self.user_id))

    async def on_timeout(self):
        # print("timeout")
        if self.message:
            try:
                # print(2)
                await self.message.delete()
            except Exception:
                pass

    def make_embed(self) -> discord.Embed:
        title = "🛍 Katzenklo-Shop"
        if self.path:
            title += " – " + " > ".join(self.path)

        shop = load_shop()
        embed = discord.Embed(title=title, color=discord.Color.blurple())
        embed.set_footer(text=f"Shop für {self.display_name}")

        if len(self.path) == 0:
            # list categories
            embed.description = "\n".join([f"{CATEGORY_EMOJIS.get(cat, '📦')} **{cat}**" for cat in shop.keys()]) or "Keine Inhalte hier."
        elif len(self.path) == 1:
            # list groups
            cat = self.path[0]
            grouped = group_items(shop, cat)
            embed.description = "\n".join([f"📂 **{g}**" for g in grouped.keys()]) or "Keine Inhalte hier."
        else:
            # list items
            cat, grp = self.path[0], self.path[1]
            grouped = group_items(shop, cat)
            lines = [f"💰 **{item['price']}** – {item['name']}" for _iid, item in grouped.get(grp, [])]
            embed.description = "\n".join(lines) if lines else "Keine Inhalte hier."

        return embed

class _NavButton(discord.ui.Button):
    def __init__(self, label: str, new_path, user_id: str, display_name: str):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.new_path = new_path
        self.user_id = user_id
        self.display_name = display_name

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if user_id != self.user_id:
            await interaction.response.send_message("❌ Das ist nicht dein Shop.", ephemeral=True)
            return
        view = ShopView(self.user_id, self.new_path, self.display_name)
        await interaction.response.edit_message(embed=view.make_embed(), view=view)
        view.message = interaction.message

class _ItemButton(discord.ui.Button):
    def __init__(self, item_id: str, item: dict, category: str, user_id: str, path: list):
        stats = load_stats()
        owned = stats.get(user_id, {}).get("owned", {}).get(category, [])
        equipped = stats.get(user_id, {}).get("equipped", {}).get(category, [])

        label = item["name"]
        style = discord.ButtonStyle.success
        disabled = False

        if item_id in equipped:
            style = discord.ButtonStyle.secondary
            label = f"⭐ {item['name']}"
            disabled = True
        elif item_id in owned:
            style = discord.ButtonStyle.primary
            label = f"🎒 {item['name']}"
        else:
            label = f"💰 {item['price']} – {item['name']}"

        super().__init__(label=label, style=style, disabled=disabled)
        self.item_id = item_id
        self.item = item
        self.category = category
        self.user_id = user_id
        self.path = path

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        stats = load_stats()
        user_id = str(interaction.user.id)

        if user_id != self.user_id:
            await interaction.followup.send("❌ Das ist nicht dein Shop.", ephemeral=True)
            return

        owned = stats.get(user_id, {}).get("owned", {}).get(self.category, [])
        equipped = stats.get(user_id, {}).get("equipped", {}).get(self.category, [])

        if self.item_id not in owned:
            # purchase flow
            embed = discord.Embed(
                title=f"🛒 {self.item['name']}",
                description=f"Preis: 💰 {self.item['price']}\n{self.item.get('description','')}",
                color=discord.Color.blurple()
            )
            if "image" in self.item:
                file = discord.File(self.item["image"], filename="item.png")
                embed.set_thumbnail(url="attachment://item.png")
            await interaction.followup.send(
                embed=embed, file=file,
                view=_ConfirmView(interaction.message, self.item_id, self.item, self.category, self.user_id, self.path),
                ephemeral=True
            )
        elif self.item_id not in equipped:
            stats[user_id]["equipped"].setdefault(self.category, [])
            stats[user_id]["equipped"][self.category] = [self.item_id]
            save_stats(stats)
            await interaction.followup.send(f"✅ {self.item['name']} jetzt ausgerüstet!", ephemeral=True)
            new_view = ShopView(self.user_id, self.path)
            await interaction.message.edit(embed=new_view.make_embed(), view=new_view)

class _ConfirmView(discord.ui.View):
    def __init__(self, shop_message: discord.Message, item_id: str, item: dict, category: str, user_id: str, path: list):
        super().__init__(timeout=SHOP_VIEW_TIMEOUT)
        self.shop_message = shop_message
        self.add_item(_ConfirmButton(shop_message, item_id, item, category, user_id, path))
        self.add_item(_CancelButton(shop_message))

class _ConfirmButton(discord.ui.Button):
    def __init__(self, shop_message: discord.Message, item_id: str, item: dict, category: str, user_id: str, path: list):
        super().__init__(label="✅ Kaufen", style=discord.ButtonStyle.success)
        self.shop_message = shop_message
        self.item_id = item_id
        self.item = item
        self.category = category
        self.user_id = user_id
        self.path = path

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        stats = load_stats()

        if user_id not in stats:
            stats[user_id] = {"owned": {}, "equipped": {}, "balance": 0}

        balance = stats[user_id].get("balance", 0)
        price = self.item["price"]

        if balance < price:
            await interaction.response.send_message(
                f"❌ Du hast nicht genug Münzen! (Kontostand: {balance}, Preis: {price})",
                ephemeral=True
            )
            await self.shop_message.delete()
            return

        stats[user_id]["balance"] = balance - price

        stats[user_id]["owned"].setdefault(self.category, [])
        if self.item_id not in stats[user_id]["owned"][self.category]:
            stats[user_id]["owned"][self.category].append(self.item_id)

        stats[user_id]["equipped"].setdefault(self.category, [])
        stats[user_id]["equipped"][self.category] = [self.item_id]

        save_stats(stats)

        embed = discord.Embed(
            title=f"✅ Gekauft & ausgerüstet: {self.item['name']}",
            description=f"Du hast dieses Item für 💰 {price} gekauft!\n💰 Neuer Kontostand: {stats[user_id]['balance']}",
            color=discord.Color.green()
        )
        if "image" in self.item:
            file = discord.File(self.item["image"], filename="item.png")
            embed.set_thumbnail(url="attachment://item.png")
            await interaction.response.edit_message(embed=embed, attachments=[file], view=None)
        else:
            await interaction.response.edit_message(embed=embed, view=None)

        await self.shop_message.delete()

class _CancelButton(discord.ui.Button):
    def __init__(self, shop_message: discord.Message):
        super().__init__(label="❌ Abbrechen", style=discord.ButtonStyle.danger)
        self.shop_message = shop_message

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="❌ Kauf abgebrochen.", embed=None, view=None)
        await self.shop_message.delete()

class _BackButton(discord.ui.Button):
    def __init__(self, new_path, user_id):
        super().__init__(label="⬅️ Zurück", style=discord.ButtonStyle.danger)
        self.new_path = new_path
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        view = ShopView(self.user_id, self.new_path)
        await interaction.response.edit_message(embed=view.make_embed(), view=view)
