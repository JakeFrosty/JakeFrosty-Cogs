# Copyright (c) 2021 - jojo7791
# Modified (c) 2023 - jakefrosty, psychotechv4
# Licensed under MIT

import logging
from typing import Any, Dict, Final, List

import discord  # type:ignore
from redbot.core import Config, commands, modlog
from redbot.core.bot import Red
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import pagify
from typing import Union
from .api import NotAuthor, NoteApi, modlog_exists
from .menus import Menu, Page
from .utils import *
import traceback

log = logging.getLogger("red.JakeFrostyCogs.ModNot3s")
_config_structure: Dict[str, Dict[str, Any]] = {
    "guild": {
        "modlog_enabled": False,
        "allow_other_edits": False,
    },
    "member": {
        "notes": [],
    },
}


class ModNot3s(commands.Cog):
    """A mod note cog for moderators to add notes to users"""

    __authors__: Final[List[str]] = ["jakefrosty, psychotechv4, jojo7791"]
    __version__: Final[str] = "1.0.3"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(None, 415779962436452353, True, cog_name="ModNot3s")
        self.config.register_guild(**_config_structure["guild"])
        self.config.register_member(**_config_structure["member"])
        self.config.register_global(updated=False)
        self.api = NoteApi(self.config, self.bot)

    async def cog_load(self) -> None:
        try:
            await modlog.register_casetype("Mod Note", True, "\N{MEMO}", "Mod Note")
        except RuntimeError:
            pass

    async def cog_check(self, ctx: commands.Context) -> bool:
        return ctx.guild is not None

    def format_help_for_context(self, ctx: commands.Context) -> str:
        plural = "" if len(self.__authors__) == 1 else "s"
        return (
            f"{super().format_help_for_context(ctx)}\n"
            f"**Author{plural}:** {', '.join(self.__authors__)}\n"
            f"**Version:** `{self.__version__}`"
        )

    async def red_delete_data_for_user(self, requester, user_id: int) -> None:
        if requester != "discord_deleted_user":
            return
        all_members = await self.config.all_members()
        async for guild_id, guild_data in AsyncIter(all_members.items(), steps=100):
            if user_id in guild_data:
                await self.config.member_from_ids(guild_id, user_id).clear()

    async def red_get_data_for_user(self, *args, **kwargs) -> Dict[Any, Any]:
        return {}

    @commands.hybrid_group(name="noteset", aliases=["nset"])
    @commands.admin_or_permissions(administrator=True)
    @commands.guild_only()
    async def noteset(self, ctx: commands.Context):
        """Setup modnotes"""
        pass

    @noteset.command()
    async def usemodlog(self, ctx: commands.Context, toggle: bool):
        """Toggle whether to use the modlog or not.

        If toggled, whenever a note is created on a user it will create a case in the modlog.

        **Arguments**
            - `toggle` Whether to enable or disable the modlog logging.
        """
        if toggle and not await modlog_exists(ctx.guild):
            return await ctx.send(
                "I could not find the modlog channel. Please set one up in order to use this feature."
            )
        current = await self.config.guild(ctx.guild).modlog_enabled()
        disabled = "enabled" if toggle else "disabled"
        if current == toggle:
            return await ctx.send(f"The modlog logging is already {disabled}.")
        await ctx.send(f"Modlog logging is now {disabled}.")
        await self.config.guild(ctx.guild).modlog_enabled.set(toggle)

    @noteset.command(name="nonauthoredits", aliases=("nae",))
    async def non_author_edits(self, ctx: commands.Context, toggle: bool):
        """Allow any moderator to edit notes, regardless of who authored it
        
        **Arguments**
            - `toggle` Whether moderators other than the author can edit notes.
        """
        if toggle == await self.config.guild(ctx.guild).allow_other_edits():
            enabled = "" if toggle else "'t"
            return await ctx.send(
                f"Moderators already can{enabled} edit notes that weren't authored by them."
            )
        await self.config.guild(ctx.guild).allow_other_edits.set(toggle)
        now_no_longer = "now" if toggle else "no longer"
        await ctx.send(f"Moderators can {now_no_longer} edit notes not authored by them.")

#    @commands.group(aliases=("mnote",), invoke_without_command=True)
    @commands.hybrid_command(name="addnote")
    @commands.mod_or_permissions(administrator=True)
    @commands.guild_only()
    async def addnote(
        self, ctx: commands.Context, user: Union[discord.Member, discord.User], *, note: str  # type:ignore
    ):
        """Create a note for a user. Cannot be a bot.

        If enabled this will also log to the modlog.

        **Arguments**
            - `user` The user you want to note.
            - `note` The note to add to them.
        """
        if isinstance(user, discord.Member) and user.bot:
            return await ctx.send("You cannot use notes on bots.")
        else:
            note = f"{note}"
            await ctx.send(f"Done. I have added that as a note for {user.name}")
            await self.api.create_note(ctx.guild, user, ctx.author, note)

# Disabled for now, will be re-enabled in a future update.
# Terribly broken, and I don't have the time to fix it right now.

