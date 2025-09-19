import discord
from discord.ext import commands
import asyncio
import logging
logging.basicConfig(level=logging.INFO)
from kk.config import DISCORD_TOKEN, GUILD_ID

# Your bot intents
intents = discord.Intents.default()
intents.message_content = True

# Prefix + hybrid support
bot = commands.Bot(command_prefix="$", intents=intents)
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")


@bot.command(name="sync")
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def sync(ctx: commands.Context):
    """Manually sync slash commands to the guild"""
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)  # copy cmds into guild scope
    synced = await bot.tree.sync(guild=guild)
    await ctx.send(f"🔄 Synced {len(synced)} commands to guild {GUILD_ID}")


@bot.command(name="clear_guild_cmds")
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def clear_guild_cmds(ctx: commands.Context):
    guild = discord.Object(id=GUILD_ID)
    bot.tree.clear_commands(guild=guild)   # remove local cache
    cmds = await bot.tree.sync(guild=guild)  # push clear to Discord
    await ctx.send(f"🗑️ Cleared {len(cmds)} guild commands for {GUILD_ID}")

@bot.command(name="clear_global_cmds")
@commands.has_permissions(administrator=True)
async def clear_global_cmds(ctx: commands.Context):
    bot.tree.clear_commands()        # wipe global cache
    cmds = await bot.tree.sync()     # push clear globally
    await ctx.send(f"🗑️ Cleared {len(cmds)} global commands")

# setup_hook runs before the bot connects
async def setup_hook():
    await bot.load_extension("cogs.katzenklo")

    # make sure commands are copied to guild + synced instantly
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)

bot.setup_hook = setup_hook

async def main():
    async with bot:
        await bot.start(DISCORD_TOKEN)

asyncio.run(main())