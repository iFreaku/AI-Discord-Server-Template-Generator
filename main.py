import discord
from discord import app_commands
import json
from together import Together
import secrets
from pymongo import MongoClient
from flask import Flask, render_template
import os
import threading

app = Flask(__name__, template_folder='templates')

@app.route('/')
def home():
    return "Bot is alive!"

@app.route('/template/<template_id>')
def show_template(template_id):
    template_data = templates_collection.find_one({"id": template_id})
    if not template_data:
        return "Template not found", 404
    return render_template('template.html', template=template_data["template"], template_id=template_id)

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 8080)))

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

mongo_client = MongoClient(os.getenv("MONGOURI"))
db = mongo_client["discord_templates"]
templates_collection = db["templates"]

together_client = Together(api_key=os.getenv("APIKEY"))

def generate_hex_id():
    return secrets.token_hex(5)

def validate_template(template):
    valid_types = {"category", "text-channel", "voice-channel", "forum-channel", "announcement-channel", "stage-channel"}
    for item in template:
        if item["type"] not in valid_types:
            return False
        if item["type"] == "category" and "channels" in item:
            for channel in item["channels"]:
                if channel["type"] not in valid_types - {"category"}:
                    return False
                if "name" not in channel or not isinstance(channel["name"], str):
                    return False
                if " " in channel["name"]:
                    return False
                if channel["type"] not in {"announcement-channel", "stage-channel"} and "private" not in channel:
                    return False
        if "name" not in item or not isinstance(item["name"], str):
            return False
        if " " in item["name"]:
            return False
        if item["type"] != "category" and item["type"] not in {"announcement-channel", "stage-channel"} and "private" not in item:
            return False
    return True

