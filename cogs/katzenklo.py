import io
import datetime
import random
import discord
from discord.ext import commands

from kk.config import (
    SUMMARY_CHANNEL_ID,
    CAT_VISIT_HOUR,
    CAT_PAYOUT_MIN,
    CAT_PAYOUT_MAX,
    LITTERSTATE_NAMES,
    LAYERING_ORDER,
    ESSENTIAL_CATEGORIES,
    DEFAULT_START_ITEMS,
    EVENT_HOURS,
    LEAVE_PERCENT,
    NO_CAT_PERCENT,
    PISS_PERCENT,
    POOP_PERCENT,
    PISSPOOP_CLEAN_COST,
    SINGLE_CLEAN_COST,
    DIRTY_MULTIPLIER_PERCENTS,
    CAT_PAYOUT_PERCENT,
    CATEGORY_EMOJIS,
    EVENT_HOURS_SHIFT
)
from kk.data_store import load_shop, load_stats, save_stats, load_cats
from kk.scheduler import wait_until_hour, sleep_until_next_full_hour, sleep_for_hours, asyncio
from kk.render import render_katzenklo
from kk.ui.shop_view import ShopView, group_items
from kk.ui.inventory_view import InventoryView
from kk.ui.summary_view import ClearSummaryView
from kk.ui.katzalog_view import KatzalogView
from kk.utils import intersect, now


