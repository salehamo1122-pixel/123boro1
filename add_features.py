# Advanced features injected into the self client.
import os, json, asyncio, datetime, logging
from pathlib import Path
from telethon import events, functions
from telethon.tl.types import Message

logger = logging.getLogger("kirmigam.advanced")

# Injected by main.py after the real user client is created.
client = None
admin_user_id = None

FEATURE_DIR = Path('settings')
FEATURE_DIR.mkdir(exist_ok=True)
AUTO_READ_FILE = FEATURE_DIR / 'auto_read.txt'
AUTO_REPLY_FILE = FEATURE_DIR / 'auto_reply.json'
SECRETARY_FILE = FEATURE_DIR / 'secretary.txt'
AWAY_FILE = FEATURE_DIR / 'away.json'
EVENT_LOG_FILE = FEATURE_DIR / 'event_log_chat.txt'
LOG_CHAT_ENV = os.getenv('LOG_CHAT_ID', '').strip()
CONTACT_SNAPSHOT_FILE = FEATURE_DIR / 'contacts_snapshot.json'
CLOCK_STYLE_FILE = FEATURE_DIR / 'clock_style.txt'

DEFAULT_AWAY = 'درود دوست عزیز، در حال حاضر آفلاینم. به محض آنلاین شدن جواب میدم.'


def _read_flag(path, default=False):
    try:
        return path.read_text(encoding='utf-8').strip().lower() == 'true'
    except Exception:
        return default


def _write_flag(path, value):
    path.write_text('True' if value else 'False', encoding='utf-8')


