import textwrap
from typing import TYPE_CHECKING

import discord
from discord import app_commands, Interaction
from discord.ext import commands

if TYPE_CHECKING:
    from ..bot import Bot


class CoreHelp(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot


@app_commands.command(name='help', description="See the commands that this bot has to offer")
async def help_cmd(self, itx: Interaction):
    title = "Bot Help Commands"

    description = textwrap.dedent(
        """For further help, use /cmd and see the hints that discord provides

        **Available Commands**
       
    """
    )
    embed = discord.Embed(title=title, description=description)
    await itx.response.send_message(embed=embed, ephemeral=True)