#    @commands.hybrid_command(name="listallnotes")
#    @commands.mod_or_permissions(administrator=True)
#    @commands.guild_only()
#    async def listallnotes(self, ctx: commands.Context):
#        """List all the members with notes in this guild"""
#        data = await self.config.all_members(ctx.guild)
#        if not data:
#            return await ctx.send("There are no notes in this guild.")
#        msg = ""
#        act = [[]] 
#        
#        for user_id, user_data in data.items():
#            user = str(ctx.guild.get_member(user_id) or user_id)
#            user_data = user_data["notes"]
#               
#            i = 0
#            noteIndex = 1
#            for note in user_data:
#                if len(act[i]) == 10:
#                    i += 1
#                    act.append([])
#                try: 
#                    time = note["time"]
#                except:
#                    time = None
#                    
#                act[i].append(
#                    [
#                        f"{str(ctx.guild.get_member(user_id) or user_id)} by {str(ctx.guild.get_member((a := note['author'])) or a)}",
#                        note["note"],
#                        time
#                    ]
#                )
#                noteIndex += 1
    
    @commands.hybrid_command(name="delnote")
    @commands.mod_or_permissions(administrator=True)
    @commands.guild_only()
    async def delnote(self, ctx: commands.Context, user: Union[discord.Member, discord.User], index: PositiveInt):
        """Remove a note from a user.

        **Arguments**
            - `user` The user to remove a note from.
            - `index` The index of the note to remove.
        """
        if isinstance(user, discord.Member) and user.bot:
            return await ctx.send("You cannot use notes on bots.")
        else:
            try:
                await self.api.remove_note(ctx.guild, index - 1, user, ctx.author)
            except NotAuthor:
                await ctx.send("You are not the author of that note.")
            except IndexError:
                await ctx.send(f"I could not find a note at index {index}.")
            else:
                await ctx.send(f"Removed a note from that user at index {index}.")    
            title = f"Notes in {ctx.guild} ({ctx.guild.id})."
            await Menu(ctx, Page(act, title, use_md=False)).start()
    
    # This is partially broken, moderators can clear notes from other moderators.
    # so I've temporarily switched it to admin only.
    @commands.hybrid_command(name="clearnotes")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def clearnotes(self, ctx: commands.Context, user: discord.Member):
        """Clear all notes from a user. This user cannot be a bot.

        **Arguments**
            - `user` The user to clear notes from.
        """
        if isinstance(user, discord.Member) and user.bot:
            return await ctx.send("You cannot use notes on bots.")
        else:
            try:
                await self.api.clear_notes(ctx.guild, user, ctx.author)
            except NotAuthor:
                await ctx.send("You are not the author of that note.")
            except IndexError:
                await ctx.send(f"I could not find a note at index {index}.")
            else:
                await ctx.send(f"Cleared all notes from that user.")

    @commands.hybrid_command(name="editnote")
    @commands.mod_or_permissions(administrator=True)
    @commands.guild_only()
    async def editnote(
        self, ctx: commands.Context, user: Union[discord.Member, discord.User], index: PositiveInt, *, note: str
    ):
        """Edit a note on a user.

        **Arguments**
            - `user` The user to edit a note on. This user cannot be a bot.
            - `index` The index of the reason to edit.
            - `note` The new note.
        """
        if isinstance(user, discord.Member) and user.bot:
            return await ctx.send("You cannot use notes on bots.")
        else:
            try:
                await self.api.edit_note(ctx.guild, index - 1, user, ctx.author, note)
            except NotAuthor:
                await ctx.send("You are not the author of that note.")
            except IndexError:
                await ctx.send(f"I could not find a note at index {index}.")
            else:
                await ctx.send(
                    f"Edited the note at index {index}."
                )  # TODO(Jojo) Maybe send the new + old note?

    @commands.hybrid_command(name="notes", aliases=("listnotes",))
    @commands.mod_or_permissions(administrator=True)
    @commands.guild_only()
    async def notes(self, ctx: commands.Context, user: Union[discord.Member, discord.User]):
        """List the notes on a certain user.

        **Arguments**
            - `user` The user to view notes of.
        """
        if isinstance(user, discord.Member) and user.bot:
            return await ctx.send("You cannot use notes on bots.")
        else:
            data = await self.config.member(user).notes()
            if not data:
                return await ctx.send("That user does not have any notes.")
            act = [[]]
            i = 0
            noteIndex = 1
            for note in data:
                if len(act[i]) == 10:
                    i += 1
                    act.append([])
                try: 
                    time = note["time"]
                except:
                    time = None
                    
                act[i].append(
                    [
                        f"{noteIndex} {ctx.guild.get_member(note['author']) or note['author']}",
                        # str(ctx.guild.get_member(note["author"]) or note["author"]),
                        note["note"],
                        time
                    ]
                )
                noteIndex += 1
            # msg = "# Moderator\tNote\n"
            # msg += "\n".join(f"{num}. {mod}\t\t{note}" for num, (mod, note) in enumerate(act, 1))
            await Menu(ctx, Page(act, f"Notes on {str(user)} ({user.id})")).start()