import os
import discord
from ..config import SHOP_VIEW_TIMEOUT
from ..data_store import load_stats, load_cats, load_shop

class KatzalogView(discord.ui.View):
    def __init__(self, user_id: str):
        super().__init__(timeout=SHOP_VIEW_TIMEOUT)
        self.user_id = user_id
        self.cats_db = load_cats()
        self.groups = self._collect_groups()
        print(self.groups)
        self.index = 0
        self.message: discord.Message | None = None
        # self.group_button.label = list(sorted(self.groups.keys()))[0]

    def _collect_groups(self):
        stats = load_stats()
        cats_seen = stats.get(self.user_id, {}).get("cats_seen", {})
        groups = {}
        for cname, entry in cats_seen.items():
            group = self.cats_db.get(cname, {}).get("group", "Andere")
            groups.setdefault(group, []).append((cname, entry))
        return groups

    def _render_current(self):
        shop = load_shop()
        if not self.groups:
            empty = discord.Embed(
                title="📒 Katzalog",
                description="Noch keine Katzen entdeckt.",
                color=discord.Color.blurple()
            )
            return [empty], []

        group_name = list(sorted(self.groups.keys()))[self.index]
        self.group_name = group_name
        self.group_button.label = group_name  # 🔑 update label dynamically

        cats = self.groups[group_name]
        embeds, files = [], []

        for cname, seen in cats:
            db = self.cats_db.get(cname, {})
            visits = seen.get("visits", 0)
            pmin = seen.get("pay_min") or db.get("pay_min")
            pmax = seen.get("pay_max") or db.get("pay_max")
            payout = f"{pmin}–{pmax}ℂ" if pmin and pmax else "?"

            em = discord.Embed(title=f"🐾 {seen.get('name', cname)}", color=discord.Color.blurple())
            em.add_field(name="👀 Besuche", value=str(visits), inline=True)
            em.add_field(name="💰 Auszahlung", value=payout, inline=True)

            for cat, items in (seen.get("matching_favs") or {}).items():
                pretty = ", ".join([shop[cat][item]["name"] for item in items]) if items else "???"
                em.add_field(name=f"⭐ {cat}", value=pretty, inline=False)

            img_path = f"img/cats/{cname.lower()}.png"
            if img_path and os.path.exists(img_path):
                fname = f"{cname}.png"
                files.append(discord.File(img_path, filename=fname))
                em.set_thumbnail(url=f"attachment://{fname}")

            embeds.append(em)

        embeds[-1].set_footer(text=f"Gruppe: {group_name} · Seite {self.index+1}/{len(self.groups)}")
        return embeds, files

    # -------- Buttons ----------
    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Nicht dein Katzalog.", ephemeral=True)
        self.index = (self.index - 1) % len(self.groups)
        embeds, files = self._render_current()
        await interaction.response.edit_message(embeds=embeds, attachments=files, view=self)

    @discord.ui.button(label="PlACEHOLDER", style=discord.ButtonStyle.secondary, disabled=True)
    async def group_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Nicht dein Katzalog.", ephemeral=True)
        self.index = (self.index + 1) % len(self.groups)
        embeds, files = self._render_current()
        await interaction.response.edit_message(embeds=embeds, attachments=files, view=self)
