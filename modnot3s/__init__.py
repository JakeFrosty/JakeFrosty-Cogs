# Copyright (c) 2021 - jojo7791
# Modified (c) 2023 - jakefrosty, psychotechv4
# Licensed under MIT

import json
from pathlib import Path

from redbot.core.bot import Red

from .core import ModNot3s

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red):
    await bot.add_cog(ModNot3s(bot))
