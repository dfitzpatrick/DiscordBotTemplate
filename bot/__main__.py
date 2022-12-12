import discord
import os
from discord.ext import commands
import asyncio
import logging
from . import config
from .bot import Bot
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

extensions = (
    'bot.core',
)
required_envs = (
    ('TOKEN', "The Bot Token", str),
)


def intents() -> discord.Intents:
    intents = discord.Intents.none()
    intents.guilds = True
    return intents


async def bootstrap():

    config.assert_envs_exist(required_envs)
    token = os.environ['TOKEN']
    bot = Bot(
        intents=intents,
        command_prefix=commands.when_mentioned,
        slash_commands=True,
    )
    try:
        for ext in extensions:
            await bot.load_extension(ext)
            log.debug(f"Extension {ext} loaded")

        await bot.start(token)
    finally:
        await bot.close()

asyncio.run(bootstrap())