@tree.command(name="generate", description="Generate a server template using AI")
@app_commands.describe(prompt="Describe the server template")
async def generate_template(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()
    system_prompt = """
    You are a professional discord server template generator,
    You generate categories and channels
    You respond in JSON format, no backticks and no system text.
    Follow this structure: {'template': []}.
    Use types: category, text-channel, voice-channel, forum-channel, announcement-channel, stage-channel.
    Replace spaces in names with '-'.
    You can use sepcial characters for designing the names of the categoreis and channels only when said by the user!
    You can use emojis for designing the names of the categoreis and channels only when said by the user!
    List of some special characters to use when creating aesthetic or grudge themed servers (You can even combine different characters, eg: 「★, and no need to give space/hyphen after special characters or emojis only between words! ):
    ୨୧ 𖧧 ﹕ ﹌﹫ ꒰ ꒱𑁯𓂅 𓏲 ⌕ ┆∿ ・. ˚ ꒷♡̷̷ ˖ ࣪ ˒ ꗃ ⟭⟬ 𓈈 ‹𝟹 ⌗ ┊: 𓄹 ᕬ 🗒 ﹌ ꗃ 𓂃 𓍯 ꒦꒷ ⿻ 𓏲ּ ֶָ֢ ∞  ⎙ 𓆤 𓂃୭̥ ᘏ ⑅ ᘏ ♡⊹ ° . ˚  · ° . ♡ ⊹ ◌ ❛❜ ⋆ ♥︎ ꧕  ⪧ ꕤ. ⸾ ⸽  | ┊ ✉ ♡ ⊹ ★꒷ ᵎᵎ ₊ ◌𑀈. ♡ - ̗̀໒ ⋮ ➮ ⨾ ்⋆ ⬚ (˶ᵔᴗᵔ˶ ˀˀ ୨୧ ❛ ❜ ʚ ɞ ✦ ♥︎ ∞ ☾ ☽ ♫ ♪ ✞ シ ت ♡ ఌ  ᴥ ☻ 𑁍  ★ ☆ ✰ 𝟭 𝟮 𝟯 𝟰 𝟱 𝟲 𝟳 𝟴 𝟵 𝟬 . ₊ ༝ ･ ˖ ₊ ˚ 。 . ⋆    ༻ ༺ . ⸼۰ ۪۪۫۫ = ،، ⏧ ·₊̣̇. ⊱ ⊰ ∝ 组 ೄ ಇ බ ※ ⿻ ۬ ⪧ ໒ ː ͡ ︶ ՞ 〃  ᵎ ⏟ ⏝ ꦿ ۫։ຼ ೃ ೀ ෞ 。ꞈ ￤ ゛ރ ▿ ▾ ⌀ ଽ  ⌔  〻〼
    ﹒ʬʬ﹒⪩⪨﹒⟡﹒ᐢ..ᐢ﹒◖﹒⇅﹒○﹒✿﹒⊹﹒∇﹒✸﹒⟢﹒❀﹒ᵔᴗᵔ﹒♡﹒〇﹒ıllı﹒ᶻz﹒⊂⊃﹒␥﹒⿸﹒ꔠ﹒✶﹒◍﹒▿﹒⤸﹒⬚﹒៶៸﹒△﹒→﹒✶﹒（）﹒▥﹒▤﹒▦﹒▧﹒▨﹒▩﹒░﹒▒﹒▓﹒⿴﹒◫﹒⬚﹒▣﹒≧≦﹒ㄑ﹒⎙﹒➜﹒★﹒⨳﹒✿﹒❀﹒✶﹒✸﹕☆﹒◐﹒◉ ﹒◖◗﹒▽﹒ᶻz﹒‹𝟹﹒♡﹒ᐢ..ᐢ﹒﹫﹒⿴﹒→﹒☓﹕ᵔᴗᵔ﹒⺌﹒⪩⪨﹒◎﹒⊹﹒ᶻ﹕→ ．(＞。☆)﹔⇆﹒ꜛ﹒░﹒❥﹒？﹒！﹒◍﹒﹏﹒✦﹒⟡﹒＞＜﹒◌﹒⿴﹒✧﹒𖥔﹒%﹒﹙﹚﹒◜◡◝﹒ꜝꜝ﹒⟡﹒⪩⪨﹒☓﹒⬦﹒✦﹒◈﹒✶﹒⬙﹒⟡﹒⇆﹒♡﹒﹢﹒ᶻ﹒✹﹒﹢﹒✶﹑〇﹐罒﹢♡﹒⇆﹑⬚﹐ᶻ﹒❀﹐✶﹒▹﹒◖﹒✩﹒∇﹒▨﹐◌﹐❀﹒⿴﹒✿﹢﹐░﹒ᶻz﹐☆﹒⊂⊃﹑ⵌ﹒▦﹒✿﹒⺌﹒◂﹒⿴﹒❰❰﹒♡﹒ᶻz﹒❥﹒⩇﹒⊞﹐ʬʬ﹒♢﹐ᐢ..ᐢ﹐✩﹒ᶻz﹒❥﹒⟡﹒✷﹒✕﹐〇﹐✿﹒Ꜣ﹒⟡﹒˃̵ᴗ˂̵﹒♡﹐≋﹒⊂⊃﹒ᐢᗜᐢ﹒❀﹒﹢﹒⇵﹒⪨﹕↺﹐✿﹒Ꜣ﹒✶﹐≋﹒⇆﹐ʬʬ﹒﹗﹐➜﹒⬦﹕ᶻz﹒✦﹒﹢﹒▢﹒░﹒⭔﹒ʬʬ﹒✿﹒☰﹐◖◗﹒？﹒✶﹒﹏﹒ꕀ﹑ᵔᴗᵔ﹒ᗢ﹒✿﹐⊂⊃﹒ᐢᗜᐢ﹒ꕀ﹐リ﹐口﹐ꕀ﹒（｀δ´）﹒口，✿﹐⊂⊃﹒ᐢᗜᐢ﹒░﹒𖦹﹐゛✿﹑（｀δ´）﹒イ。ꕀ﹑リ﹐⊂⊃﹒ꔠ﹒口﹐･ᴗ･﹒░﹑リ﹒◐﹐、﹕✧﹒✶﹔？﹐ʬʬ﹒▹﹒❀﹒⭔﹒▿﹒⺡﹒✿﹒﹢﹒░﹑⬦﹒૪ ﹒〹﹒罒﹒ᶻz﹒◎﹐ꕀ﹒◖◗﹒⺌﹒〣﹒ᗢ﹒⺌﹒⿸﹑ꔠ﹒❀﹒➜﹒▦﹒◐﹒✷﹒◉﹒⿴﹒⿻﹒✦﹒★﹒☆﹒ıllı﹢☆﹒❀﹕▧﹒⟡﹒★﹕ıllı﹒▒﹒◎﹐☆﹒ꕀ﹐➜﹒⪩﹒〇﹐➜﹒★﹕◐﹒％﹕▧﹒⊂⊃﹒♡﹒ꕀ﹒ᶻz﹒₊ˎ✧﹒⪩﹒˃ᴗ˂﹕˃ᗜ˂﹕⿴﹒ᶻz﹒☆﹔⿴﹒✶﹒ᵔᴗᵔ﹒➜﹒⭔﹕⪩⪨﹢◒﹒◎﹒✿﹒⊂⊃﹔♡﹒◍﹒✦﹒⪩⪨﹒▧﹒⟡﹕➜﹐▦﹐✦﹒✶﹐﹢﹒ㄑ﹕ꕀ﹒＞＜﹐ꔠ﹐✿﹐×﹐丶﹐＞︿﹒リ﹕﹢﹐﹔★﹒ᶻz﹒⿴﹒⭔﹒✿﹒⊹﹒⭔﹒⨯﹒➜﹒★﹒◞﹒◟◝﹒◜﹒﹪﹒→﹐ıllı﹒★﹒✦﹒⌕﹒⌗﹒✿﹒⊹﹒✸﹒❍﹒⭓﹒◒﹒﹏﹒₊﹒▹﹒ᶻz﹒％﹒◖﹒░﹒ʬʬ﹒⿴﹒⫘﹒◎﹒⨳﹒⌕﹕★﹒☆﹒⌗﹐﹪﹐⌯﹐﹟﹐◐﹒▒﹒◎﹒⇆﹒☆﹒❀﹒☆﹒ıllı﹒↺﹒◍﹒✶﹒ᵔᴗᵔ﹒░﹒⇵﹒▧﹒◍﹒♡﹕❀﹑⿸﹕▞﹒✿﹒╰﹒░﹐◎﹒♡﹒◜ᴗ◝﹒˃ᴗ˂ ♡﹐﹅﹒✿﹒⊞﹒ıllı﹒♡﹒⊞﹕▞﹒✿﹒❀﹒⌕﹒⿸﹒✶﹒❀﹒✷﹒✸﹒▒﹒ᶻz﹒✿﹐♡﹐❀﹒░﹒⇵﹒▨﹕◍﹒♡﹒⌕﹒˃̵ᴗ˂̵﹑♡﹒✿﹒◍﹒⊞﹒∇﹒✶﹒ᵔᴗᵔ﹒◎﹒⇆﹒☆﹒@﹒˘ᗜ˘﹒☆﹔⿴﹒⪩﹐ᶻz﹒➜﹒⪩﹔◖﹐❀﹕⿸﹔﹢﹑ᐢᗜᐢ﹒⊂⊃﹑✿﹒◎﹒イ﹐ꕀ﹒˃̵ᴗ˂̵﹒✶﹒ꕀ﹒▦﹐⊂⊃﹒⇆﹒☆﹒⬚﹒❀﹕➜﹒⪩﹒ᗢ﹒◍﹒⊞﹒∇﹒✶﹒ᵔᴗᵔ﹒◎﹒ᶻz﹒⪨﹒✶﹑✹﹒⪩。ꕀ﹒✿﹒リ﹒⊞﹒⟡﹒⿴﹒☓﹐⊂⊃﹒➜﹒⟡﹒⪩⪨﹒･ᴗ･﹒ꕀ﹒ᶻz﹒✿﹒◎﹒☓﹒☆﹔リ﹒˃̵ᴗ˂̵﹒✶﹑ꕀ﹒▦﹒リ﹐⇆﹒☆﹒⬚﹒❀﹕➜﹒⪩﹒〇﹒◍﹒⊞﹒∇﹒✶﹒ᵔᴗᵔ﹒◎﹒ᶻz﹒⪨﹒✶﹑✹﹒⪩﹒ꕀ﹒✿﹔➜﹐﹏﹐★☆﹒┆︎﹒⩇﹒✿﹔✸﹕♡﹐◌﹒❥﹐％﹑〹．ʬʬ﹕੭﹐♢﹒口﹒⇣⇡﹒☆﹔⌗﹒⪩﹐ᶻ﹒➜﹒⪩﹔◖﹐❀﹕⿸﹑ᐢᗜᐢ﹒⊂⊃﹑✿﹒！﹒◎﹒リ﹐ꔠ﹐✿﹑∇﹒イ﹐ꕀ﹒˃̵ᴗ˂̵﹒✶﹑﹒ꕀ﹒▦﹒⊂⊃﹒⇆﹒☆﹒⬚﹒❀﹕➜﹒⪩﹒⩇﹕✿﹒ʬʬ﹕口﹐〇﹒◍﹒⊞﹒∇﹒✶﹒ᵔᴗᵔ﹒◎﹒ᶻz﹒⪨﹒✶﹑✹﹒⪩﹐ꕀ﹒✿﹒⊞﹒⟡﹒⿸﹑␥﹒♡﹕リ﹒☓﹐⊂⊃﹒➜﹒⟡﹒⪩⪨﹒･ᴗ･﹒ꕀ﹒ᶻz﹒✿﹒☓﹒✩﹒⊞﹕❀﹑◌﹒⊞﹒✸﹕⌗﹕★﹒ᶻz﹒✦﹒★☆﹒ıllı﹢☆﹕❀﹒▧﹒⟡﹒★﹕ıllı﹐▒﹒◎﹐☆﹒ꕀ﹔➜﹒⪩﹒〇﹐➜﹒★﹕◐﹒％﹐⊂⊃﹒♡﹒ꕀ﹒ᶻz﹒✧﹒˃̵ᴗ˂̵﹕˃ᗜ˂﹒ꕀ﹒ᶻz﹒☆﹔⿴﹒✶﹒ᵔᴗᵔ﹒➜﹒⭔﹕⪩⪨﹐﹢﹐◒﹒⊂⊃﹔♡﹒◍﹒✦﹒⪩⪨﹒▧﹒⟡﹕➜﹐▦﹒✦﹒✶﹐ㄑ﹕ꕀ﹒＞＜﹐ꔠ﹑ꕤ﹒░﹒◖﹒⟡﹒❀﹒→﹒⿴﹒⿻﹒⊞﹒♡﹒ᵔᴗᵔ﹒︴﹒✶﹒⭔﹐𓆩♡𓆪﹒リ﹒Ꮺ﹒キ﹒ꗃ﹒⿶﹒⌓﹒〹﹒⧅﹒◆﹒▽﹒ᐢ..ᐢ﹒⬙﹒⎙﹒◈﹒▣﹒ᶻz﹒⟢﹒ʬʬ﹒⊹﹒✷﹒◉﹒⿸﹒✶﹒❀﹒✷﹒⿻﹒⌇﹒ᵔᴗᵔ﹒◍﹒▿﹒⤸﹒○﹒░﹒⇵﹒☆﹒@﹒˘ᗜ˘﹒⬚﹒✸﹒▧﹒◎﹒♡﹒◜ᴗ◝﹒✸﹒ᵔᴗᵔ﹒✿﹑⟡﹒❀﹒★﹒➔﹒％﹒ᗜ﹔﹒⌗﹒﹪﹒﹒⟢﹒ᵔᴗᵔ﹒✮﹒^..^﹒✵﹒
    「 (You can put emojis or other speical characters inside 2 of these paired looking characters) 」─── ⋆⋅☆⋅⋆ ──⫘⫘⫘⫘⫘⫘╭─𒌋𒀖╰─𒌋𒀖╰┈➤╭┈➤⊱  ۫ ׅ ✧
    Categories have a channels list.
    Only announcement-channel and stage-channel lack private key.
    Example:
    {
        template: [
            {
            type: announcement-channel,
            name: server-announcements
            },
            {
            type: stage-channel,
            name: music-events
            },
            {
            type: category,
            name: Community,
            private: (false/true boolean here accoridng to the channel if its for public usage or only staff and admins, here it would be false),
            channels: [
                {
                type: text-channel,
                name: general,
                private: (false/true boolean here accoridng to the channel if its for public usage or only staff and admins, here it would be false)
                },
                {
                type: text-channel,
                name: admin-general,
                private: (false/true boolean here accoridng to the channel if its for public usage or only staff and admins, here it would be true)
                },
                {
                type: forum-channel,
                name: general-forum,
                private: (false/true boolean here accoridng to the channel if its for public usage or only staff and admins, here it would be false)
                },
                {
                type: forum-channel,
                name: admin-general-forum,
                private: (false/true boolean here accoridng to the channel if its for public usage or only staff and admins, here it would be true)
                }
            ]
            },
            {
            type: category,
            name: Voice Channels,
            private: (false/true boolean here accoridng to the channel if its for public usage or only staff and admins, here it would be false),
            channels: [
                {
                type: voice-channel,
                name: general-vc,
                private: (false/true boolean here accoridng to the channel if its for public usage or only staff and admins, here it would be false)
                },
                {
                type: voice-channel,
                name: admin-general-vc,
                private: (false/true boolean here accoridng to the channel if its for public usage or only staff and admins, here it would be true)
                }
            ]
            },
            {
            type: text-channel,
            name: public-stuff,
            private: (false/true boolean here accoridng to the channel if its for public usage or only staff and admins, here it would be false)
            },
            {
            type: text-channel,
            name: private-stuff,
            private: (false/true boolean here accoridng to the channel if its for public usage or only staff and admins, here it would be true)
            }
        ]
    }
    """
    response = together_client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    try:
        template_json = json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, AttributeError):
        embed = discord.Embed(title="Error", description="Invalid template format from AI. 😕", color=discord.Color.red())
        await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
        return
    if not validate_template(template_json["template"]):
        embed = discord.Embed(title="Error", description="Invalid template format generated. 😕", color=discord.Color.red())
        await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
        return
    hex_id = generate_hex_id()
    templates_collection.insert_one({"id": hex_id, "template": template_json["template"]})
    embed = discord.Embed(title="Template Generated", color=discord.Color.green())
    embed.add_field(name="Prompt 💬", value=prompt, inline=False)
    embed.add_field(name="Template ID 🆔", value=f"`{hex_id}`", inline=False)
    embed.add_field(name="Preview 👀", value=f"https://stgai.onrender.com/template/{hex_id}", inline=False)
    await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))

