from __future__ import annotations
from typing import TYPE_CHECKING
from .sync import CoreSync
from .help import CoreHelp

if TYPE_CHECKING:
    from ..bot import Bot


async def setup(bot: Bot):
    await bot.add_cog(CoreSync(bot))
    await bot.add_cog(CoreHelp(bot))
