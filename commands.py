class Commands(object):
    """
    A class handling parsing of commands, mentions (members/roles), and
    performing various actions such as XP management, prefix changes,
    and a 'rickroll' feature that targets specific members/roles.
    """

    def __init__(self, discord, xp_manager):
        """
        Initialize the Commands object with references to:
          - discord: The discord.py module (for Embed, Member, etc.)
          - xp_manager: A custom XP Manager for handling XP logic
        """
        self.discord = discord
        self.xp_manager = xp_manager
        self.database = xp_manager.database

    # Class-wide properties used across methods
    message = None         # The current message being processed
    command = ""           # The raw command string (excluding prefix)
    interpreter = []       # Parsed command tokens
    prefix = ""            # The prefix for this guild
    index = 0              # Index for iterating through message content
    mention = 0            # Counter of how many members have been mentioned so far
    role_mention = 0       # Counter of how many roles have been mentioned so far
    mentions = {}          # A dict mapping mention strings -> Member/Role objects
    needed = {}            # A dict used for handling positional/keyword arguments

    def check_mention(self, before: str, after: str):
        """
        Looks for a substring starting with 'before' (e.g. '<@!') and ending with 'after' (e.g. '>'),
        at the current self.index in the message content. Returns the mention string if valid, else None.
        
        This function supports variable-length numeric IDs (e.g. <@!123456>, <@!123456789012345678>).
        """
        content = self.message.content
        start_index = self.index

        # Does the content at position start_index begin with 'before'?
        if content.startswith(before, start_index):
            # Find the position of 'after' (e.g. '>') after the opening tag
            close_index = content.find(after, start_index + len(before))
            if close_index != -1:
                # Extract the full mention substring, e.g. <@!1234567890>
                substring = content[start_index: close_index + len(after)]
                # The part inside might look like "1234567890" if substring is <@!1234567890>
                inside = substring[len(before):-len(after)]
                # Check if inside is purely numeric (the ID)
                if inside.isnumeric():
                    return substring
        return None

    def check_member(self):
        """
        Checks the message content (at self.index) for a valid member mention.
        It tries <@!ID> first, then <@ID> if the first fails.
        If found, updates self.mentions mapping the mention string -> discord.Member.
        """
        mention = self.check_mention("<@!", ">")
        if mention is None:
            mention = self.check_mention("<@", ">")
            # Ensure it's not actually a role mention like <@&...>
            if mention and mention.startswith("<@&"):
                mention = None

        # If we successfully found a mention and we still have unprocessed message.mentions
        if mention is not None and self.mention < len(self.message.mentions):
            self.mentions.update({mention: self.message.mentions[self.mention]})
            self.mention += 1

    def check_role(self):
        """
        Checks the message content (at self.index) for a valid role mention <@&ID>.
        If found, updates self.mentions mapping the mention string -> discord.Role.
        """
        mention = self.check_mention("<@&", ">")
        if mention is not None and self.role_mention < len(self.message.role_mentions):
            self.mentions.update({mention: self.message.role_mentions[self.role_mention]})
            self.role_mention += 1

    def format_mentions(self, message):
        """
        Iterates over every character in message.content, calling check_member() and check_role().
        This populates self.mentions with all user and role mentions it finds.
        """
        self.index = 0
        self.mention = 0
        self.role_mention = 0
        self.mentions = {}
        while self.index < len(message.content):
            self.check_member()
            self.check_role()
            self.index += 1

    def separate(self, char):
        """
        Helper function used during tokenization (format_text) to separate tokens by specific characters (e.g. '=' or '+').
        If found, split at that point and insert them as separate tokens in self.interpreter.
        """
        if self.index < len(self.command):
            if self.command[self.index] == char:
                self.interpreter += self.command[:self.index].split() + [char]
                self.command = self.command[self.index + 1:]

    def format_text(self):
        """
        Tokenizes the raw command string (self.command) into separate elements in self.interpreter.
        Splits on whitespace normally, but also handles quoted strings and separators like '=' and '+'.
        """
        str_type = None
        self.index = 0
        while self.index < len(self.command):
            if str_type is None:
                # Check if we are starting a quoted string
                if self.command[self.index] in ["'", '"']:
                    str_type = self.command[self.index]
                    self.interpreter += self.command[:self.index].split()
                    self.command = self.command[self.index + 1:]
                else:
                    # Check for '=' or '+'
                    self.separate("=")
                    self.separate("+")
            else:
                # We are inside a quoted string; check if we've reached the closing quote
                if self.command[self.index] == str_type:
                    str_type = None
                    self.interpreter.append(self.command[:self.index])
                    self.command = self.command[self.index + 1:]
            self.index += 1
        self.interpreter += self.command.split()

    def get_member_by_mention(self, mention):
        """
        Retrieves the object stored in self.mentions for a given mention string.
        This could be a discord.Member or a discord.Role, depending on which function stored it.
        """
        return self.mentions.get(mention)

    def format_lists(self):
        """
        Processes the tokens in self.interpreter.
        If it finds a '+' between tokens, it merges them into a list (e.g. [token1, token2]).
        """
        self.index = 0
        while self.index < len(self.interpreter):
            if self.interpreter[self.index] == "+":
                if 0 < self.index:
                    if isinstance(self.interpreter[self.index - 1], list):
                        self.interpreter[self.index - 1].append(self.interpreter[self.index + 1])
                        self.interpreter = self.interpreter[:self.index] + self.interpreter[self.index + 2:]
                    else:
                        self.interpreter = (
                            self.interpreter[:self.index - 1]
                            + [[self.interpreter[self.index - 1], self.interpreter[self.index + 1]]]
                            + self.interpreter[self.index + 2:]
                        )
            self.index += 1

    def format_arguments(self):
        """
        Processes tokens again, this time looking for '='.
        If it finds 'key = value', it stores them as a dict {key: value} in self.interpreter.
        Repeated keys get merged into an existing dictionary if present.
        """
        self.index = 0
        while self.index < len(self.interpreter):
            if self.interpreter[self.index] == "=":
                if 0 < self.index:
                    if self.index > 1:
                        # If there's a dict before the key, merge
                        if isinstance(self.interpreter[self.index - 2], dict):
                            self.interpreter[self.index - 2].update({
                                self.interpreter[self.index - 1]: self.interpreter[self.index + 1]
                            })
                            self.interpreter = (
                                self.interpreter[:self.index - 1] + self.interpreter[self.index + 2:]
                            )
                            self.index -= 2
                    # If there's no dict before the key, create a new dict
                    if self.interpreter[self.index] == "=":
                        self.interpreter = (
                            self.interpreter[:self.index - 1]
                            + [{self.interpreter[self.index - 1]: self.interpreter[self.index + 1]}]
                            + self.interpreter[self.index + 2:]
                        )
                        self.index -= 1
            self.index += 1

    def format_code(self, message):
        """
        Orchestrates the multi-step parsing of the command:
          1. format_mentions -> capture mentions
          2. format_text -> tokenize text
          3. format_lists -> merge tokens with '+'
          4. format_arguments -> merge tokens with '=' into dicts
        """
        self.format_mentions(message)
        self.format_text()
        self.format_lists()
        self.format_arguments()

    def check(self, argument):
        """
        Checks if the first token in self.interpreter matches `argument`.
        If it does, remove it from self.interpreter and return True, else False.
        """
        ret = False
        if self.interpreter:
            if self.interpreter[0] == argument:
                self.interpreter = self.interpreter[1:]
                ret = True
        return ret

    def assign_keyword_arguments(self, arguments):
        """
        Merges any keyword arguments (dict) into self.needed for matching named arguments.
        """
        for key in self.needed.keys():
            if key in arguments.keys():
                self.needed[key] = arguments[key]

    def assign_positional_arguments(self, arguments):
        """
        Assigns positional arguments (items in a list) in order to self.needed keys,
        but only if a needed key is still None.
        """
        for self.index, value in enumerate(arguments):
            if self.index < len(self.needed):
                key = list(self.needed.keys())[self.index]
                if self.needed[key] is None:
                    self.needed[key] = value

    def assign_default_arguments(self, arguments):
        """
        If a needed key is still None but has a default provided in 'arguments',
        set it to that default.
        """
        for key in self.needed.keys():
            if key in arguments.keys():
                if self.needed[key] is None:
                    self.needed[key] = arguments[key]

    def assign_arguments(self, needed: list = [], default: dict = {}):
        """
        Splits self.interpreter into positional arguments and keyword arguments (dicts).
        Then assigns them to the keys in 'needed' (with possible defaults in 'default').

        Returns True if all required arguments are assigned; otherwise False.
        """
        self.needed = {key: None for key in needed}
        keyword = {}
        positional = []

        for argument in self.interpreter:
            if isinstance(argument, dict):
                keyword.update(argument)
            else:
                positional.append(argument)

        self.assign_keyword_arguments(keyword)
        self.assign_positional_arguments(positional)
        self.assign_default_arguments(default)

        # If any needed value is still None, return False
        return not any([value is None for value in self.needed.values()])

    def check_and_assign(self, argument: str, needed: list = [], default: dict = {}):
        """
        Shorthand to check if the first token in interpreter matches `argument`
        and, if so, attempt to assign the needed arguments. Returns True on success.
        """
        if self.check(argument):
            return self.assign_arguments(needed, default)
        else:
            return False

    def reversed_split(self, str_list):
        """
        Joins a list of strings into a single spaced string.
        If the list is empty, returns an empty string. If not, returns
        them joined by spaces. Example: ["123", "456"] -> "123 456".
        """
        ret = ""
        for obj in str_list:
            if isinstance(obj, str):
                ret += obj + " "
        return ret[:-1] if ret else ret

    async def update_rickroll_targets(self, mode):
        """
        Called when adding or removing rickroll targets (members or roles).
        Pulls IDs from self.needed['targets'], which may be a single mention or a list of mentions.
        
        Depending on 'mode':
          - "append": adds them to the DB
          - "remove": removes them from the DB
        """
        targets = self.needed["targets"]
        if not isinstance(targets, list):
            targets = [targets]

        # Separate member vs. role mentions by prefix
        target_member_ids = [
            str(self.get_member_by_mention(m).id)
            for m in targets
            if (m.startswith("<@!") or (m.startswith("<@") and not m.startswith("<@&")))
        ]
        target_role_ids = [
            str(self.get_member_by_mention(m).id)
            for m in targets
            if m.startswith("<@&")
        ]

        rickroll_members = self.database.get_from_guild(self.message.guild.id, "rickroll_members").split()
        rickroll_roles = self.database.get_from_guild(self.message.guild.id, "rickroll_roles").split()

        # Add or remove targets accordingly
        if mode == "append":
            for mid in target_member_ids:
                if mid not in rickroll_members:
                    rickroll_members.append(mid)
            for rid in target_role_ids:
                if rid not in rickroll_roles:
                    rickroll_roles.append(rid)
        elif mode == "remove":
            rickroll_members = [mid for mid in rickroll_members if mid not in target_member_ids]
            rickroll_roles = [rid for rid in rickroll_roles if rid not in target_role_ids]

        # Update database fields
        self.database.change_in_guild(self.message.guild.id, "rickroll_members", self.reversed_split(rickroll_members))
        self.database.change_in_guild(self.message.guild.id, "rickroll_roles", self.reversed_split(rickroll_roles))

        # Send a generic reply
        reply = self.GuildEmbed("Targets updated.", "")
        await self.message.channel.send(embed=reply)

    def StandardEmbed(self, title, description):
        """
        Returns a base embed with a fixed color, title, description, and a footer referencing the message author.
        """
        embed = self.discord.Embed(title=title, description=description, color=0x0FFFFF)
        embed.set_footer(text="Requested by " + self.message.author.name, icon_url=self.message.author.avatar_url)
        return embed

    def SyntaxErrorEmbed(self):
        """
        Returns a generic embed used when there's a syntax error in parsing arguments.
        """
        return self.StandardEmbed("Error", "Syntax error")

    def GuildEmbed(self, title, description):
        """
        Returns an embed with the server (guild) icon as a thumbnail.
        """
        embed = self.StandardEmbed(title, description)
        embed.set_thumbnail(url=self.message.guild.icon_url)
        return embed

    def MemberEmbed(self, member, title, description):
        """
        Returns an embed with the specified member's avatar as a thumbnail.
        """
        embed = self.StandardEmbed(title, description)
        embed.set_thumbnail(url=member.avatar_url)
        return embed

    def PermissionDeniedEmbed(self, member):
        """
        Returns a generic embed used when a member tries to run a command they don't have permission for.
        """
        return self.MemberEmbed(member, "Missing Permissions", "You don't have the permission to use this.")

    def MenuHelpEmbed(self, path, menus, admin_menus):
        """
        Returns an embed listing possible menus (subcommands).
        If the user is an administrator, admin_menus are also added.
        """
        embed = self.StandardEmbed("Help", f"for command `{self.prefix}{path}`")
        menu_list = ""
        if self.message.author.guild_permissions.administrator:
            menus += admin_menus
        for menu in menus:
            menu_list += f"- {menu}\n"
        embed.add_field(name="Menus", value=menu_list)
        return embed

    def CommandHelpEmbed(self, path, description, arguments: dict):
        """
        Returns an embed describing a specific command's usage: its description and arguments.
        """
        embed = self.StandardEmbed("Help", f"for command `{self.prefix}{path}`")
        embed.add_field(name="Description", value=description)
        for key in arguments.keys():
            embed.add_field(name=key, value=arguments[key])
        return embed

    async def is_admin(self, member):
        """
        Checks if the given member has administrator permissions in the guild.
        If not, sends a PermissionDeniedEmbed.
        """
        if member.guild_permissions.administrator:
            return True
        else:
            await self.message.channel.send(embed=self.PermissionDeniedEmbed(member))

    async def run(self, message):
        """
        The main entry point for this command system. 
        Called whenever the bot sees a message. If it starts with the guild prefix, 
        we parse the command and execute the corresponding actions.
        """
        self.message = message
        self.command = message.content
        self.prefix = self.database.get_from_guild(message.guild.id, "prefix")

        # Only proceed if the message actually starts with the prefix
        if self.command.startswith(self.prefix):
            self.command = self.command[len(self.prefix):]
            self.interpreter = []

            # Parse mentions, text, lists, and argument assignments
            self.format_code(message)

            # A nested "menu" system of possible commands
            menu_system = {
                "": {
                    "xp": ({
                        "add": [
                            "Adds xp to a given member.",
                            {"member": "The mention of the member you want to add xp to.", "amount": "The amount of xp you want to add."}
                        ],
                        "set": [
                            "Sets xp of a given member.",
                            {"member": "The mention of the member you want to set the xp to.", "amount": "The new xp value."}
                        ]
                    },),
                    "prefix": ([
                        "Changes the prefix.",
                        {"new": "The new prefix."}
                    ],),
                    "rickroll": ({
                        "add": [
                            "Adds a member/role that will be rickrolled in the future, if it joins a call.",
                            {"target": "The mention of the member/role you want to rickroll."}
                        ],
                        "remove": [
                            "Removes a member/role, so won't be rickrolled anymore.",
                            {"target": "The mention of the member/role you want to remove."}
                        ],
                        "get": [
                            "Returns the rickroll targets.",
                            {}
                        ]
                    },),
                    "autoroles": {
                        "set": ([
                            "Sets the automatic roles.",
                            {"data": "String with minimal xp and role mention in pairs: 'xp1 @Role xp2 @Role ...'."}
                        ],),
                        "get": [
                            "Returns the automatic roles.",
                            {}
                        ]
                    },
                    "stats": [
                        "Returns the stats of a given member.",
                        {"member": "The mention of the member (you by default)."}
                    ],
                    "ranklist": [
                        "Returns a ranklist with all xp of this guild's members.",
                        {}
                    ]
                }
            }

            # "help" command to navigate the menu system
            if self.check("help"):
                interpreter = [""] + self.interpreter
                path = ""
                fine = True
                while interpreter and fine:
                    key = interpreter[0]
                    interpreter = interpreter[1:]
                    fine = key in menu_system.keys()
                    if fine:
                        path += " " + key
                        menu_system = menu_system[key]
                        if isinstance(menu_system, tuple):
                            # If we encounter a tuple, it's an admin-only branch
                            fine = message.author.guild_permissions.administrator
                            menu_system = menu_system[0]
                path = path.strip()
                if path:
                    path = path[1:] if len(path) > 1 else path

                if isinstance(menu_system, dict):
                    # Show submenus
                    menus = []
                    admin_menus = []
                    for k in menu_system.keys():
                        if isinstance(menu_system[k], tuple):
                            admin_menus.append(k)
                        else:
                            menus.append(k)
                    await message.channel.send(embed=self.MenuHelpEmbed(path, menus, admin_menus))
                elif isinstance(menu_system, list):
                    # It's a command, show details
                    description, arguments = menu_system
                    await message.channel.send(embed=self.CommandHelpEmbed(path, description, arguments))

            # Stats command
            elif self.check_and_assign("stats", ["member"], {"member": message.author}):
                mention = self.needed["member"]
                if isinstance(mention, self.discord.Member):
                    member = mention
                else:
                    member = self.get_member_by_mention(mention)
                if member is not None:
                    reply = self.MemberEmbed(member, "Stats", "for " + member.name)
                    xp = self.xp_manager.calculate_xp(member)
                    reply.add_field(name="XP", value=str(xp))
                    await message.channel.send(embed=reply)

            # Ranklist command
            elif self.check_and_assign("ranklist"):
                members_data = self.database.get_from_guild(message.guild.id, "members")
                member_ids = [int(mid) for mid in list(members_data.keys())]
                xp_to_members = {}
                for mid in member_ids:
                    member = message.guild.get_member(mid)
                    if member is not None:
                        xp_val = self.xp_manager.calculate_xp(member)
                        if xp_val != 0:
                            xp_to_members.setdefault(xp_val, []).append(member)
                xps = sorted(xp_to_members.keys(), reverse=True)
                reply = self.GuildEmbed("Ranklist", "Here is the server-wide ranklist:")
                reply.add_field(name="Σ", value=str(sum(xps)) if xps else "0", inline=False)
                rank = 1
                for xp_val in xps:
                    for mem in xp_to_members[xp_val]:
                        reply.add_field(name=f"{rank} - {mem.name}", value=str(xp_val), inline=False)
                    rank += len(xp_to_members[xp_val])
                await message.channel.send(embed=reply)

            # Autoroles command
            elif self.check("autoroles"):
                try:
                    if self.check_and_assign("set", ["data"]):
                        data = self.needed["data"]
                        splitted = data.split()
                        min_role_xp = {}
                        if len(splitted) > 1:
                            # Build a dict from pairs: xp, mention
                            # e.g. "100 @Role 200 @AnotherRole"
                            for i in range(0, len(splitted), 2):
                                xp_val = splitted[i]
                                role_mention = splitted[i + 1]
                                if xp_val.isnumeric():
                                    min_role_xp[role_mention] = int(xp_val)

                        all_roles = await message.guild.fetch_roles()
                        roles = {}
                        # Map the mention -> role.id, keyed by the xp
                        for role in all_roles:
                            if role.mention in min_role_xp.keys():
                                xp_key = min_role_xp[role.mention]
                                roles[str(xp_key)] = role.id

                        self.database.change_in_guild(message.guild.id, "roles", roles)
                        reply = self.GuildEmbed("Autoroles set.", "The autoroles have been set successfully.")
                        await message.channel.send(embed=reply)

                    elif self.check_and_assign("get"):
                        roles = self.database.get_from_guild(message.guild.id, "roles")
                        min_xp_list = sorted((int(x) for x in roles.keys()), reverse=True)
                        reply = self.GuildEmbed("Autoroles", "The automatic roles for this server.")
                        for min_xp in min_xp_list:
                            rid = roles[str(min_xp)]
                            r = message.guild.get_role(rid)
                            reply.add_field(name=str(min_xp), value=r.name, inline=False)
                        await message.channel.send(embed=reply)
                except:
                    await message.channel.send(embed=self.SyntaxErrorEmbed())

            # XP commands
            elif self.check("xp"):
                if await self.is_admin(message.author):
                    if self.check_and_assign("add", ["member", "amount"]):
                        member_mention = self.needed["member"]
                        member = self.get_member_by_mention(member_mention)
                        if member is not None:
                            amount = self.needed["amount"]
                            old_xp = int(self.database.get_from_member(member, "xp"))
                            old_xp_str = str(self.xp_manager.calculate_xp(member))

                            # Convert amount to float (could be negative)
                            if amount.isnumeric():
                                amount = float(amount)
                            elif amount.startswith("-") and amount[1:].isnumeric():
                                amount = float(amount)

                            if isinstance(amount, float):
                                if old_xp + amount >= 0:
                                    self.database.change_in_member(member, "xp", old_xp + amount)
                                    new_xp = self.xp_manager.calculate_xp(member)
                                    reply = self.MemberEmbed(
                                        member,
                                        "XP changed.",
                                        f"Changed xp of {member.mention} from {old_xp_str} to {new_xp}."
                                    )
                                    await message.channel.send(embed=reply)

                    elif self.check_and_assign("set", ["member", "amount"]):
                        member_mention = self.needed["member"]
                        member = self.get_member_by_mention(member_mention)
                        if member is not None:
                            amount = self.needed["amount"]
                            if amount.isnumeric():
                                xp_val = float(amount)
                                if xp_val >= 0:
                                    old_xp = self.xp_manager.calculate_xp(member)
                                    self.database.change_in_member(member, "xp", xp_val)
                                    new_xp = self.xp_manager.calculate_xp(member)
                                    reply = self.MemberEmbed(
                                        member,
                                        "XP changed.",
                                        f"Changed xp of {member.mention} from {old_xp} to {new_xp}."
                                    )
                                    await message.channel.send(embed=reply)

            # Prefix change
            elif self.check_and_assign("prefix", ["new"]):
                if await self.is_admin(message.author):
                    new = self.needed["new"]
                    if isinstance(new, str):
                        self.database.change_in_guild(message.guild.id, "prefix", new)
                        reply = self.GuildEmbed("Prefix changed.", f"{self.prefix} --> {new}")
                        await message.channel.send(embed=reply)

            # Rickroll commands
            elif self.check("rickroll"):
                # Show current targets
                if self.check_and_assign("get"):
                    rickroll_members = self.database.get_from_guild(message.guild.id, "rickroll_members").split()
                    rickroll_roles = self.database.get_from_guild(message.guild.id, "rickroll_roles").split()

                    role_names = ""
                    member_names = ""
                    for rid in rickroll_roles:
                        role_obj = message.guild.get_role(int(rid))
                        if role_obj is not None:
                            role_names += role_obj.name + "\n"
                    for mid in rickroll_members:
                        mem_obj = message.guild.get_member(int(mid))
                        if mem_obj is not None:
                            member_names += mem_obj.name + "\n"

                    if not role_names:
                        role_names = "-"
                    if not member_names:
                        member_names = "-"

                    reply = self.GuildEmbed("Targets", "Here are the rickroll targets:")
                    reply.add_field(name="Roles", value=role_names)
                    reply.add_field(name="Members", value=member_names)
                    await message.channel.send(embed=reply)

                elif await self.is_admin(message.author):
                    # Add
                    if self.check_and_assign("add", ["targets"]):
                        await self.update_rickroll_targets("append")

                    # Remove
                    elif self.check_and_assign("remove", ["targets"]):
                        await self.update_rickroll_targets("remove")

            # Cleanup: delete the user's command message (if desired)
            await message.delete()