class Katzenklo(commands.Cog):
    """Main cog for the Katzenklo mini-game."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop.create_task(self._cat_visit_scheduler())
        # self.bot.loop.create_task(self._hourly_scheduler())

    # ------------- SCHEDULERS -------------
    # async def _hourly_scheduler(self):
    #     await self.bot.wait_until_ready()
    #     while not self.bot.is_closed():
    #         await sleep_until_next_full_hour()
    #         await self._hourly_event()

    async def _cat_visit_scheduler(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            next_hour = (now().hour + ((EVENT_HOURS_SHIFT - now()) % EVENT_HOURS or EVENT_HOURS)) % 24 # too lazy to fix issue with timezones in docker
            print(f"Uhrzeit: {now().hour} | Nächster Besuch: {next_hour}")
            await wait_until_hour(next_hour, 0)
            await self._regular_event()
            # print("Uhrzeit:", datetime.datetime.now().hour,"| Nächster Besuch:", datetime.datetime.now() + datetime.timedelta(minutes=3))
            # await asyncio.sleep(3*60)
            # await self._regular_event()

    # async def _x_hourly_scheduler(self):
    #     await self.bot.wait_until_ready()
    #     while not self.bot.is_closed():
    #         await sleep_for_hours(EVENT_HOURS)
    #         await self._regular_event()

    # ------------- EVENTS -------------
    # async def _hourly_event(self):
    #     """Example hourly reward."""
    #     stats = load_stats()
    #     rewards = []
    #     for uid, user in stats.items():
    #         user["balance"] = user.get("balance", 0) + 1
    #         rewards.append(f"<@{uid}> bekam 1 Münze für Aktivität 🕒")
    #     save_stats(stats)

    #     if SUMMARY_CHANNEL_ID and rewards:
    #         ch = self.bot.get_channel(SUMMARY_CHANNEL_ID)
    #         if ch:
    #             await ch.send("⏰ **Stündliche Belohnung**\n" + "\n".join(rewards))

    # async def _cat_visit_event(self):
    #     stats = load_stats()
    #     cats = load_cats()
    #     rewards = []

    #     for uid, user in stats.items():
    #         eq = user.get("equipped", {})

    #         if not all(eq.get(cat) for cat in ESSENTIAL_CATEGORIES):
    #             continue  # must have essentials equipped

    #         cat_name = random.choice(list(cats.keys())) if cats else None
    #         cat = cats.get(cat_name, {}) if cat_name else {}

    #         payout = random.randint(CAT_PAYOUT_MIN, CAT_PAYOUT_MAX)
    #         if cat:
    #             payout = min(payout, int(cat.get("budget", payout)))

    #         user["balance"] = user.get("balance", 0) + payout
    #         user.setdefault("cats_seen", [])
    #         if cat_name and cat_name not in user["cats_seen"]:
    #             user["cats_seen"].append(cat_name)

    #         user["dirty"] = random.choice(["piss", "poop", "pisspoop"])  # dirty after one visit
    #         rewards.append(f"<@{uid}> bekam {payout} Münzen von {cat_name or 'KATZE'}")  # fallback name

    #     save_stats(stats)

    #     if SUMMARY_CHANNEL_ID and rewards:
    #         ch = self.bot.get_channel(SUMMARY_CHANNEL_ID)
    #         if ch:
    #             await ch.send("🐾 **Katzenbesuche**\n" + "\n".join(rewards))

    async def _regular_event(self):
        stats = load_stats()
        cats = load_cats()

        for uid in stats:
            # ------------- CAT LEAVES -------------
            if stats[uid]["occupied"]:
                final_leave_percent = LEAVE_PERCENT**(1/(DIRTY_MULTIPLIER_PERCENTS**(int("piss" in stats[uid]["dirty"]) + int("poop" in stats[uid]["dirty"]))))
                leaving = (random.random() < final_leave_percent)
                if leaving:
                    message = f"Deine Katze {stats[uid]["occupied"]} hat dich leider verlassen und dein Katzenklo ist jetzt unbesetzt. ({now().strftime("am %d.%m.%Y um %H Uhr")})"
                    stats[uid]["occupied"] = False
                    stats[uid]["summary"].append(message)

            # ------------- CAT COMES -------------
            if not stats[uid]["occupied"]:
                cat_list = []
                for cat in [cat for cat in cats.keys() if (cats[cat].get("go_anywhere", False) or stats[uid]["equipped"]["Orte"][0] in cats[cat]["favs"]["Orte"])]:
                    for item in stats[uid]["equipped"]:
                        if stats[uid]["equipped"][item][0] in cats[cat]["favs"][item]:
                            cat_list.append(cat)
                final_no_cat_percent = NO_CAT_PERCENT**(1/(DIRTY_MULTIPLIER_PERCENTS**(2*int("piss" in stats[uid]["dirty"]) + 4*int("poop" in stats[uid]["dirty"]))))
                if random.random() > final_no_cat_percent:
                    chosen_cat = random.choice(cat_list)
                    message = f"Die Katze {cats[chosen_cat]["name"]} hat sich in dein Katzenklo gesetzt. ({now().strftime("am %d.%m.%Y um %H Uhr")})"
                    stats[uid]["summary"].append(message)
                    stats[uid]["occupied"] = chosen_cat
                    if chosen_cat not in stats[uid]["cats_seen"]:
                        stats[uid]["cats_seen"][chosen_cat] = {
                            "name": cats[chosen_cat]["name"],
                            "pay_min": None,
                            "pay_max": None,
                            "matching_favs":{
                                "Katzenklos": [],
                                "Katzenstreu": [],
                                "Dekoartikel": [],
                                "Orte": [],
                                "Schilder": [],
                                "Schildtexte": []
                            },
                            "visits": 0
                        }
                    
                    print(uid, chosen_cat)
                    print(stats[uid]["equipped"])

                    for item in stats[uid]["equipped"]:
                        # print(cats[cat]["favs"])
                        # print(stats[uid]["equipped"][item][0])
                        # print(cats[cat]["favs"][item])
                        matching_favs = set(stats[uid]["cats_seen"][chosen_cat]["matching_favs"][item])
                        print(intersect(stats[uid]["equipped"][item], cats[chosen_cat]["favs"][item]))
                        if a:= intersect(stats[uid]["equipped"][item], cats[chosen_cat]["favs"][item]): #[0] in cats[cat]["favs"][item]:
                            print(a)
                            new = matching_favs.union(set(a))
                            print(new)
                            stats[uid]["cats_seen"][chosen_cat]["matching_favs"][item] = list(new)
                    print(stats[uid]["cats_seen"][chosen_cat]["matching_favs"])
                    stats[uid]["cats_seen"][chosen_cat]["visits"] += 1
                    

            # ------------- CAT GIVES STUFF AND PAYS ------------- (GIVES STUFF WIP)
            if stats[uid]["occupied"]:
                if random.random() < CAT_PAYOUT_PERCENT:
                    pay_amount = random.randrange(cats[stats[uid]["occupied"]]["pay_min"], cats[stats[uid]["occupied"]]["pay_max"])
                    stats[uid]["balance"] += pay_amount
                    stats[uid]["cats_seen"][stats[uid]["occupied"]]["pay_min"] = min(stats[uid]["cats_seen"][stats[uid]["occupied"]]["pay_min"], pay_amount) if stats[uid]["cats_seen"][stats[uid]["occupied"]]["pay_min"] is not None else pay_amount
                    stats[uid]["cats_seen"][stats[uid]["occupied"]]["pay_max"] = max(stats[uid]["cats_seen"][stats[uid]["occupied"]]["pay_max"], pay_amount) if stats[uid]["cats_seen"][stats[uid]["occupied"]]["pay_max"] is not None else pay_amount
                    message = f"Die Katze {cats[stats[uid]["occupied"]]["name"]} hat dir einen wertvollen Gegenstand mitgebracht. Du hast ihn für {pay_amount}ℂ verkauft. ({now().strftime("am %d.%m.%Y um %H Uhr")})"
                    stats[uid]["summary"].append(message)

            # ------------- CAT USES LITTER BOX -------------
            if stats[uid]["occupied"]:

                state = stats[uid]["dirty"]

                new_state = ""
                if "piss" in state or random.random() < PISS_PERCENT: new_state += "piss"
                if "poop" in state or random.random() < POOP_PERCENT: new_state += "poop"
                new_state = "clean" if new_state == "" else new_state
                message = f"Die Katzenklo ist jetzt im Zustand: {LITTERSTATE_NAMES[new_state]}. ({now().strftime("am %d.%m.%Y um %H Uhr")})"#
                stats[uid]["summary"].append(message)
                stats[uid]["dirty"] = new_state




            save_stats(stats)
            

    # ------------- COMMAND GATE -------------
    async def cog_check(self, ctx: commands.Context):
        # allow /katzenklo start without account

        if ctx.command.qualified_name == "katzenklo start":
            return True
        
        stats = load_stats()
        if str(ctx.author.id) in stats:
            return True
        

        await ctx.send("Mache dir erst ein Konto mit /katzenklo start")
        return False

    # ------------- COMMANDS -------------
    @commands.hybrid_group(name="katzenklo", aliases=["kk"], with_app_command=True)
    async def katzenklo_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send("Nutze ein Subcommand wie `/katzenklo shop`")

    @katzenklo_group.command(name="catvisit", description="Manueller Katzenbesuch")
    @commands.is_owner()
    async def catvisit(self, ctx: commands.Context):
        await self._regular_event()
        await ctx.send("😺 Katzenbesuch wurde manuell ausgelöst!")

    @katzenklo_group.command(name="shop", description="Öffnet den Katzenklo-Shop")
    async def shop(self, ctx: commands.Context):
        view = ShopView(str(ctx.author.id), display_name=ctx.author.display_name)
        await ctx.send(embed=view.make_embed(), view=view)
        view.message = ctx

    # @katzenklo_group.command(name="shopoverview", description="Zeigt alle Items im Katzenklo-Shop")
    @katzenklo_group.command(name="shopoverview", description="Zeigt alle Items im Katzenklo-Shop")
    async def shopoverview(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🛍 Katzenklo-Shop Übersicht",
            description="Alle Items mit ihren Preisen",
            color=discord.Color.blurple()
        )

        # Kategorien mit ihren Items
        embed.add_field(
            name="🎨 Katzenklos",
            value="• **25** - Standard",
            inline=False
        )

        embed.add_field(
            name="✨ Dekoartikel",
            value="\n".join([
                "• **10** - Sterne",
                "• **25** – f",
                "• **50** - Lennartcoin",
            ]),
            inline=False
        )

        embed.add_field(
            name="🥛 Katzenklostreu",
            value="\n".join([
                "• **10** - Erde",
                "• **20** - Gitterstreu",
                "• **30** - Konfettistreu",
                "• **200** - Lennartstreu",
                "• **500** - Goldstreu",
            ]),
            inline=False
        )

        embed.add_field(
            name="🏷️ Schilder und -texte",
            value="\n".join([
                "• **20** - Schildtexte",
                "• **30** - Schilder",
            ]),
            inline=False
        )

        embed.add_field(
            name="📍 Orte",
            value="\n".join([
                "• **10** - Seitengasse",
                "• **10** - Waschsalon",
                "• **30** - Wald",
                "• **30** - Strand",
                "• **50** - Hügel",
                "• **50** - Friedhof",
                "• **200** - Flugzeugflügel",
                "• **300** - Museum",
                "• **400** - Lennarts Pool",
                "• **500** - Herbert's Benham Jaw Stone",
            ]),
            inline=False
        )

        embed.set_footer(text="Preise in ℂ")
        await ctx.send(embed=embed)


    @katzenklo_group.command(name="show", description="Zeigt dein Katzenklo mit allen Items")
    async def show(self, ctx: commands.Context, user: discord.User = None):
        user = ctx.author if user == None else user
        user_id = str(user.id)
        stats = load_stats()
        cats = load_cats()

        if user_id not in stats or "equipped" not in stats[user_id]:
            await ctx.send("❌ Du besitzt noch keine Items.")
            return

        equipped = stats[user_id]["equipped"]
        litter_state = stats[user_id].get("dirty", "clean")
        balance = stats[user_id].get("balance", 0)
        occupied = stats[user_id].get("occupied") if stats[user_id].get("occupied") else "Unbesetzt"
        cat_name = cats[occupied]['name'] if occupied != occupied else occupied
        news_count = len(stats[user_id].get("summary"))

        base = render_katzenklo(equipped, litter_state, occupied, load_shop())
        if not base:
            await ctx.send("❌ Keine gültigen Items gefunden.")
            return

        buffer = io.BytesIO()
        base.save(buffer, format="PNG")
        buffer.seek(0)

        file = discord.File(buffer, filename="katzenklo.png")
        embed = discord.Embed(title=f"{user.display_name}'s Katzenklo 🐾")
        embed.add_field(name="Sauberkeit ✨", value=LITTERSTATE_NAMES.get(litter_state, litter_state), inline=True)
        embed.add_field(name="Besetzt 😺", value=cat_name, inline=True)
        embed.add_field(name="ℂ 💰", value=str(balance), inline=True)
        embed.add_field(name="Neuigkeiten 🔰", value=str(news_count), inline=True)
        embed.set_image(url="attachment://katzenklo.png")
        await ctx.send(embed=embed, file=file)

    @katzenklo_group.command(name="balance", description="Zeigt dein Münzkonto")
    async def balance(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        stats = load_stats()
        balance = stats.get(user_id, {}).get("balance", 0)

        embed = discord.Embed(
            title=f"💰 Kontostand von {ctx.author.display_name}",
            description=f"Du hast aktuell **{balance}** ℂ.",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @katzenklo_group.command(name="inventory", description="Zeigt deine Items")
    async def inventory(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        stats = load_stats()
        owned = stats.get(user_id, {}).get("owned", {})

        if not owned:
            await ctx.send("❌ Du besitzt keine Items.")
            return

        view = InventoryView(user_id)
        await ctx.send(embed=view.make_embed(), view=view)

    @katzenklo_group.command(name = "summary", description="Zeigt die Zusammenfassung der vergangenen Ereignisse bis jetzt an.")
    async def summary(self, ctx: commands.Context, length: int = 20):
        length = length if length > 0 else 20
        summary = load_stats()[str(ctx.author.id)]['summary'][-length:]
        if summary:
            desc = "```md\n" + "\n\n".join(summary) + "\n```"
            if len(desc) > 4000:
                desc = "🛑Du versuchst zu viele Ereignisse anzuzeigen.🛑"
        else:
            desc = "Keine Ereignisse gespeichert."

        embed = discord.Embed(
            title="📜 Zusammenfassung",
            description=desc,
            color=discord.Color.blurple()
        )

        view = ClearSummaryView(ctx.author.id)
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @katzenklo_group.command(name="leaderboard", description="Zeigt die reichsten Spieler")
    async def leaderboard(self, ctx: commands.Context, limit: int = 20):
        stats = load_stats()

        balances = [(uid, data.get("balance", 0)) for uid, data in stats.items()]
        balances.sort(key=lambda x: x[1], reverse=True)

        embed = discord.Embed(
            title="💰 Münz-Leaderboard",
            description=f"Top {limit} Spieler mit den meisten ℂ",
            color=discord.Color.gold()
        )

        for i, (uid, balance) in enumerate(balances[:limit], start=1):
            user = ctx.guild.get_member(int(uid)) or await self.bot.fetch_user(int(uid))
            name = user.display_name if user else f"Unbekannt ({uid})"
            embed.add_field(name=f"#{i} {name}", value=f"**{balance}** ℂ", inline=False)

        await ctx.send(embed=embed)

    @katzenklo_group.command(name="clean", description="Reinigt dein Katzenklo")
    async def clean(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        stats = load_stats()
        litter_state = stats.get(user_id, {}).get("dirty", "clean")

        if litter_state == "clean":
            await ctx.send("Dein Katzenklo ist schon sauber.")
            return

        stats[user_id]["dirty"] = "clean"
        if litter_state == "pisspoop":
            stats[user_id]["balance"] = stats[user_id].get("balance", 0) - PISSPOOP_CLEAN_COST
            await ctx.send(f"Dein Katzenklo ist jetzt wieder sauber! Das hat dich {PISSPOOP_CLEAN_COST}ℂ gekostet.")
        else:
            stats[user_id]["balance"] = stats[user_id].get("balance", 0) - SINGLE_CLEAN_COST
            await ctx.send(f"Dein Katzenklo ist jetzt wieder sauber! Das hat dich {SINGLE_CLEAN_COST}ℂ gekostet.")

        save_stats(stats)

    @katzenklo_group.command(name="start", description="Baue dir dein Katzenklogeschäft auf!")
    async def start(self, ctx: commands.Context, force: bool = False):
        user_id = str(ctx.author.id)
        stats = load_stats()
        shop = load_shop()
        force == (force and await self.bot.is_owner(ctx.author))

        # print(force, await self.bot.is_owner(ctx.author))

        if user_id in stats and not force:
            await ctx.send("Du hast schon ein Katzenklo!")
            return

        def _pick_default(cat: str):
            pref = DEFAULT_START_ITEMS.get(cat)
            if pref and pref in shop.get(cat, {}):
                return pref
            # fallback to first item id if preferred not present
            return next(iter(shop.get(cat, {}).keys()), None)

        new_statblock = {
            "owned": {cat: ([iid] if (iid := _pick_default(cat)) else []) for cat in shop.keys()},
            "equipped": {cat: ([iid] if (iid := _pick_default(cat)) else []) for cat in shop.keys()},
            "balance": 10,
            "cats_seen": {},
            "dirty": "clean",
            "occupied": False,
            "summary": []
        }

        stats[user_id] = new_statblock
        save_stats(stats)

        await ctx.send("Juhuu! Du hast jetzt dein eigenes Katzenklo, schau es dir direkt an mit `/katzenklo show`!")

    @katzenklo_group.command(name="katzalog", description="Zeigt alle entdeckten Katzen (mit Bildern), gruppiert und seitenweise")
    async def katzalog(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        stats = load_stats()
        if stats[user_id]["cats_seen"]:
            view = KatzalogView(user_id)
            embeds, files = view._render_current()
            msg = await ctx.send(embeds=embeds, files=files, view=view, ephemeral=True)
            view.message = msg
        else:
            await ctx.send("🛑Du hast noch keine Katzen gesehen!🛑", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Katzenklo(bot))
