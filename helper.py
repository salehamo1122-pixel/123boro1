from telethon import Button, events
from lib import *

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)


@client.on(events.InlineQuery)
async def inline_handler(event):
    if event.sender_id != admin_user_id or event.text != "/panel":
        return
    text = "**❈ Self Control Panel**\n\nUse /panel in Saved Messages to open the full control panel."
    buttons = [[Button.url("Support", SUPPORT_URL)]]
    result = event.builder.article(
        title="Self Control Panel",
        description="Open the English control panel",
        text=text,
        buttons=buttons,
    )
    await event.answer([result])


@client.on(events.CallbackQuery)
async def callback(event):
    if event.sender_id != admin_user_id:
        return
    await event.answer("**❈ Use /panel in Saved Messages to open the full control panel.**", alert=True)
