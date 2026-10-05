from telethon import Button, events
from lib import *

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://salselfmmk.onrender.com/miniapp').strip()

def miniapp_button():
    # Telethon 1.45 does not expose a stable Button.web_app helper; the real Web App
    # entry point is configured through Bot API setChatMenuButton in main.py.
    return Button.url('کنترل پنل', WEBAPP_URL)


@client.on(events.InlineQuery)
async def inline_handler(event):
    if event.sender_id != admin_user_id or event.text != "/panel":
        return
    text = "**Salself**\n\nمدیریت اکانت تلگرام\nبرای باز کردن پنل کامل، دکمه کنترل پنل را بزن."
    buttons = [[miniapp_button()], [Button.url("Support", SUPPORT_URL)]]
    result = event.builder.article(
        title="پنل کنترل Salself",
        description="باز کردن پنل کنترل",
        text=text,
        buttons=buttons,
    )
    await event.answer([result])


@client.on(events.CallbackQuery)
async def callback(event):
    if event.sender_id != admin_user_id:
        return
    await event.answer("**❈ برای باز کردن پنل کامل، در Saved Messages دستور /panel را بزن.**", alert=True)