def _load_json(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def _save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

if not AUTO_READ_FILE.exists(): _write_flag(AUTO_READ_FILE, False)
if not SECRETARY_FILE.exists(): _write_flag(SECRETARY_FILE, False)
if not CLOCK_STYLE_FILE.exists(): CLOCK_STYLE_FILE.write_text('classic', encoding='utf-8')
if not AUTO_REPLY_FILE.exists(): _save_json(AUTO_REPLY_FILE, {'enabled': False, 'text': DEFAULT_AWAY})
if not AWAY_FILE.exists(): _save_json(AWAY_FILE, {'enabled': False, 'text': DEFAULT_AWAY})

away_replied = set()
file_cover_waiting = {}

CLOCK_STYLES = {
    'classic': lambda s: s,
    'bold': lambda s: s.translate(str.maketrans('0123456789', '𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗')),
    'circle': lambda s: s.translate(str.maketrans('0123456789', '⓪①②③④⑤⑥⑦⑧⑨')),
    'double': lambda s: s.translate(str.maketrans('0123456789', '𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡')),
    'farsi': lambda s: s.translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')),
    'mini': lambda s: s.translate(str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')),
}


def styled_clock():
    raw = datetime.datetime.now().strftime('%H:%M')
    style = CLOCK_STYLE_FILE.read_text(encoding='utf-8').strip() if CLOCK_STYLE_FILE.exists() else 'classic'
    return CLOCK_STYLES.get(style, CLOCK_STYLES['classic'])(raw)


def configure(client_instance, owner_id):
    """Attach the real Telethon user client and owner id to this module."""
    global client, admin_user_id
    client = client_instance
    admin_user_id = int(owner_id)


LOG_MARKER = "SELF_CONFIG::LOG_CHAT_ID="

async def _find_log_marker():
    if client is None:
        return None
    try:
        async for msg in client.iter_messages("me", search=LOG_MARKER, limit=10):
            if msg.raw_text and LOG_MARKER in msg.raw_text:
                return msg
    except Exception:
        logger.exception("Could not search Saved Messages for log marker")
    return None


async def restore_log_chat():
    """Restore the log target from env or a single config marker in Saved Messages."""
    env_target = os.getenv("LOG_CHAT_ID", "").strip()
    if env_target:
        EVENT_LOG_FILE.write_text(env_target, encoding="utf-8")
        return env_target
    marker = await _find_log_marker()
    if marker and marker.raw_text:
        target = marker.raw_text.split(LOG_MARKER, 1)[1].split()[0].strip()
        if target:
            EVENT_LOG_FILE.write_text(target, encoding="utf-8")
            return target
    return EVENT_LOG_FILE.read_text(encoding="utf-8").strip() if EVENT_LOG_FILE.exists() else ""


async def set_log_chat(chat_id):
    """Set the log destination immediately and persist it through Telegram."""
    target = str(chat_id)
    EVENT_LOG_FILE.write_text(target, encoding="utf-8")
    marker = await _find_log_marker()
    marker_text = f"{LOG_MARKER}{target}"
    try:
        if marker:
            await marker.edit(marker_text)
        else:
            await client.send_message("me", marker_text)
    except Exception:
        logger.exception("Could not persist log target marker")
    return target


async def get_event_log_target():
    env_target = os.getenv("LOG_CHAT_ID", "").strip()
    if env_target:
        return env_target
    if EVENT_LOG_FILE.exists():
        return EVENT_LOG_FILE.read_text(encoding="utf-8").strip()
    return await restore_log_chat()


async def event_log(text, file_path=None):
    """Send operational notifications to the configured log chat, never Saved Messages."""
    target = await get_event_log_target()
    if not target or client is None:
        return False
    try:
        entity = int(target) if target.lstrip('-').isdigit() else target
        if file_path:
            await client.send_file(entity, file_path, caption=text)
        else:
            await client.send_message(entity, text)
        return True
    except Exception:
        logger.exception('event_log failed for target=%s', target)
        return False


@events.register(events.NewMessage(pattern=r'(?i)^(?:/autoread|auto_read|خواندن_خودکار)\s+(on|off|روشن|خاموش)$'))
async def advanced_auto_read(event):
    if event.sender_id != admin_user_id: return
    enabled = event.pattern_match.group(1).lower() in ('on', 'روشن')
    _write_flag(AUTO_READ_FILE, enabled)
    await event.reply('❈ Auto-read enabled.' if enabled else '❈ Auto-read disabled.')


@events.register(events.NewMessage(pattern=r'(?i)^/(?:autoreply|پاسخ_خودکار)\s+(on|off|روشن|خاموش)$'))
async def advanced_auto_reply_toggle(event):
    if event.sender_id != admin_user_id: return
    data = _load_json(AUTO_REPLY_FILE, {'enabled': False, 'text': DEFAULT_AWAY})
    data['enabled'] = event.pattern_match.group(1).lower() in ('on', 'روشن')
    _save_json(AUTO_REPLY_FILE, data)
    away_replied.clear()
    await event.reply('❈ Auto-reply enabled.' if data['enabled'] else '❈ Auto-reply disabled.')


@events.register(events.NewMessage(pattern=r'(?i)^/(?:autoreply|پاسخ_خودکار)\s+text\s+(.+)$'))
async def advanced_auto_reply_text(event):
    if event.sender_id != admin_user_id: return
    data = _load_json(AUTO_REPLY_FILE, {'enabled': False, 'text': DEFAULT_AWAY})
    data['text'] = event.pattern_match.group(1).strip()[:500]
    _save_json(AUTO_REPLY_FILE, data)
    await event.reply('❈ Auto-reply text updated.')


@events.register(events.NewMessage(pattern=r'(?i)^/(?:away|آفلاین)\s+(on|off|روشن|خاموش)$'))
async def advanced_away_toggle(event):
    if event.sender_id != admin_user_id: return
    data = _load_json(AWAY_FILE, {'enabled': False, 'text': DEFAULT_AWAY})
    data['enabled'] = event.pattern_match.group(1).lower() in ('on', 'روشن')
    _save_json(AWAY_FILE, data)
    away_replied.clear()
    await event.reply('❈ Away mode enabled.' if data['enabled'] else '❈ Away mode disabled.')


@events.register(events.NewMessage(pattern=r'(?i)^/(?:away|آفلاین)\s+text\s+(.+)$'))
async def advanced_away_text(event):
    if event.sender_id != admin_user_id: return
    data = _load_json(AWAY_FILE, {'enabled': False, 'text': DEFAULT_AWAY})
    data['text'] = event.pattern_match.group(1).strip()[:500]
    _save_json(AWAY_FILE, data)
    await event.reply('❈ Away message updated.')


@events.register(events.NewMessage(pattern=r'(?i)^/(?:secretary|منشی)\s+(on|off|روشن|خاموش)$'))
async def advanced_secretary_toggle(event):
    if event.sender_id != admin_user_id: return
    enabled = event.pattern_match.group(1).lower() in ('on', 'روشن')
    _write_flag(SECRETARY_FILE, enabled)
    away_replied.clear()
    await event.reply('❈ Smart secretary enabled.' if enabled else '❈ Smart secretary disabled.')


@events.register(events.NewMessage(pattern=r'(?i)^/(?:clock|ساعت)\s+(classic|bold|circle|double|farsi|mini)$'))
async def advanced_clock_style(event):
    if event.sender_id != admin_user_id: return
    style = event.pattern_match.group(1).lower()
    CLOCK_STYLE_FILE.write_text(style, encoding='utf-8')
    await event.reply(f'❈ Clock style set to {style}.')


@events.register(events.NewMessage(pattern=r'(?i)^/(?:setlogchat|ثبت_گپ_اعلان)$'))
async def advanced_set_log_chat(event):
    if event.sender_id != admin_user_id:
        return
    target = await set_log_chat(event.chat_id)
    await event.reply(
        f'❈ مقصد اعلان‌ها تنظیم شد.\n\nChat ID: `{target}`\n\n'
        'ضدحذف، ادیت/حذف و تغییرات پروفایل از این به بعد به همین گپ می‌روند.'
    )


@events.register(events.NewMessage(pattern=r'(?i)^/(?:logchat|گپ_اعلان)$'))
async def advanced_show_log_chat(event):
    if event.sender_id != admin_user_id:
        return
    target = await get_event_log_target()
    if not target:
        await event.reply('❈ هنوز مقصد اعلان‌ها تنظیم نشده است. همین‌جا `/setlogchat` را بفرست.')
        return
    try:
        entity = await client.get_entity(int(target) if target.lstrip('-').isdigit() else target)
        name = getattr(entity, 'title', None) or getattr(entity, 'first_name', None) or getattr(entity, 'username', None) or str(target)
    except Exception:
        name = str(target)
    await event.reply(f'❈ مقصد اعلان‌ها: {name}\nChat ID: `{target}`')


@events.register(events.NewMessage(pattern=r'(?i)^/(?:renamefile|تغییر_نام_فایل)\s+(.+)$'))
async def advanced_rename_file(event):
    if event.sender_id != admin_user_id or not event.is_reply: return
    reply = await event.get_reply_message()
    if not reply or not reply.media:
        await event.reply('❈ Reply to a file/media message first.')
        return
    new_name = event.pattern_match.group(1).strip()
    if not Path(new_name).suffix:
        old_name = getattr(getattr(reply.media, 'document', None), 'attributes', None)
        ext = '.bin'
        if old_name:
            for attr in old_name:
                fn = getattr(attr, 'file_name', None)
                if fn and Path(fn).suffix:
                    ext = Path(fn).suffix; break
        new_name += ext
    tmp = await reply.download_media(file='save/')
    try:
        await client.send_file(event.chat_id, tmp, caption=reply.raw_text or '', force_document=True, file_name=new_name)
        await event.reply('❈ File re-uploaded with the new name.')
    finally:
        if tmp and os.path.exists(tmp): os.remove(tmp)


@events.register(events.NewMessage(pattern=r'(?i)^/(?:filecover|کاور_فایل)$'))
async def advanced_file_cover_start(event):
    if event.sender_id != admin_user_id or not event.is_reply: return
    reply = await event.get_reply_message()
    if not reply or not reply.media:
        await event.reply('❈ Reply to the target file first, then send a photo as the next message.')
        return
    file_cover_waiting[event.chat_id] = reply.id
    await event.reply('❈ Now send the cover photo. The file will be re-uploaded with that cover.')


@events.register(events.NewMessage())
async def advanced_file_cover_finish(event):
    if event.sender_id != admin_user_id or event.chat_id not in file_cover_waiting or not event.media:
        return
    # Ignore commands and non-photo media.
    if event.raw_text and event.raw_text.startswith('/'):
        return
    if not getattr(event.media, 'photo', None):
        return
    source_id = file_cover_waiting.pop(event.chat_id, None)
    try:
        source = await client.get_messages(event.chat_id, ids=source_id)
        if not source or not source.media:
            await event.reply('❈ Original file was not found.')
            return
        original = await source.download_media(file='save/')
        cover = await event.download_media(file='save/')
        try:
            name = 'renamed_file'
            doc = getattr(source.media, 'document', None)
            if doc:
                for attr in getattr(doc, 'attributes', []):
                    fn = getattr(attr, 'file_name', None)
                    if fn: name = fn; break
            await client.send_file(event.chat_id, original, thumb=cover, force_document=True, file_name=name, caption=source.raw_text or '')
            await event.reply('❈ File re-uploaded with the new cover.')
        finally:
            for p in (original, cover):
                if p and os.path.exists(p): os.remove(p)
    except Exception as exc:
        await event.reply(f'❈ Cover operation failed: {str(exc)[:180]}')


@events.register(events.NewMessage(incoming=True))
async def advanced_incoming_controls(event):
    if event.sender_id == admin_user_id:
        return
    if _read_flag(AUTO_READ_FILE, False):
        try:
            await client.send_read_acknowledge(event.chat_id, max_id=event.id)
        except Exception:
            pass
    if not event.is_private:
        return
    away = _load_json(AWAY_FILE, {'enabled': False, 'text': DEFAULT_AWAY})
    auto = _load_json(AUTO_REPLY_FILE, {'enabled': False, 'text': DEFAULT_AWAY})
    secretary = _read_flag(SECRETARY_FILE, False)
    if not (away.get('enabled') or auto.get('enabled') or secretary):
        return
    if event.sender_id in away_replied:
        return
    text = (event.raw_text or '').lower()
    if secretary:
        if any(x in text for x in ('سلام', 'hello', 'hi', 'درود')):
            response = 'درود 🌹 پیام شما دریافت شد. در حال حاضر در دسترس نیستم و بعداً پاسخ می‌دهم.'
        elif any(x in text for x in ('کجایی', 'where are you', 'کجایی؟')):
            response = 'در حال حاضر در دسترس نیستم. به محض آنلاین شدن پاسخ می‌دهم.'
        elif any(x in text for x in ('کمک', 'help')):
            response = 'پیامت دریافت شد. وقتی برگردم بررسی می‌کنم.'
        else:
            response = away.get('text') or auto.get('text') or DEFAULT_AWAY
    else:
        response = away.get('text') if away.get('enabled') else auto.get('text')
    try:
        await event.reply(response)
        away_replied.add(event.sender_id)
    except Exception:
        logger.exception('advanced auto reply failed')


async def advanced_profile_watch_loop():
    """Periodically snapshot contacts and notify the configured event-log chat."""
    while True:
        try:
            contacts = {}
            async for user in client.iter_contacts():
                contacts[str(user.id)] = {
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'username': user.username or '',
                    'phone': user.phone or '',
                }
            old = _load_json(CONTACT_SNAPSHOT_FILE, {})
            added = [uid for uid in contacts if uid not in old]
            removed = [uid for uid in old if uid not in contacts]
            changed = [uid for uid in contacts if uid in old and contacts[uid] != old[uid]]
            if added:
                await event_log('❈ New contact/profile detected:\n' + '\n'.join(added[:30]))
            if removed:
                await event_log('❈ Contact/profile removed:\n' + '\n'.join(removed[:30]))
            if changed:
                lines = []
                for uid in changed[:20]:
                    lines.append(f"{uid}: {old[uid].get('first_name','')} → {contacts[uid].get('first_name','')}")
                await event_log('❈ Contact profile changed:\n' + '\n'.join(lines))
            _save_json(CONTACT_SNAPSHOT_FILE, contacts)
        except Exception:
            logger.exception('advanced_profile_watch_loop failed')
        await asyncio.sleep(300)