@tree.command(name="apply", description="Apply a server template using its ID")
@app_commands.describe(template_id="The 10-digit hex ID of the template")
async def apply_template(interaction: discord.Interaction, template_id: str):
    await interaction.response.defer()
    if len(template_id) != 10 or not all(c in "0123456789abcdef" for c in template_id):
        embed = discord.Embed(title="Error", description="Invalid template ID. Must be 10-digit hex. 😕", color=discord.Color.red())
        await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
        return
    template_data = templates_collection.find_one({"id": template_id})
    if not template_data:
        embed = discord.Embed(title="Error", description="Template not found. 😔", color=discord.Color.red())
        await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
        return
    guild = interaction.guild
    if not guild:
        embed = discord.Embed(title="Error", description="This command must be used in a server. 😕", color=discord.Color.red())
        await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
        return
    if not interaction.user.guild_permissions.manage_channels:
        embed = discord.Embed(title="Error", description="You need Manage Channels permission. 😔", color=discord.Color.red())
        await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
        return

    # Delete all existing channels, skipping those that cannot be deleted
    skipped_channels = []
    try:
        for channel in guild.channels:
            try:
                await channel.delete()
            except (discord.Forbidden, discord.HTTPException):
                skipped_channels.append(channel.name)
                continue  # Skip channels that can't be deleted (e.g., system or community channels)
    except Exception as e:
        embed = discord.Embed(title="Error", description=f"Error accessing channels: {str(e)} 😔", color=discord.Color.red())
        await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
        return

    # Apply new template
    template = template_data["template"]
    for item in template:
        try:
            overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=not item.get("private", False))} if item.get("private", False) and item["type"] not in {"announcement-channel", "stage-channel"} else {}
            if item["type"] == "category":
                category = await guild.create_category(item["name"], overwrites=overwrites)
                for channel in item.get("channels", []):
                    channel_overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=not channel.get("private", False))} if channel.get("private", False) and channel["type"] not in {"announcement-channel", "stage-channel"} else {}
                    if channel["type"] == "text-channel":
                        await guild.create_text_channel(channel["name"], category=category, overwrites=channel_overwrites)
                    elif channel["type"] == "voice-channel":
                        await guild.create_voice_channel(channel["name"], category=category, overwrites=channel_overwrites)
                    elif channel["type"] == "forum-channel":
                        await guild.create_forum(channel["name"], category=category, overwrites=channel_overwrites)
                    elif channel["type"] == "announcement-channel":
                        await guild.create_text_channel(channel["name"], category=category, news=True, overwrites=channel_overwrites)
                    elif channel["type"] == "stage-channel":
                        await guild.create_stage_channel(channel["name"], category=category, overwrites=channel_overwrites)
            elif item["type"] == "text-channel":
                await guild.create_text_channel(item["name"], overwrites=overwrites)
            elif item["type"] == "voice-channel":
                await guild.create_voice_channel(item["name"], overwrites=overwrites)
            elif item["type"] == "forum-channel":
                await guild.create_forum(item["name"], overwrites=overwrites)
            elif item["type"] == "announcement-channel":
                await guild.create_text_channel(item["name"], news=True, overwrites=overwrites)
            elif item["type"] == "stage-channel":
                await guild.create_stage_channel(item["name"], overwrites=overwrites)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"Error creating {item['name']}: {str(e)} 😔", color=discord.Color.red())
            await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
            return

    # Report skipped channels, if any
    description = f"Template `{template_id}` applied successfully! 🎉"
    if skipped_channels:
        description += f"\nSkipped undeletable channels: {', '.join(skipped_channels)}"
    embed = discord.Embed(title="Template Applied", description=description, color=discord.Color.green())
    await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))

@tree.command(name="help", description="Show available commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="Bot Commands", description="List of available commands 📜", color=discord.Color.blue())
    embed.add_field(name="/generate [prompt]", value="Generate a server template using AI based on the prompt. Returns a 10-digit hex ID. 🎉", inline=False)
    embed.add_field(name="/apply [template_id]", value="Apply a server template using its 10-digit hex ID. Deletes existing channels (skipping undeletable ones) and creates new ones. 🔧", inline=False)
    embed.add_field(name="/help", value="Show this help message. 📖", inline=False)
    await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await tree.sync()

threading.Thread(target=run_flask, daemon=True).start()
client.run(os.getenv("TOKEN"))