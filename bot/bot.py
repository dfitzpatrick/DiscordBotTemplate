from typing import Tuple

import discord.ext.commands
from discord.ext import commands
import logging

log = logging.getLogger(__name__)


def ext_status(ext: str, status: str):
    return f"Extension {ext}: {status}"


class Bot(commands.Bot):

    def __init__(self, *, initial_extensions: Tuple[str] = (), **kwargs):
        super(Bot, self).__init__(**kwargs)
        self.initial_extensions = initial_extensions

    async def load_extensions(self, extensions: Tuple[str]):
        for ext in extensions:
            status = ""
            try:
                await self.load_extension(ext)
                status = "Loaded"
            except commands.ExtensionAlreadyLoaded:
                await self.reload_extension(ext)
                status = "Reloaded"
            finally:
                log.debug(ext_status(ext, status))

    async def setup_hook(self) -> None:
        await self.load_extensions(self.initial_extensions)

