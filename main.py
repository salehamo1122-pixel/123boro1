# coded by @saleh681 in Telegram
import logging
from keep_alive import keep_alive

keep_alive()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("kirmigam")

from lib import *
from telethon import Button
from telethon.tl.types import MessageEntitySpoiler
from datetime import timezone as dt_timezone

import speech_recognition as sr
from pydub import AudioSegment
pending_input = {}
bot_client = TelegramClient('helper_session', api_id, api_hash)
saved_messages_cache = {}
MEDIA_CACHE_DIR = os.path.join('save', 'deleted_cache')
MAX_DELETED_CACHE = 100
os.makedirs(MEDIA_CACHE_DIR, exist_ok=True)
NOTES_FILE = os.path.join('save', 'notes.txt')
os.makedirs('save', exist_ok=True)
if not os.path.exists(NOTES_FILE):
    open(NOTES_FILE, 'a', encoding='utf-8').close()
anti_delete_chats = set()
ANTI_DELETE_GLOBAL_FILE = os.path.join('settings', 'anti_delete_global.txt')
os.makedirs('settings', exist_ok=True)
if not os.path.exists(ANTI_DELETE_GLOBAL_FILE):
    with open(ANTI_DELETE_GLOBAL_FILE, 'w', encoding='utf-8') as _f:
        _f.write('False')

def is_global_anti_delete_enabled():
    try:
        return open(ANTI_DELETE_GLOBAL_FILE, 'r', encoding='utf-8').read().strip().lower() == 'true'
    except OSError:
        return False

def set_global_anti_delete(enabled):
    with open(ANTI_DELETE_GLOBAL_FILE, 'w', encoding='utf-8') as _f:
        _f.write('True' if enabled else 'False')

anti_delete_global_enabled = is_global_anti_delete_enabled()
ghost_mode_enabled = False
spoiler_mode_enabled = False

# Advanced account features (loaded after the self client and globals exist)
import add_features as _advanced_features

# Advanced handlers are declared without a client. Inject the real self client
# before Telegram starts delivering updates, then attach every registered handler.
_advanced_features.configure(client, admin_user_id)
for _name in dir(_advanced_features):
    _handler = getattr(_advanced_features, _name, None)
    if callable(_handler) and events.is_handler(_handler):
        client.add_event_handler(_handler)


def _button_style(style):
    return style if style in {"primary", "success", "danger"} else "primary"


def pbtn(text, data, style="primary"):
    """Create a Telegram button with the new native color styles.
    Falls back cleanly if an older Telethon build is used.
    """
    style = _button_style(style)
    try:
        return Button.inline(text, data, style=style)
    except TypeError:
        # Compatibility fallback for older Telethon releases.
        try:
            style_obj = types.KeyboardButtonStyle(
                bg_primary=style == "primary",
                bg_success=style == "success",
                bg_danger=style == "danger",
            )
            return types.KeyboardButtonCallback(text=text, data=data, style=style_obj)
        except Exception:
            return Button.inline(text, data)


def purl(text, url, style="primary"):
    try:
        return Button.url(text, url, style=_button_style(style))
    except TypeError:
        return Button.url(text, url)


def support_button():
    return purl("Support", SUPPORT_URL, "primary")


def result_ok(text):
    return f"**❈ {text}**"


def result_info(text):
    return f"**❈ {text}**"


def result_error(text):
    return f"❈ Error: {text}"


def admin_only(event):
    return event.sender_id == admin_user_id
settings_folder = 'settings'
file_defaults = {
    'time.txt': 'False',
    'timepic.txt': 'False',
    'nameinfo.txt': 'time',
    'bioinfo.txt': 'False',
    'heart.txt': 'False',
    'rnamest.txt': 'False',
    'bio.txt': 'time',
    'mode.txt': 'Default',
    'creator.txt': '@DevSeyed',
    'tpic.json': '{"cordx": 80, "cordy": 230, "size": 50, "color": "white"}',
    'rname.txt': ''
}

if not os.path.exists(settings_folder):
    os.makedirs(settings_folder)

for file_name, default_content in file_defaults.items():
    file_path = os.path.join(settings_folder, file_name)
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write(default_content)

def add_note(text):
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(NOTES_FILE, 'a', encoding='utf-8') as f:
        f.write(f'[{stamp}] {text}\n')

def read_notes(limit=10):
    try:
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            lines = [line.rstrip() for line in f if line.strip()]
        return lines[-limit:]
    except Exception:
        return []

async def unread_summary():
    rows = []
    async for dialog in client.iter_dialogs():
        if dialog.unread_count:
            entity = dialog.entity
            name = getattr(entity, 'title', None) or getattr(entity, 'first_name', None) or getattr(entity, 'username', None) or str(entity.id)
            rows.append((dialog.unread_count, name, dialog.id))
    rows.sort(reverse=True)
    return rows[:15]

@client.on(events.NewMessage(pattern=r'(?i)^(?:/note|یادداشت)\s+(.+)$'))
async def add_note_command(event):
    if event.sender_id != admin_user_id: return
    text = event.pattern_match.group(1).strip()
    add_note(text)
    await event.reply(f'**❈ Note saved.**\n{text[:500]}')

@client.on(events.NewMessage(pattern=r'(?i)^(?:/notes|یادداشتها)$'))
async def list_notes_command(event):
    if event.sender_id != admin_user_id: return
    notes = read_notes(15)
    await event.reply('**❈ Latest Notes**\n\n' + ('\n'.join(notes) if notes else 'No notes yet.')[:3500])

@client.on(events.NewMessage(pattern=r'(?i)^(?:/clear_notes|پاک_کردن_یادداشتها)$'))
async def clear_notes_command(event):
    if event.sender_id != admin_user_id: return
    open(NOTES_FILE, 'w', encoding='utf-8').close()
    await event.reply('**❈ Notes cleared.**')

@client.on(events.NewMessage(pattern=r'(?i)^(?:/unread|خوانده_نشده)$'))
async def unread_command(event):
    if event.sender_id != admin_user_id: return
    rows = await unread_summary()
    if not rows:
        await event.reply('**❈ No unread chats.**')
        return
    text = '**❈ Unread Center**\n\n' + '\n'.join(f'• {name}: {count}' for count, name, _ in rows)
    await client.send_message('me', text)
    await event.reply(f'**❈ {len(rows)} unread chats sent to Saved Messages.**')

@client.on(events.NewMessage(pattern=r'(?i)^(?:/health|سلامت)$'))
async def health_command(event):
    if event.sender_id != admin_user_id: return
    dialogs = 0
    async for _ in client.iter_dialogs(): dialogs += 1
    try:
        cache_files = len([x for x in os.listdir(MEDIA_CACHE_DIR) if os.path.isfile(os.path.join(MEDIA_CACHE_DIR, x))])
    except Exception:
        cache_files = 0
    await event.reply(f'**❈ System Health**\n\nConnection: OK\nUptime: {get_uptime(start_time)}\nMemory: {psutil.virtual_memory().percent}%\nDialogs: {dialogs}\nNotes: {len(read_notes(100000))}\nDeleted cache: {cache_files}')

#check command
@client.on(events.NewMessage(pattern='(?i)(/check|/چک)'))
async def handle_start_command(event):
    await start_command(event)
#end of command check


@client.on(events.NewMessage(pattern='(?i)(/help|/راهنما)'))
async def handle_inline(event):
    if event.sender_id == admin_user_id:
        try:
            if event.raw_text.lower() in ['/help', '/راهنما']:
                await show_panel(event)
                await event.delete()
            elif event.raw_text in ['/help 1', '/راهنما 1']:
                await help_1(event)
            elif event.raw_text in ['/help 2', '/راهنما 2']:
                await help_2(event)
            elif event.raw_text in ['/help 3', '/راهنما 3']:
                await help_3(event)
            elif event.raw_text in ['/help 4', '/راهنما 4']:
                await help_4(event)
        except Exception as e:
            await event.reply(f"Error sending panel: {e}")


@client.on(events.NewMessage(pattern='(?i)(/ping|/Ping)'))
async def handle_ping(event):
    await ping(event)


@client.on(events.NewMessage(pattern='(?i)(/mem|/حافظه)'))
async def handle_mem(event):
    await mem(event)


if not os.path.exists(MSAVE_DIRECTORY):
    os.makedirs(MSAVE_DIRECTORY)

@client.on(events.NewMessage(pattern='(?i)(/gmusic|/موزیک)'))
async def handle_sc(event):
    await sc(event)

@client.on(events.NewMessage(pattern='(?i)(/tarikh|/تاریخ)'))
async def handle_tarikh(event):
    await tarikh(event)

@client.on(events.NewMessage(pattern='(?i)(/gmsg|/تایپ_متن)'))
async def handle_gmsg(event):
    await gmsg(event)

@client.on(events.NewMessage(pattern='(?i)(/weather|/هواشناسی)'))
async def handle_weather(event):
    await weather(event)

@client.on(events.NewMessage(pattern='(?i)(/rsong|/آهنگ_Random)'))
async def handle_rsong(event):
    await rsong(event)

@client.on(events.NewMessage(pattern='(?i)(/info|/اطلاعات)'))
async def handle_info(event):
    await info(event)

@client.on(events.NewMessage(pattern='(?i)(/setprof|/تنظیم_عکس)'))
async def handle_set_profile_pic(event):
    await set_profile_pic(event)

@client.on(events.NewMessage(pattern='(?i)(/delprof|/حذف_عکس)'))
async def handle_delete_profile_pic(event):
    await delete_profile_pic(event)

@client.on(events.NewMessage(pattern='(?i)(/rinfo|/اطلاعات_کاربر)'))
async def handle_rinfo(event):
    await rinfo(event)

@client.on(events.NewMessage(pattern='(?i)(/rem|/حذف_اخیر)'))
async def handle_delete_recent_messages(event):
    await delete_recent_messages(event)

@client.on(events.NewMessage(pattern='(?i)(/sgoogle|/گوگل)'))
async def handle_sgoogle(event):
    await sgoogle(event)

@client.on(events.NewMessage(pattern='(?i)(/wiki|/ویکی)'))
async def handle_wiki(event):
    await wiki(event)

@client.on(events.NewMessage(pattern='(?i)(/save|/ذخیره)'))
async def handle_save_message(event):
    await save_message(event)
#Auto Save
@client.on(events.NewMessage)
async def save_self_destructing_media(event):
    try:
        if (
            event.sender_id != admin_user_id
            and event.is_private
            and event.message.media
            and hasattr(event.message.media, 'ttl_seconds')
            and event.message.media.ttl_seconds is not None
            and event.message.media.ttl_seconds > 0
        ):
            file = await event.download_media()
            user_id = event.sender_id
            username = event.sender.username
            caption = f"❈ Self-Saved Photo From User: {user_id}, @{username}"
            await client.send_file(admin_user_id, file, caption=caption)
            os.remove(file)

    except Exception as e:
        await event.respond(f"❈ Error while saving self-destructing media: {str(e)}")
# End Auto Save
        
@client.on(events.NewMessage(pattern='(?i)(/addbio|/اضافه_بیو)'))
async def handle_add_bio(event):
    await add_bio(event)

@client.on(events.NewMessage(pattern='(?i)(/addlname|/اضافه_نام_خانوادگی)'))
async def handle_add_lname(event):
    await add_lname(event)

@client.on(events.NewMessage(pattern='(?i)(/addrname|/اضافه_نام_Random)'))
async def handle_add_rname(event):
    await add_rname(event)

@client.on(events.NewMessage(pattern='(?i)(/delrname|/حذف_نام_Random)'))
async def handle_delete_rname(event):
    await delete_rname(event)

@client.on(events.NewMessage(pattern='(?i)(/reload|/ریلود)'))
async def handle_reload_bot(event):
    await reload_bot(event)

@client.on(events.NewMessage(pattern='(?i)(/backupchat|/پشتیبان_چت)'))
async def handle_backup_chat(event):
    await backup_chat(event)

@client.on(events.NewMessage(pattern='(?i)(/calc|/محاسبه)'))
async def handle_calculator(event):
    await calculator(event)

@client.on(events.NewMessage(pattern='(?i)(/create_channel|/ساخت_کانال) (.*)'))
async def handle_create_channel(event):
    await create_channel(event)

@client.on(events.NewMessage(pattern='(?i)(/silent|/سکوت)'))
async def handle_enemy_mode(event):
    await enemy_mode(event)

@client.on(events.NewMessage(pattern='(?i)(/unsilent|/رفع_سکوت)'))
async def handle_unenemy_mode(event):
    await unenemy_mode(event)

@client.on(events.NewMessage)
async def delete_enemy_messages(event):
    sender_id = event.sender_id
    if sender_id in enemy_list:
        user_msgs = user_messages.get(sender_id, [])
        user_msgs.append(event.message)
        user_messages[sender_id] = user_msgs[-10:]

        if len(user_msgs) >= 10:
            await client(functions.contacts.BlockRequest(sender_id))
            await client.send_message(admin_user_id, f"❈System Notification ⚠️\nBlocked User {sender_id} for sending too many messages while in silent mode")

        await event.delete()

@client.on(events.NewMessage(pattern='(?i)(/tag|/تگ)'))
async def handle_tag_all_members(event):
    await tag_all_members(event)

@client.on(events.NewMessage(pattern='(?i)(/Del|/پاک)'))
async def handle_delete_reply(event):
    await delete_reply(event)

@client.on(events.NewMessage(pattern='(?i)(/GSilent|/سکوت_گروه)'))
async def handle_save_user_id(event):
    await save_user_id(event)

@client.on(events.NewMessage(pattern=r'(?i)(/GUnSilent|/رفع_سکوت_گروه)(\s+\d+)?'))
async def handle_remove_user_from_silenced(event):
    await remove_user_from_silenced(event)

@client.on(events.NewMessage(pattern='(?i)(/promote|/ادمین)'))
async def handle_promote_user_to_admin(event):
    await promote_user_to_admin(event)

@client.on(events.NewMessage(pattern='(?i)(/demote|/عزل)'))
async def handle_demote_admin(event):
    await demote_admin(event)

@client.on(events.NewMessage)
async def delete_silent_user_messages(event):
    if event.is_group and event.sender_id in silenced_users:
        await client.delete_messages(event.chat_id, [event.id])

@client.on(events.NewMessage(pattern='(?i)(/pass|/رمز)'))
async def handle_generate_password(event):
    await generate_password(event)

if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)
@client.on(events.NewMessage(pattern='(?i)(/Gmedia|/ذخیره_ویدیو)'))
async def handle_save_video(event):
    await save_video(event)

@client.on(events.NewMessage(pattern='(?i)(/Smedia|/ارسال_ویدیو)'))
async def handle_send_video(event):
    await send_video(event)

@client.on(events.NewMessage(pattern='(?i)(/Lmedia|/لیست_ویدیو)'))
async def handle_list_saved_media(event):
    await list_saved_media(event)

@client.on(events.NewMessage(pattern='(?i)(/Freplay|/پاسخ_سریع)'))
async def handle_fast_replies(event):
    await ffast_replies(event)

@client.on(events.NewMessage(pattern='(?i)(/Lreplay|/لیست_پاسخ)'))
async def handle_show_fast_replies(event):
    await show_fast_replies(event)

@client.on(events.NewMessage)
async def handle_user_message(event):
    if event.sender_id != admin_user_id:
        message = event.raw_text
        reply = fast_replies.get(message.lower())
        if reply:
            await event.reply(reply)

@client.on(events.NewMessage(pattern='(?i)(/whois|/هویت_دامنه)'))
async def handle_whois_domain(event):
    await whois_domain(event)

@client.on(events.NewMessage(pattern='(?i)(/Scrypto|/قیمت_ارز)'))
async def handle_show_crypto_prices(event):
    await show_crypto_prices(event)

@client.on(events.NewMessage(pattern='(?i)(/sreplace|/جایگزین)'))
async def handle_replace_words(event):
    await replace_words(event)

@client.on(events.NewMessage(pattern='(?i)(/Convertdate|/تبدیل_تاریخ)'))
async def handle_convert_date(event):
    await globals()['convert_date'](event)

@client.on(events.NewMessage(pattern='(?i)(/setname|/تنظیم_نام)'))
async def handle_set_user_first_name(event):
    await set_user_first_name(event)

@client.on(events.NewMessage(pattern='(?i)(/sfootball|/فوتبال)'))
async def handle_get_football_stats(event):
    await get_football_stats(event)

@client.on(events.NewMessage(pattern='(?i)(/setcolor|/تنظیم_رنگ)'))
async def handle_apply_color_filter(event):
    await apply_color_filter(event)

@client.on(events.NewMessage(pattern=r'(?i)(/flood|/فلود) (\d+) - ([\w,]+)'))
async def handle_flood_message(event):
    await flood_message(event)

@client.on(events.NewMessage(pattern='(?i)(/orcen|/تبدیل_ویس) (.+)'))
async def handle_replay_as_voice(event):
    await replay_as_voice(event)

@client.on(events.NewMessage(pattern='(?i)(/setfname|/تنظیم_نام_فایل) (.+)'))
async def handle_set_music_name(event):
    await set_music_name(event)

@client.on(events.NewMessage(pattern='(?i)(/screen|/اسکرین) (.+)'))
async def handle_take_screenshot(event):
    await take_screenshot(event)

if not os.path.exists(SAVE_DIRECTORY_YT):
    os.makedirs(SAVE_DIRECTORY_YT)

@client.on(events.NewMessage(pattern='(?i)(/yt|/یوتیوب) (.+)'))
async def handle_download_youtube_video(event):
    await download_youtube_video(event)

@client.on(events.NewMessage(pattern='(?i)(/Sproxy|/پروکسی)'))
async def handle_proxy_command(event):
    await proxy_command(event)

@client.on(events.NewMessage(pattern='(?i)(/Sv2ray|/وی_تو_ری)'))
async def handle_v2ray_command(event):
    await v2ray_command(event)


@client.on(events.NewMessage(pattern='(?i)(/time|/ساعت) (.+)'))
async def handle_get_world_time(event):
    await get_world_time(event)

load_timers()

@client.on(events.NewMessage(pattern='(?i)(newtimer|تایمر_جدید) (.+)'))
async def handle_create_timer(event):
    await create_timer(event)

@client.on(events.NewMessage(pattern='(?i)(deltimer|حذف_تایمر) (.+)'))
async def handle_delete_timer(event):
    await delete_timer(event)

@client.on(events.NewMessage(pattern='(?i)(timers|تایمرها)'))
async def handle_list_timers(event):
    await list_timers(event)

@client.on(events.NewMessage(pattern='(?i)(clean timers|پاکسازی_تایمرها)'))
async def handle_clean_timers(event):
    await clean_timers(event)

@client.on(events.NewMessage(pattern='(?i)(gfile|فایل) (.+)'))
async def handle_download_file(event):
    await download_file(event)

@client.on(events.NewMessage(pattern='(?i)(getip|آی_پی) (.+)'))
async def handle_get_ip_info(event):
    await get_ip_info(event)
@client.on(events.NewMessage(pattern='(?i)(/sunextract|/استخراج فایل)'))
async def handle_extract_files(event):
    await extract_files(event)

@client.on(events.NewMessage(pattern='(?i)(Stv|تلویزیون)'))
async def handle_send_tv_channels(event):
    await send_tv_channels(event)

@client.on(events.NewMessage(pattern='(به qr|sqr|به_کیوآر)'))
async def handle_create_qr_code(event):
    await create_qr_code(event)

@client.on(events.NewMessage(pattern='(?i)(خواندن qr|readqr|خواندن_کیوآر)'))
async def handle_read_qr_code(event):
    await read_qr_code(event)

@client.on(events.NewMessage(pattern='(پاکسازی همه|cleanall)'))
async def handle_clean_messages_containing_text(event):
    await clean_messages_containing_text(event)

@client.on(events.NewMessage(pattern='^(joinall|پیوستن به همه)$'))
async def handle_join_all_channels(event):
    await join_all_channels(event)

@client.on(events.NewMessage(pattern='^(setusername|تنظیم نام کاربری) (.+)'))
async def handle_set_bot_username(event):
    await set_bot_username(event)

@client.on(events.NewMessage(pattern='^(اخراج|kick) (.+)'))
async def handle_kick_users(event):
    await kick_users(event)

@client.on(events.NewMessage(pattern='(پاکسازی بین|cleanb)'))
async def handle_clean_between_messages(event):
    await clean_between_messages(event)

@client.on(events.NewMessage(pattern='(?i)(/Ggit|/گیت)'))
async def handler_Git(event):
    await Git(event)

@client.on(events.NewMessage(pattern='(?i)(/copycontent|/کپی_محتوا)'))
async def handler_copycontent(event):
    await copycontent(event)

@client.on(events.NewMessage(pattern='(?i)(ReadAllPvs|خواندن_همه_پیوی)'))
async def handle_read_all_pvs(event):
    await read_all_pvs(event)

@client.on(events.NewMessage(pattern='(?i)(ReadallGps|خواندن_همه_گروه)'))
async def handle_read_all_groups(event):
    await read_all_groups(event)

@client.on(events.NewMessage(pattern='(?i)(ReadAllChannels|خواندن_همه_کانال)'))
async def handle_read_all_channels(event):
    await read_all_channels(event)

@client.on(events.NewMessage(pattern='(?i)(ReadAllBots|خواندن_همه_ربات)'))
async def handle_read_all_bots(event):
    await read_all_bots(event)

@client.on(events.NewMessage(pattern='(?i)(typing on|تایپ روشن)'))
async def handle_start_typing(event):
    await start_typing(event)

@client.on(events.NewMessage(pattern='(?i)(typing off|تایپ خاموش)'))
async def handle_stop_typing(event):
    await stop_typing(event)

@client.on(events.NewMessage(pattern='(?i)(sticker on|استیکر روشن)'))
async def handle_start_sticker(event):
    await start_sticker(event)

@client.on(events.NewMessage(pattern='(?i)(sticker off|استیکر خاموش)'))
async def handle_stop_sticker(event):
    await stop_sticker(event)

@client.on(events.NewMessage(pattern='(?i)(gaming on|گیم روشن)'))
async def handle_start_game(event):
    await start_game(event)

@client.on(events.NewMessage(pattern='(?i)(gaming off|گیم خاموش)'))
async def handle_stop_game(event):
    await stop_game(event)

@client.on(events.NewMessage(pattern='(?i)(DelVideos|حذف_ویدیوها)'))
async def delete_videos(event):
    await delete_media(event, media_type='video')

@client.on(events.NewMessage(pattern='(?i)(DelPhotos|حذف_عکسها)'))
async def delete_photos(event):
    await delete_media(event, media_type='photo')

@client.on(events.NewMessage(pattern='(?i)(DelVoices|حذف_ویسها)'))
async def delete_voices(event):
    await delete_media(event, media_type='voice')

@client.on(events.NewMessage(pattern='(?i)(DelFiles|حذف_فایلها)'))
async def delete_files(event):
    await delete_media(event, media_type='document')

@client.on(events.NewMessage(pattern='(?i)(DelVideoNotes|حذف_ویدیومسیج)'))
async def delete_video_notes(event):
    await delete_media(event, media_type='video_note')

@client.on(events.NewMessage(pattern='(?i)(DelGifs|حذف_گیفها)'))
async def delete_gifs(event):
    await delete_media(event, media_type='gif')

@client.on(events.NewMessage(pattern='(?i)(Pvinfo|اطلاعات_پیوی)'))
async def handle_pvinfo(event):
    await pvinfo(event)
@client.on(events.NewMessage(pattern='(?i)^(/chkdomain|/چک_دامنه)'))
async def handle_check_domain(event):
    await check_domain(event)

@client.on(events.NewMessage(pattern='(?i)^(/logout|/خروج)'))
async def logout_handler(event):
    await logout(event)

@client.on(events.NewMessage(pattern='(?i)(tpic|عکس_موقت)'))
async def handle_tpic_set(event):
    if event.raw_text.lower() in ['tpic set', 'عکس_موقت تنظیم']:
        await tpic_set(event)
    elif event.raw_text.lower() in ['tpic prv', 'عکس_موقت خصوصی']:
        await tpic_prv(event)


@client.on(events.NewMessage(pattern='^(ضد حذف|antidelete)$'))
async def toggle_anti_delete(event):
    if event.sender_id == admin_user_id:
        chat_id = event.chat_id
        if chat_id in anti_delete_chats:
            anti_delete_chats.remove(chat_id)
            await event.reply("**❈ Anti-delete disabled for this chat.**")
        else:
            anti_delete_chats.add(chat_id)
            await event.reply("**❈ Anti-delete enabled for this chat.**")

@client.on(events.NewMessage())
async def cache_private_messages(event):
    if event.sender_id == admin_user_id:
        return

    # Global anti-delete is intentionally PV-only. Groups, megagroups and
    # channels are never covered by the global switch. Per-chat /antidelete
    # remains available separately for chats the owner explicitly enables.
    if anti_delete_global_enabled:
        if not event.is_private:
            return
    elif event.chat_id not in anti_delete_chats:
        return

    try:
        sender = await event.get_sender()
        if sender and getattr(sender, 'bot', False):
            return
        name = getattr(sender, 'first_name', None) or "Unknown user"
        item = {
            'text': event.raw_text or '',
            'name': name,
            'time': event.date.strftime('%H:%M:%S'),
            'media_path': None,
            'is_private': bool(event.is_private),
            'chat_id': event.chat_id,
        }
        if event.media:
            try:
                path = await event.download_media(file=MEDIA_CACHE_DIR)
                if path:
                    item['media_path'] = path
            except Exception:
                logger.exception("Could not cache media for deleted-message recovery")
        saved_messages_cache[event.id] = item

        # Keep RAM/disk bounded. Oldest entries are discarded first.
        while len(saved_messages_cache) > MAX_DELETED_CACHE:
            old_id, old = saved_messages_cache.popitem()
            old_path = old.get('media_path')
            if old_path and os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    pass
    except Exception:
        logger.exception("cache_private_messages failed")

@client.on(events.MessageEdited())
async def track_edited_messages(event):
    if not event.is_private or event.sender_id == admin_user_id:
        return
    if not anti_delete_global_enabled and event.chat_id not in anti_delete_chats:
        return
    try:
        sender = await event.get_sender()
        if sender and getattr(sender, 'bot', False):
            return
        old = saved_messages_cache.get(event.id)
        old_text = old.get('text', 'Unknown') if old else 'Unknown'
        name = old.get('name', 'کاربر ناشناس') if old else (getattr(sender, 'first_name', None) or 'کاربر ناشناس')
        await _advanced_features.event_log(
            f"✏️ پیام ویرایش شد\nفرستنده: {name}\nساعت: {event.date.strftime('%H:%M:%S')}\nمتن قبلی: {old_text}\nمتن جدید: {event.raw_text or '(رسانه)'}"
        )
        if old and old.get('media_path') and event.media:
            try:
                os.remove(old['media_path'])
            except OSError:
                pass
        saved_messages_cache[event.id] = {
            'text': event.raw_text or '',
            'name': name,
            'time': event.date.strftime('%H:%M:%S'),
            'media_path': None,
            'is_private': True,
            'chat_id': event.chat_id,
        }
        if event.media:
            try:
                saved_messages_cache[event.id]['media_path'] = await event.download_media(file=MEDIA_CACHE_DIR)
            except Exception:
                logger.exception("Could not refresh edited media cache")
    except Exception:
        logger.exception("track_edited_messages failed")

@client.on(events.MessageDeleted())
async def track_deleted_messages(event):
    for msg_id in event.deleted_ids:
        data = saved_messages_cache.pop(msg_id, None)
        # Global anti-delete only stores PV messages. This extra check prevents
        # an old cache entry from accidentally making the global switch cover
        # groups/channels/bots.
        if anti_delete_global_enabled and (not data or not data.get('is_private', False)):
            continue
        if not anti_delete_global_enabled and event.chat_id not in anti_delete_chats:
            continue
        if not data:
            continue
        try:
            caption = (
                f"**❈ Message deleted\n"
                f"Sender: {data['name']}\n"
                f"Time: {data['time']}\n"
                f"Text: {data.get('text') or '(no text)'}**"
            )
            media_path = data.get('media_path')
            if media_path and os.path.exists(media_path):
                await _advanced_features.event_log(caption, media_path)
                os.remove(media_path)
            else:
                await _advanced_features.event_log(caption)
        except Exception:
            logger.exception("track_deleted_messages failed")
            media_path = data.get('media_path')
            if media_path and os.path.exists(media_path):
                try:
                    os.remove(media_path)
                except OSError:
                    pass
@client.on(events.NewMessage(pattern='(?i)(انگلیسیش کن|/entranslate)(.*)'))
async def translate_to_english(event):
    if event.sender_id != admin_user_id:
        return
    if event.is_reply:
        replied = await event.get_reply_message()
        text = replied.raw_text
    else:
        parts = event.raw_text.split(' ', 1)
        text = parts[1].strip() if len(parts) > 1 else None
    if not text:
        await event.reply("**❈ Reply to a message or provide text after the command.**")
        return
    translator = Translator()
    translated = translator.translate(text, dest='en')
    await event.reply(translated.text)

@client.on(events.NewMessage(pattern='^(timename on|timename off|timepic on|timepic off|mini on|bio on|bio off|bold on|default on|mono on|rnd on|heart on|heart off|rname on|rname off|see rname|see bio|see lname|farsi on|fancy on|circle on)$'))
async def handle_settings(event):
    await settings(event)

@client.on(events.NewMessage(pattern='(?i)^(subscript on|Subscript)$'))
async def font_subscript(event):
    if event.sender_id != admin_user_id:
        return
    with open('settings/mode.txt', 'w') as f:
        f.write('Subscript')
    await event.reply("**❈ Subscript font enabled.**")

@client.on(events.NewMessage(pattern='(?i)^(double on|دبل)$'))
async def font_double(event):
    if event.sender_id != admin_user_id:
        return
    with open('settings/mode.txt', 'w') as f:
        f.write('DoubleStruck')
    await event.reply("**❈ Double-struck font enabled.**")

@client.on(events.NewMessage(pattern='(?i)^(sansbold on|Sans_Bold)$'))
async def font_sansbold(event):
    if event.sender_id != admin_user_id:
        return
    with open('settings/mode.txt', 'w') as f:
        f.write('SansBold')
    await event.reply("**❈ Sans-bold font enabled.**")

@client.on(events.NewMessage(pattern='(?i)^(sans on|Sans)$'))
async def font_sans(event):
    if event.sender_id != admin_user_id:
        return
    with open('settings/mode.txt', 'w') as f:
        f.write('Sans')
    await event.reply("**❈ Sans font enabled.**")

@client.on(events.NewMessage(pattern='(?i)^(typewriter on|تایپ_رایتر)$'))
async def font_typewriter(event):
    if event.sender_id != admin_user_id:
        return
    with open('settings/mode.txt', 'w') as f:
        f.write('Typewriter')
    await event.reply("**❈ Typewriter font enabled.**")

@client.on(events.NewMessage(pattern='(?i)^(Spoiler ON|spoiler on)$'))
async def spoiler_on(event):
    global spoiler_mode_enabled
    if event.sender_id != admin_user_id:
        return
    spoiler_mode_enabled = True
    await event.reply("**❈ Spoiler mode enabled. Copy-to-Saved will use spoilers.**")

@client.on(events.NewMessage(pattern='(?i)^(Spoiler OFF|spoiler off)$'))
async def spoiler_off(event):
    global spoiler_mode_enabled
    if event.sender_id != admin_user_id:
        return
    spoiler_mode_enabled = False
    await event.reply("**❈ Spoiler mode disabled.**")

@client.on(events.NewMessage(pattern='(?i)^(کپی به سیو|savecopy)$'))
async def copy_to_saved(event):
    if event.sender_id != admin_user_id:
        return
    if not event.is_reply:
        await event.reply("**❈ Reply to a message and then use this command.**")
        return
    replied = await event.get_reply_message()
    sender = await replied.get_sender()
    sender_name = sender.first_name if sender and sender.first_name else "ناشناس"
    caption = f"**❈ Copied from: {sender_name}\nText: {replied.raw_text or '(no text)'}**"

    if spoiler_mode_enabled and replied.raw_text and not replied.media:
        entities = [MessageEntitySpoiler(offset=0, length=len(replied.raw_text))]
        await client.send_message('me', replied.raw_text, formatting_entities=entities)
    elif replied.media:
        await client.send_file('me', replied.media, caption=caption)
    else:
        await client.send_message('me', caption)

@client.on(events.NewMessage(pattern=r'(?i)^/(?:anim|انیمیشن)\s+(.+)$'))
async def animated_message(event):
    if event.sender_id != admin_user_id:
        return
    text = event.pattern_match.group(1).strip()[:500]
    msg = await event.reply('…')
    for i in range(1, len(text) + 1):
        try:
            await msg.edit(text[:i] + ' ▌')
            await asyncio.sleep(0.035)
        except Exception:
            break
    try:
        await msg.edit(text)
    except Exception:
        pass

@client.on(events.NewMessage(pattern=r'(?i)^(?:پنل|panel|/panel)$'))
async def show_panel(event):
    """Open the helper-bot panel through a stable Telegram deep link."""
    if event.sender_id != admin_user_id:
        return
    bot_name = helper_username.lstrip('@')
    panel_url = f"https://t.me/{bot_name}?start=panel"
    text = (
        f"**❈ Self Control Panel**\n\n"
        f"🤖 @{bot_name}\n\n"
        f"[❈ باز کردن پنل / Open Control Panel]({panel_url})"
    )
    await event.reply(text, link_preview=False)


PANEL_LANG_FILE = os.path.join('settings', 'panel_lang.txt')
if not os.path.exists(PANEL_LANG_FILE):
    with open(PANEL_LANG_FILE, 'w', encoding='utf-8') as f:
        f.write('fa')


def get_panel_lang():
    try:
        lang = open(PANEL_LANG_FILE, 'r', encoding='utf-8').read().strip().lower()
        return lang if lang in {'fa', 'en'} else 'fa'
    except Exception:
        return 'fa'


def set_panel_lang(lang):
    lang = 'en' if lang == 'en' else 'fa'
    with open(PANEL_LANG_FILE, 'w', encoding='utf-8') as f:
        f.write(lang)
    return lang


PANEL_I18N = {
    'fa': {
        'title': 'پنل کنترل سلف', 'choose': 'یک بخش را انتخاب کنید:', 'language': 'زبان',
        'fa': 'فارسی', 'en': 'English', 'support': 'پشتیبانی', 'back': 'بازگشت',
        'profile': 'پروفایل', 'fonts': 'فونت‌ها', 'messages': 'مدیریت پیام', 'security': 'امنیت',
        'privacy': 'حریم خصوصی', 'media': 'رسانه', 'utilities': 'ابزارها', 'statistics': 'آمار',
        'automation': 'اتوماسیون', 'system': 'سیستم', 'dashboard': 'داشبورد', 'notes': 'یادداشت‌ها',
        'fun': 'سرگرمی', 'smart': 'منشی و اتوماسیون', 'files': 'فایل‌ها', 'profiles': 'پروفایل مخاطبین', 'language_btn': 'English 🇬🇧',
        'profile_title': 'تنظیمات پروفایل', 'time_name_on': 'ساعت در نام روشن', 'time_name_off': 'ساعت در نام خاموش',
        'time_photo_on': 'ساعت در عکس روشن', 'time_photo_off': 'ساعت در عکس خاموش',
        'bio_on': 'بیوی پویا روشن', 'bio_off': 'بیوی پویا خاموش', 'heart_on': 'قلب روشن', 'heart_off': 'قلب خاموش',
        'random_name_on': 'نام تصادفی روشن', 'random_name_off': 'نام تصادفی خاموش',
        'font_title': 'تنظیمات فونت ساعت', 'bold': 'بولد', 'mono': 'مونو', 'mini': 'مینی', 'farsi': 'فارسی',
        'fancy': 'فانتزی', 'circle': 'دایره‌ای', 'subscript': 'زیرنویس', 'double': 'دوخطی',
        'sansbold': 'Sans Bold', 'sans': 'Sans', 'typewriter': 'تایپ‌رایتر', 'random': 'تصادفی', 'default': 'پیش‌فرض',
        'msg_title': 'مدیریت پیام', 'animation': 'پیام انیمیشنی', 'antidel_on': 'ضدحذف روشن', 'antidel_off': 'ضدحذف خاموش', 'antidel_chats': 'چت‌های ضدحذف',
        'security_title': 'امنیت', 'block': 'بلاک کاربر', 'unblock': 'آنبلاک کاربر', 'blocked_words': 'کلمات مسدود', 'watchlist': 'لیست مراقبت',
        'privacy_title': 'حریم خصوصی و اسپویلر', 'ghost_on': 'حالت مخفی روشن', 'ghost_off': 'حالت مخفی خاموش',
        'spoiler_on': 'اسپویلر روشن', 'spoiler_off': 'اسپویلر خاموش', 'media_title': 'مرکز رسانه',
        'media_desc': 'ابزارهای پاک‌سازی و بازیابی رسانه.', 'del_gif': 'حذف GIF', 'del_sticker': 'حذف استیکر',
        'del_photo': 'حذف عکس', 'del_video': 'حذف ویدیو', 'cache': 'کش ضدحذف', 'clear_cache': 'پاک‌کردن کش',
        'tools_title': 'مرکز ابزارها', 'tools_desc': 'ابزارهای سریع حساب و سیستم.', 'account': 'اطلاعات حساب', 'uptime': 'آپ‌تایم',
        'now': 'زمان فعلی', 'memory': 'حافظه', 'read_private': 'خواندن همه خصوصی', 'read_groups': 'خواندن همه گروه‌ها', 'read_channels': 'خواندن همه کانال‌ها',
        'auto_title': 'مرکز اتوماسیون', 'auto_desc': 'میانبرهای اتوماسیون و کنترل وضعیت.', 'antidel_status': 'وضعیت ضدحذف', 'reload': 'ریلود',
        'dashboard_title': 'داشبورد', 'unread': 'مرکز خوانده‌نشده', 'health': 'بررسی سلامت', 'refresh': 'تازه‌سازی',
        'notes_title': 'یادداشت‌ها', 'new_note': 'یادداشت جدید', 'clear_notes': 'پاک‌کردن یادداشت‌ها', 'no_notes': 'هنوز یادداشتی ثبت نشده.',
        'fun_title': 'سرگرمی', 'hafez': 'فال حافظ', 'stats_title': 'آمار و گزارش‌ها', 'today_stats': 'آمار امروز',
        'system_title': 'سیستم', 'ping': 'پینگ', 'logout': 'خروج از حساب', 'anti_delete_guide': 'راهنمای ضدحذف',
        'choose_lang': 'زبان پنل را انتخاب کنید:', 'smart_title': 'منشی و اتوماسیون', 'auto_read_on': 'خواندن خودکار روشن', 'auto_read_off': 'خواندن خودکار خاموش', 'auto_reply_on': 'پاسخ خودکار روشن', 'auto_reply_off': 'پاسخ خودکار خاموش', 'secretary_on': 'منشی روشن', 'secretary_off': 'منشی خاموش', 'away_on': 'حالت آفلاین روشن', 'away_off': 'حالت آفلاین خاموش', 'event_log': 'گپ اعلان‌ها', 'profiles_title': 'پروفایل مخاطبین', 'files_title': 'مدیریت فایل', 'rename_help': 'تغییر نام فایل', 'cover_help': 'تغییر کاور فایل', 'clock_title': 'استایل ساعت', 'clock_classic': 'ساعت کلاسیک', 'clock_bold': 'ساعت بولد', 'clock_circle': 'ساعت دایره‌ای', 'clock_double': 'ساعت دوبل', 'clock_farsi': 'ساعت فارسی', 'clock_mini': 'ساعت کوچک'
    },
    'en': {
        'title': 'Self Control Panel', 'choose': 'Choose a section:', 'language': 'Language',
        'fa': 'فارسی', 'en': 'English', 'support': 'Support', 'back': 'Back',
        'profile': 'Profile', 'fonts': 'Fonts', 'messages': 'Messages', 'security': 'Security',
        'privacy': 'Privacy', 'media': 'Media', 'utilities': 'Utilities', 'statistics': 'Statistics',
        'automation': 'Automation', 'system': 'System', 'dashboard': 'Dashboard', 'notes': 'Notes',
        'fun': 'Fun', 'smart': 'Smart Secretary', 'files': 'Files', 'profiles': 'Contact Profiles', 'language_btn': 'فارسی 🇮🇷',
        'profile_title': 'Profile Settings', 'time_name_on': 'Time in Name ON', 'time_name_off': 'Time in Name OFF',
        'time_photo_on': 'Time in Photo ON', 'time_photo_off': 'Time in Photo OFF',
        'bio_on': 'Dynamic Bio ON', 'bio_off': 'Dynamic Bio OFF', 'heart_on': 'Heart ON', 'heart_off': 'Heart OFF',
        'random_name_on': 'Random Name ON', 'random_name_off': 'Random Name OFF',
        'font_title': 'Time Font Settings', 'bold': 'Bold', 'mono': 'Mono', 'mini': 'Mini', 'farsi': 'Farsi',
        'fancy': 'Fancy', 'circle': 'Circle', 'subscript': 'Subscript', 'double': 'Double-struck',
        'sansbold': 'Sans-bold', 'sans': 'Sans', 'typewriter': 'Typewriter', 'random': 'Random', 'default': 'Default',
        'msg_title': 'Message Management', 'animation': 'Animated Message', 'antidel_on': 'Anti-delete ON', 'antidel_off': 'Anti-delete OFF', 'antidel_chats': 'Anti-delete Chats',
        'security_title': 'Security', 'block': 'Block User', 'unblock': 'Unblock User', 'blocked_words': 'Blocked Words', 'watchlist': 'Watchlist',
        'privacy_title': 'Privacy & Spoiler', 'ghost_on': 'Ghost ON', 'ghost_off': 'Ghost OFF',
        'spoiler_on': 'Spoiler ON', 'spoiler_off': 'Spoiler OFF', 'media_title': 'Media Center',
        'media_desc': 'Media cleanup and recovery tools.', 'del_gif': 'Delete GIFs', 'del_sticker': 'Delete Stickers',
        'del_photo': 'Delete Photos', 'del_video': 'Delete Videos', 'cache': 'Deleted Cache', 'clear_cache': 'Clear Cache',
        'tools_title': 'Utility Center', 'tools_desc': 'Fast account and system tools.', 'account': 'Account Info', 'uptime': 'Uptime',
        'now': 'Current Time', 'memory': 'Memory', 'read_private': 'Read All Private', 'read_groups': 'Read All Groups', 'read_channels': 'Read All Channels',
        'auto_title': 'Automation Center', 'auto_desc': 'Automation shortcuts and status controls.', 'antidel_status': 'Anti-delete Status', 'reload': 'Reload',
        'dashboard_title': 'Dashboard', 'unread': 'Unread Center', 'health': 'Health Check', 'refresh': 'Refresh',
        'notes_title': 'Notes', 'new_note': 'New Note', 'clear_notes': 'Clear Notes', 'no_notes': 'No notes yet.',
        'fun_title': 'Fun', 'hafez': 'Hafez Fortune', 'stats_title': 'Statistics & Reports', 'today_stats': "Today's Stats",
        'system_title': 'System', 'ping': 'Ping', 'logout': 'Log Out', 'anti_delete_guide': 'Anti-delete Guide',
        'choose_lang': 'Choose panel language:', 'smart_title': 'Smart Secretary & Automation', 'auto_read_on': 'Auto-read ON', 'auto_read_off': 'Auto-read OFF', 'auto_reply_on': 'Auto-reply ON', 'auto_reply_off': 'Auto-reply OFF', 'secretary_on': 'Secretary ON', 'secretary_off': 'Secretary OFF', 'away_on': 'Away Mode ON', 'away_off': 'Away Mode OFF', 'event_log': 'Event Log Chat', 'profiles_title': 'Contact Profiles', 'files_title': 'File Manager', 'rename_help': 'Rename a file', 'cover_help': 'Change file cover', 'clock_title': 'Clock Style', 'clock_classic': 'Classic clock', 'clock_bold': 'Bold clock', 'clock_circle': 'Circle clock', 'clock_double': 'Double clock', 'clock_farsi': 'Persian clock', 'clock_mini': 'Mini clock'
    }
}


def pt(key, lang=None):
    lang = lang or get_panel_lang()
    return PANEL_I18N[lang].get(key, PANEL_I18N['en'].get(key, key))


def _panel_main_buttons(lang=None):
    lang = lang or get_panel_lang()
    return [
        [pbtn(pt('profile', lang), b'menu_settings'), pbtn(pt('fonts', lang), b'menu_fonts')],
        [pbtn(pt('messages', lang), b'menu_msg'), pbtn(pt('security', lang), b'menu_security')],
        [pbtn(pt('privacy', lang), b'menu_ghost'), pbtn(pt('media', lang), b'menu_media')],
        [pbtn(pt('utilities', lang), b'menu_tools'), pbtn(pt('statistics', lang), b'menu_stats')],
        [pbtn(pt('automation', lang), b'menu_auto'), pbtn(pt('system', lang), b'menu_system')],
        [pbtn(pt('dashboard', lang), b'menu_dashboard'), pbtn(pt('notes', lang), b'menu_notes')],
        [pbtn(pt('smart', lang), b'menu_smart'), pbtn(pt('files', lang), b'menu_files')],
        [pbtn(pt('profiles', lang), b'menu_profiles'), pbtn(pt('fun', lang), b'menu_fun')],
        [pbtn(pt('language_btn', lang), b'panel_language')],
        [support_button()]
    ]


def panel_language_buttons():
    return [
        [pbtn('🇮🇷 فارسی', b'panel_lang_fa', 'primary'), pbtn('🇬🇧 English', b'panel_lang_en', 'primary')],
        [pbtn(pt('back'), b'menu_main', 'primary')]
    ]


def panel_menu(data, lang=None):
    lang = lang or get_panel_lang()
    if data == 'menu_media':
        return f"**❈ {pt('media_title', lang)}**\n\n{pt('media_desc', lang)}", [
            [pbtn(pt('del_gif', lang), b'p_del_gif', 'danger'), pbtn(pt('del_sticker', lang), b'p_del_sticker', 'danger')],
            [pbtn(pt('del_photo', lang), b'p_del_photo', 'danger'), pbtn(pt('del_video', lang), b'p_del_video', 'danger')],
            [pbtn(pt('cache', lang), b'p_cache_info'), pbtn(pt('clear_cache', lang), b'p_cache_clear', 'danger')],
            [pbtn(pt('back', lang), b'menu_main')]
        ]
    if data == 'menu_tools':
        return f"**❈ {pt('tools_title', lang)}**\n\n{pt('tools_desc', lang)}", [
            [pbtn(pt('account', lang), b'p_account'), pbtn(pt('uptime', lang), b'p_uptime')],
            [pbtn(pt('now', lang), b'p_now'), pbtn(pt('memory', lang), b'p_mem')],
            [pbtn(pt('read_private', lang), b'p_read_pv')], [pbtn(pt('read_groups', lang), b'p_read_group')],
            [pbtn(pt('read_channels', lang), b'p_read_channel')], [pbtn(pt('back', lang), b'menu_main')]
        ]
    if data == 'menu_auto':
        return f"**❈ {pt('auto_title', lang)}**\n\n{pt('auto_desc', lang)}", [
            [pbtn(pt('antidel_status', lang), b'p_antidelete_list'), pbtn(pt('watchlist', lang), b'p_watch_list')],
            [pbtn(pt('blocked_words', lang), b'p_words_list'), pbtn(pt('reload', lang), b'p_reload')],
            [pbtn(pt('back', lang), b'menu_main')]
        ]
    if data == 'menu_dashboard':
        return None, None
    if data == 'menu_notes':
        return None, None
    if data == 'menu_settings':
        return f"**❈ {pt('profile_title', lang)}**", [
            [pbtn(pt('time_name_on', lang), b'p_timename_on', 'success'), pbtn(pt('time_name_off', lang), b'p_timename_off', 'danger')],
            [pbtn(pt('time_photo_on', lang), b'p_timepic_on', 'success'), pbtn(pt('time_photo_off', lang), b'p_timepic_off', 'danger')],
            [pbtn(pt('bio_on', lang), b'p_bio_on', 'success'), pbtn(pt('bio_off', lang), b'p_bio_off', 'danger')],
            [pbtn(pt('heart_on', lang), b'p_heart_on', 'success'), pbtn(pt('heart_off', lang), b'p_heart_off', 'danger')],
            [pbtn(pt('random_name_on', lang), b'p_rname_on', 'success'), pbtn(pt('random_name_off', lang), b'p_rname_off', 'danger')],
            [pbtn(pt('back', lang), b'menu_main')]
        ]
    if data == 'menu_fonts':
        return f"**❈ {pt('font_title', lang)}**", [
            [pbtn(pt('bold', lang), b'p_font_bold'), pbtn(pt('mono', lang), b'p_font_mono')],
            [pbtn(pt('mini', lang), b'p_font_mini'), pbtn(pt('farsi', lang), b'p_font_farsi')],
            [pbtn(pt('fancy', lang), b'p_font_fancy'), pbtn(pt('circle', lang), b'p_font_circle')],
            [pbtn(pt('subscript', lang), b'p_font_subscript'), pbtn(pt('double', lang), b'p_font_double')],
            [pbtn(pt('sansbold', lang), b'p_font_sansbold'), pbtn(pt('sans', lang), b'p_font_sans')],
            [pbtn(pt('typewriter', lang), b'p_font_typewriter'), pbtn(pt('random', lang), b'p_font_rnd')],
            [pbtn(pt('default', lang), b'p_font_default')], [pbtn(pt('back', lang), b'menu_main')]
        ]
    if data == 'menu_msg':
        return f"**❈ {pt('msg_title', lang)}**", [
            [pbtn('🛡 ضدحذف PV همه ON', b'p_antidelete_global_on', 'success'), pbtn('🛡 ضدحذف PV همه OFF', b'p_antidelete_global_off', 'danger')],
            [pbtn(pt('antidel_on', lang), b'p_antidelete_on', 'success'), pbtn(pt('antidel_off', lang), b'p_antidelete_off', 'danger')],
            [pbtn(pt('antidel_chats', lang), b'p_antidelete_list')], [pbtn(pt('anti_delete_guide', lang), b'p_antidelete_help')], [pbtn(pt('animation', lang), b'p_anim_help')],
            [pbtn(pt('back', lang), b'menu_main')]
        ]
    if data == 'menu_security':
        return f"**❈ {pt('security_title', lang)}**", [
            [pbtn(pt('block', lang), b'p_block_start', 'danger'), pbtn(pt('unblock', lang), b'p_unblock_start', 'success')],
            [pbtn(pt('blocked_words', lang), b'p_words_list')], [pbtn(pt('watchlist', lang), b'p_watch_list')], [pbtn(pt('back', lang), b'menu_main')]
        ]
    if data == 'menu_ghost':
        return f"**❈ {pt('privacy_title', lang)}**", [
            [pbtn(pt('ghost_on', lang), b'p_ghost_on', 'success'), pbtn(pt('ghost_off', lang), b'p_ghost_off', 'danger')],
            [pbtn(pt('spoiler_on', lang), b'p_spoiler_on', 'success'), pbtn(pt('spoiler_off', lang), b'p_spoiler_off', 'danger')],
            [pbtn(pt('back', lang), b'menu_main')]
        ]
    if data == 'menu_smart':
        return f"**❈ {pt('smart_title', lang)}**", [
            [pbtn(pt('auto_read_on', lang), b'p_auto_read_on', 'success'), pbtn(pt('auto_read_off', lang), b'p_auto_read_off', 'danger')],
            [pbtn(pt('auto_reply_on', lang), b'p_auto_reply_on', 'success'), pbtn(pt('auto_reply_off', lang), b'p_auto_reply_off', 'danger')],
            [pbtn(pt('secretary_on', lang), b'p_secretary_on', 'success'), pbtn(pt('secretary_off', lang), b'p_secretary_off', 'danger')],
            [pbtn(pt('away_on', lang), b'p_away_on', 'success'), pbtn(pt('away_off', lang), b'p_away_off', 'danger')],
            [pbtn(pt('event_log', lang), b'p_set_log_chat')],
            [pbtn(pt('back', lang), b'menu_main')]
        ]
    if data == 'menu_files':
        return f"**❈ {pt('files_title', lang)}**", [
            [pbtn(pt('rename_help', lang), b'p_rename_help'), pbtn(pt('cover_help', lang), b'p_cover_help')],
            [pbtn(pt('back', lang), b'menu_main')]
        ]
    if data == 'menu_profiles':
        return f"**❈ {pt('profiles_title', lang)}**\n\nAutomatic contact/profile snapshots are checked every 5 minutes.", [
            [pbtn(pt('event_log', lang), b'p_set_log_chat')],
            [pbtn(pt('back', lang), b'menu_main')]
        ]
    if data == 'menu_fun':
        return f"**❈ {pt('fun_title', lang)}**", [[pbtn(pt('hafez', lang), b'p_hafez')], [pbtn(pt('back', lang), b'menu_main')]]
    if data == 'menu_stats':
        return f"**❈ {pt('stats_title', lang)}**", [[pbtn(pt('today_stats', lang), b'p_stats_today'), pbtn(pt('memory', lang), b'p_mem')], [pbtn(pt('back', lang), b'menu_main')]]
    if data == 'menu_system':
        return f"**❈ {pt('system_title', lang)}**", [[pbtn(pt('ping', lang), b'p_ping'), pbtn(pt('reload', lang), b'p_reload')], [pbtn(pt('logout', lang), b'p_logout_confirm', 'danger')], [pbtn(pt('back', lang), b'menu_main')]]
    return None, None


@client.on(events.CallbackQuery)
async def self_panel_callback(event):
    """Handle buttons rendered by /panel on the self client."""
    global ghost_mode_enabled, spoiler_mode_enabled, anti_delete_global_enabled
    if event.sender_id != admin_user_id:
        return
    try:
        data = event.data.decode("utf-8")

        if data == "menu_main":
            await event.edit("**❈ Self Control Panel**\n\nChoose a section:", buttons=_panel_main_buttons())
            return

        if data == "menu_settings":
            buttons = [
                [pbtn("Time in Name ON", b"p_timename_on", "success"), pbtn("Time in Name OFF", b"p_timename_off", "danger")],
                [pbtn("Time in Photo ON", b"p_timepic_on", "success"), pbtn("Time in Photo OFF", b"p_timepic_off", "danger")],
                [pbtn("Dynamic Bio ON", b"p_bio_on", "success"), pbtn("Dynamic Bio OFF", b"p_bio_off", "danger")],
                [pbtn("Heart ON", b"p_heart_on", "success"), pbtn("Heart OFF", b"p_heart_off", "danger")],
                [pbtn("Random Name ON", b"p_rname_on", "success"), pbtn("Random Name OFF", b"p_rname_off", "danger")],
                [pbtn("Back", b"menu_main", "primary")],
            ]
            await event.edit("Profile Settings", buttons=buttons)
            return

        if data == "menu_fonts":
            buttons = [
                [pbtn("Bold", b"p_font_bold", "primary"), pbtn("Mono", b"p_font_mono", "primary")],
                [pbtn("Mini", b"p_font_mini", "primary"), pbtn("Farsi", b"p_font_farsi", "primary")],
                [pbtn("Fancy", b"p_font_fancy", "primary"), pbtn("Circle", b"p_font_circle", "primary")],
                [pbtn("Subscript", b"p_font_subscript", "primary"), pbtn("Double-struck", b"p_font_double", "primary")],
                [pbtn("Sans-bold", b"p_font_sansbold", "primary"), pbtn("Sans", b"p_font_sans", "primary")],
                [pbtn("Typewriter", b"p_font_typewriter", "primary"), pbtn("Random", b"p_font_rnd", "primary")],
                [pbtn("Default", b"p_font_default", "primary")],
                [pbtn("Back", b"menu_main", "primary")],
            ]
            await event.edit("**❈ Time Font Settings**", buttons=buttons)
            return

        if data == "menu_msg":
            buttons = [
                [pbtn("🛡 Anti-delete PV ALL ON", b"p_antidelete_global_on", "success"), pbtn("🛡 Anti-delete PV ALL OFF", b"p_antidelete_global_off", "danger")],
                [pbtn("Anti-delete this chat", b"p_antidelete_toggle", "primary")],
                [pbtn("Anti-delete chats", b"p_antidelete_list", "primary")],
                [pbtn("Anti-delete Guide", b"p_antidelete_help", "primary")],
                [pbtn("Back", b"menu_main", "primary")],
            ]
            await event.edit("Message Management", buttons=buttons)
            return

        if data == "menu_security":
            buttons = [
                [pbtn("Block User", b"p_block_start", "danger"), pbtn("Unblock User", b"p_unblock_start", "success")],
                [pbtn("Blocked Words", b"p_words_list", "primary")],
                [pbtn("Watchlist", b"p_watch_list", "primary")],
                [pbtn("Back", b"menu_main", "primary")],
            ]
            await event.edit("Security", buttons=buttons)
            return

        if data == "menu_ghost":
            buttons = [
                [pbtn("Ghost ON", b"p_ghost_on", "success"), pbtn("Ghost OFF", b"p_ghost_off", "danger")],
                [pbtn("Spoiler ON", b"p_spoiler_on", "success"), pbtn("Spoiler OFF", b"p_spoiler_off", "danger")],
                [pbtn("Back", b"menu_main", "primary")],
            ]
            await event.edit("**❈ Privacy & Spoiler**", buttons=buttons)
            return

        if data == "menu_fun":
            await event.edit("**❈ Fun**", buttons=[
                [pbtn("Hafez Fortune", b"p_hafez", "primary")],
                [pbtn("Back", b"menu_main", "primary")],
            ])
            return

        if data == "menu_stats":
            await event.edit("**❈ Statistics & Reports**", buttons=[
                [pbtn("Today's Stats", b"p_stats_today", "primary"), pbtn("Memory Usage", b"p_mem", "primary")],
                [pbtn("Back", b"menu_main", "primary")],
            ])
            return

        if data == "menu_system":
            await event.edit("**❈ System**", buttons=[
                [pbtn("Ping", b"p_ping", "primary"), pbtn("Reload", b"p_reload", "primary")],
                [pbtn("Log Out", b"p_logout_confirm", "danger")],
                [pbtn("Back", b"menu_main", "primary")],
            ])
            return

        profile_actions = {
            "p_timename_on": ("settings/time.txt", "True", "Time in Name enabled"),
            "p_timename_off": ("settings/time.txt", "False", "Time in Name disabled"),
            "p_timepic_on": ("settings/timepic.txt", "True", "Time in Photo enabled"),
            "p_timepic_off": ("settings/timepic.txt", "False", "Time in Photo disabled"),
            "p_bio_on": ("settings/bioinfo.txt", "True", "Dynamic Bio enabled"),
            "p_bio_off": ("settings/bioinfo.txt", "False", "Dynamic Bio disabled"),
            "p_heart_on": ("settings/heart.txt", "True", "Heart mode enabled"),
            "p_heart_off": ("settings/heart.txt", "False", "Heart mode disabled"),
            "p_rname_on": ("settings/rnamest.txt", "True", "Random name mode enabled"),
            "p_rname_off": ("settings/rnamest.txt", "False", "Random name mode disabled"),
        }
        if data in profile_actions:
            path, value, message = profile_actions[data]
            with open(path, "w", encoding="utf-8") as f:
                f.write(value)
            if data == "p_timename_on":
                await client(UpdateProfileRequest(last_name=current_time_str))
            elif data == "p_timename_off":
                await client(UpdateProfileRequest(last_name=""))
            elif data == "p_bio_off":
                await client(UpdateProfileRequest(about=""))
            await event.answer("**❈ " + message + "**", alert=True)
            return

        font_actions = {
            "p_font_bold": "Bold", "p_font_mono": "Mono", "p_font_mini": "Mini",
            "p_font_farsi": "Farsi", "p_font_fancy": "Fancy", "p_font_circle": "Circle",
            "p_font_subscript": "Subscript", "p_font_double": "DoubleStruck", "p_font_sansbold": "SansBold",
            "p_font_sans": "Sans", "p_font_typewriter": "Typewriter", "p_font_default": "Default", "p_font_rnd": "rnd",
        }
        if data in font_actions:
            with open("settings/mode.txt", "w", encoding="utf-8") as f:
                f.write(font_actions[data])
            await event.answer("**❈ Font changed.**", alert=True)
            return

        if data == "p_antidelete_global_on":
            anti_delete_global_enabled = True
            set_global_anti_delete(True)
            await event.answer("**❈ Global anti-delete enabled for all chats.**", alert=True)
            return

        if data == "p_antidelete_global_off":
            anti_delete_global_enabled = False
            set_global_anti_delete(False)
            await event.answer("**❈ Global anti-delete disabled.**", alert=True)
            return

        if data == "p_antidelete_toggle":
            chat_id = event.chat_id
            if chat_id in anti_delete_chats:
                anti_delete_chats.remove(chat_id)
                msg = "**❈ Anti-delete disabled for this chat.**"
            else:
                anti_delete_chats.add(chat_id)
                msg = "**❈ Anti-delete enabled for this chat.**"
            await event.answer(msg, alert=True)
            return

        if data == "p_antidelete_list":
            await event.answer(f"**❈ Global PV anti-delete: {'ON' if anti_delete_global_enabled else 'OFF'} | Per-chat: {len(anti_delete_chats)}**", alert=True)
            return
        if data == "p_antidelete_help":
            await event.answer("**❈ To enable anti-delete in a chat, send /antidelete in that chat. This panel is open in Saved Messages.**", alert=True)
            return

        if data == "p_ghost_on":
            ghost_mode_enabled = True
            await event.answer("**❈ Ghost mode enabled.**", alert=True)
            return
        if data == "p_ghost_off":
            ghost_mode_enabled = False
            await event.answer("**❈ Ghost mode disabled.**", alert=True)
            return
        if data == "p_spoiler_on":
            spoiler_mode_enabled = True
            await event.answer("**❈ Spoiler mode enabled.**", alert=True)
            return
        if data == "p_spoiler_off":
            spoiler_mode_enabled = False
            await event.answer("**❈ Spoiler mode disabled.**", alert=True)
            return

        if data == "p_words_list":
            await event.answer(("\n".join(blocked_words) if blocked_words else "Empty list.")[:200], alert=True)
            return
        if data == "p_watch_list":
            await event.answer(("\n".join(watch_keywords) if watch_keywords else "Empty list.")[:200], alert=True)
            return

        if data in ("p_block_start", "p_unblock_start"):
            pending_input[admin_user_id] = "block" if data == "p_block_start" else "unblock"
            await event.answer("**❈ Send the numeric ID or @username here in a separate message.**", alert=True)
            return

        if data == "p_hafez":
            try:
                response = requests.get("https://hafez-dxle.onrender.com/fal", timeout=15)
                response.raise_for_status()
                hdata = response.json()
                interpretation = hdata.get("interpreter", "No fortune found.")
                await event.answer(interpretation[:200], alert=True)
            except Exception as e:
                await event.answer(f"**❈ Error getting fortune: {e}**", alert=True)
            return

        if data == "p_stats_today":
            await event.answer(f"**❈ Messages: {daily_stats['messages_today']}\nUsers: {len(daily_stats['unique_senders'])}**", alert=True)
            return
        if data == "p_mem":
            await event.answer(f"**❈ Memory usage: {psutil.virtual_memory().percent}%**", alert=True)
            return
        if data == "p_ping":
            await event.answer("**❈ Self client is online and responding.**", alert=True)
            return
        if data == "p_reload":
            await client.send_message("me", "**❈ Reloading from panel...**")
            await event.answer("**❈ Reloading...**", alert=True)
            await asyncio.sleep(0.5)
            os.execv(sys.executable, [sys.executable] + sys.argv)
            return
        if data == "p_logout_confirm":
            await event.answer("**❈ To actually log out, use /logout directly.**", alert=True)
            return

        await event.answer("**❈ This option is not connected to a direct feature yet.**", alert=True)
    except Exception as e:
        logger.exception("self_panel_callback failed")
        try:
            await event.answer(f"**❈ Panel error: {str(e)[:180]}**", alert=True)
        except Exception:
            pass


@client.on(events.NewMessage)
async def self_panel_pending_input(event):
    if event.sender_id != admin_user_id or not event.is_private:
        return
    action = pending_input.get(admin_user_id)
    if not action or event.raw_text.startswith('/'):
        return
    # Only consume explicit input in Saved Messages, not arbitrary private chats.
    if event.chat_id != admin_user_id:
        return
    target = event.raw_text.strip()
    try:
        entity = await client.get_entity(target)
        if action == "block":
            await client(functions.contacts.BlockRequest(entity.id))
            await event.reply(result_ok(f"User {target} blocked."))
        elif action == "unblock":
            await client(functions.contacts.UnblockRequest(entity.id))
            await event.reply(result_ok(f"User {target} unblocked."))
    except Exception as e:
        await event.reply(f"**❈ User not found or operation failed: {e}**")
    finally:
        pending_input.pop(admin_user_id, None)

@client.on(events.NewMessage(pattern='(?i)(Farsiش کن|/fatranslate)(.*)'))
async def translate_to_farsi(event):
    if event.sender_id != admin_user_id:
        return
    if event.is_reply:
        replied = await event.get_reply_message()
        text = replied.raw_text
    else:
        parts = event.raw_text.split(' ', 1)
        text = parts[1].strip() if len(parts) > 1 else None
    if not text:
        await event.reply("**❈ Reply to a message or provide text after the command.**")
        return
    translator = Translator()
    translated = translator.translate(text, dest='fa')
    await event.reply(translated.text)

daily_stats = {'messages_today': 0, 'unique_senders': set()}

@client.on(events.NewMessage)
async def track_daily_stats(event):
    if event.is_private and event.sender_id != admin_user_id:
        daily_stats['messages_today'] += 1
        daily_stats['unique_senders'].add(event.sender_id)

async def send_daily_report():
    while True:
        now = datetime.datetime.now(timezone)
        target_time = now.replace(hour=23, minute=59, second=0, microsecond=0)
        if now >= target_time:
            target_time += datetime.timedelta(days=1)
        wait_seconds = (target_time - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        report = f"""📊 گزارش روزانه

📨 تعداد پیام‌های دریافتی: {daily_stats['messages_today']}
👥 تعداد کاربران متفاوت: {len(daily_stats['unique_senders'])}
🗑 چت‌های ضد حذف فعال: {len(anti_delete_chats)}"""
        await client.send_message('me', report)

        daily_stats['messages_today'] = 0
        daily_stats['unique_senders'] = set()

blocked_words = ["کص مادرت"]

@client.on(events.NewMessage)
async def auto_block_words(event):
    if event.is_private and event.sender_id != admin_user_id:
        text = event.raw_text.lower() if event.raw_text else ""
        for word in blocked_words:
            if word.lower() in text:
                await client(functions.contacts.BlockRequest(event.sender_id))
                await client.send_message(admin_user_id, result_ok(f"User {event.sender_id} was blocked for using a blocked word."))
                break

@client.on(events.NewMessage(pattern='(?i)^(اضافه کلمه|addword) (.+)'))
async def add_blocked_word(event):
    if event.sender_id == admin_user_id:
        word = event.raw_text.split(' ', 1)[1].strip()
        blocked_words.append(word)
        await event.reply(f"**❈ Word \"{word}\" added to the blocked-word list.**")

@client.on(events.NewMessage(pattern='(?i)^(لیست کلمات|listwords)$'))
async def list_blocked_words(event):
    if event.sender_id == admin_user_id:
        if blocked_words:
            await event.reply("**❈ Blocked words:**\n" + "\n".join(blocked_words))
        else:
            await event.reply("**❈ The list is empty.**")

@client.on(events.NewMessage(pattern='(?i)^(ویس به متن|voicetotext)$'))
async def voice_to_text(event):
    if event.sender_id != admin_user_id:
        return
    if not event.is_reply:
        await event.reply("**❈ Reply to a voice message and then use this command.**")
        return
    replied = await event.get_reply_message()
    if not replied.voice:
        await event.reply("**❈ The replied message is not a voice message.**")
        return

    ogg_path = await replied.download_media()
    wav_path = ogg_path.replace('.ogg', '.wav')
    AudioSegment.from_ogg(ogg_path).export(wav_path, format='wav')

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data, language='fa-IR')
        await event.reply(f"**❈ Voice transcription:**\n\n{text}")
    except sr.UnknownValueError:
        await event.reply("**❈ I could not recognize the audio.**")
    except Exception as e:
        await event.reply(f"**❈ Error: {e}**")
    finally:
        os.remove(ogg_path)
        os.remove(wav_path)

@client.on(events.NewMessage(pattern='(?i)^(فال حافظ|falhafez)$'))
async def send_hafez_fortune(event):
    try:
        response = requests.get('https://hafez-dxle.onrender.com/fal')
        data = response.json()
        title = data.get('title', '')
        interpretation = data.get('interpreter', 'فالی پیدا نشد.')
        await event.reply(f"**❈ Hafez Fortune: {title}\n\n{interpretation}**")
    except Exception as e:
        await event.reply(f"**❈ Error getting fortune: {e}**")

@client.on(events.NewMessage(pattern='(?i)^(بلاک|block)$'))
async def block_user(event):
    if event.sender_id != admin_user_id:
        return
    if not event.is_reply:
        await event.reply("**❈ Reply to the target user's message.**")
        return
    replied = await event.get_reply_message()
    target_id = replied.sender_id
    await client(functions.contacts.BlockRequest(target_id))
    await event.reply(result_ok(f"User {target_id} blocked."))

@client.on(events.NewMessage(pattern='(?i)^(آنبلاک|unblock)$'))
async def unblock_user(event):
    if event.sender_id != admin_user_id:
        return
    if not event.is_reply:
        await event.reply("**❈ Reply to the target user's message.**")
        return
    replied = await event.get_reply_message()
    target_id = replied.sender_id
    await client(functions.contacts.UnblockRequest(target_id))
    await event.reply(result_ok(f"User {target_id} unblocked."))

@client.on(events.NewMessage(pattern='(?i)^(حذف|delmsg)$'))
async def delete_replied_message(event):
    if event.sender_id != admin_user_id:
        return
    if not event.is_reply:
        await event.reply("**❈ Reply to the message you want to delete.**")
        return
    replied = await event.get_reply_message()
    await replied.delete()
    await event.delete()

@client.on(events.NewMessage(pattern='(?i)^(گوست|ghost) (.+)$'))
async def ghost_read(event):
    if event.sender_id != admin_user_id:
        return
    target = event.pattern_match.group(2).strip()
    try:
        entity = await client.get_entity(target)
    except Exception:
        try:
            entity = await client.get_entity(int(target))
        except Exception as e:
            await event.reply(f"**❈ User not found: {e}**")
            return

    dialog = None
    async for d in client.iter_dialogs():
        if d.entity.id == entity.id:
            dialog = d
            break

    if not dialog or dialog.unread_count == 0:
        await event.reply("**❈ There are no unread messages from this user.**")
        return

    unread_count = dialog.unread_count
    messages = []
    async for msg in client.iter_messages(entity, limit=unread_count):
        messages.append(msg)
    messages.reverse()

    sender_name = getattr(entity, 'first_name', None) or getattr(entity, 'title', None) or str(entity.id)
    report = f"👻 پیام‌های خونده‌نشده از {sender_name}:\n\n"
    for msg in messages:
        text = msg.raw_text or "(media without text)"
        report += f"• {text}\n"

    await client.send_message('me', report)
    await event.reply("**❈ Messages were sent without marking them as seen.**")

@client.on(events.NewMessage(pattern='(?i)^(ghost on)$'))
async def ghost_mode_on_text(event):
    global ghost_mode_enabled
    if event.sender_id != admin_user_id:
        return
    ghost_mode_enabled = True
    await event.reply("**❈ Ghost mode enabled.**")

@client.on(events.NewMessage(pattern='(?i)^(ghost off)$'))
async def ghost_mode_off_text(event):
    global ghost_mode_enabled
    if event.sender_id != admin_user_id:
        return
    ghost_mode_enabled = False
    await event.reply("**❈ Ghost mode disabled.**")

watch_keywords = []

@client.on(events.NewMessage(pattern='(?i)^(اضافه کلمه دیده‌بان|addwatch) (.+)$'))
async def add_watch_keyword(event):
    if event.sender_id != admin_user_id or not event.is_private:
        return
    keyword = event.pattern_match.group(2).strip()
    watch_keywords.append(keyword.lower())
    await event.reply(f"**❈ Keyword \"{keyword}\" added to the watchlist.**")

@client.on(events.NewMessage(pattern='(?i)^(حذف کلمه دیده‌بان|delwatch) (.+)$'))
async def remove_watch_keyword(event):
    if event.sender_id != admin_user_id or not event.is_private:
        return
    keyword = event.pattern_match.group(2).strip().lower()
    if keyword in watch_keywords:
        watch_keywords.remove(keyword)
        await event.reply(f"**❈ Keyword \"{keyword}\" removed from the watchlist.**")
    else:
        await event.reply("**❈ This keyword was not in the list.**")

@client.on(events.NewMessage(pattern='(?i)^(لیست دیده‌بان|listwatch)$'))
async def list_watch_keywords(event):
    if event.sender_id == admin_user_id and event.is_private:
        if watch_keywords:
            await event.reply("**❈ Watchlist:**\n" + "\n".join(watch_keywords))
        else:
            await event.reply("**❈ The list is empty.**")

@client.on(events.NewMessage)
async def group_watcher(event):
    if event.sender_id != admin_user_id and event.raw_text and watch_keywords:
        text_lower = event.raw_text.lower()
        for keyword in watch_keywords:
            if keyword in text_lower:
                chat = await event.get_chat()
                sender = await event.get_sender()
                sender_name = sender.first_name if sender and sender.first_name else "ناشناس"
                chat_name = getattr(chat, 'title', None) or getattr(chat, 'first_name', 'خصوصی')
                await client.send_message(
                    admin_user_id,
                    f"👁 کلمه دیده‌بانی «{keyword}» شنیده شد!\n\n📍 چت: {chat_name}\n👤 فرستنده: {sender_name}\n💬 متن: {event.raw_text}"
                )
                break

@client.on(events.NewMessage(pattern='(?i)^(اعلام وضعیت|status)$'))
async def show_status(event):
    if event.sender_id != admin_user_id:
        return
    def read_status(path):
        try:
            with open(path, 'r') as f:
                return f.read().strip()
        except:
            return "Unknown"
    timename = "🟢 روشن" if read_status('settings/time.txt') == 'True' else "🔴 خاموش"
    timepic = "🟢 روشن" if read_status('settings/timepic.txt') == 'True' else "🔴 خاموش"
    bio = "🟢 روشن" if read_status('settings/bioinfo.txt') == 'True' else "🔴 خاموش"
    heart = "🟢 روشن" if read_status('settings/heart.txt') == 'True' else "🔴 خاموش"
    rname = "🟢 روشن" if read_status('settings/rnamest.txt') == 'True' else "🔴 خاموش"
    mode = read_status('settings/mode.txt')
    ghost = "🟢 روشن" if ghost_mode_enabled else "🔴 خاموش"
    spoiler = "🟢 روشن" if spoiler_mode_enabled else "🔴 خاموش"
    status_lines = []
    status_lines.append("**❈ Self Client Status**")
    status_lines.append("")
    status_lines.append("**❈ Profile Settings**")
    status_lines.append(f"Time in Name: {timename}")
    status_lines.append(f"Time in Photo: {timepic}")
    status_lines.append(f"Dynamic Bio: {bio}")
    status_lines.append(f"Heart Mode: {heart}")
    status_lines.append(f"Random Name: {rname}")
    status_lines.append(f"Current Font: {mode}")
    status_lines.append("")
    status_lines.append("**❈ Security**")
    status_lines.append(f"Ghost Mode: {ghost}")
    status_lines.append(f"Spoiler Mode: {spoiler}")
    status_lines.append(f"Anti-delete Chats: {len(anti_delete_chats)}")
    status_lines.append(f"Blocked Words: {len(blocked_words)}")
    status_lines.append(f"Watchlist Words: {len(watch_keywords)}")
    status_lines.append("")
    status_lines.append("**❈ Today's Statistics**")
    status_lines.append(f"Received Messages: {daily_stats['messages_today']}")
    status_lines.append(f"Unique Users: {len(daily_stats['unique_senders'])}")
    status_lines.append("")
    status_lines.append("**❈ System**")
    status_lines.append(f"**❈ Memory usage: {psutil.virtual_memory().percent}%**")
    await event.reply("\n".join(status_lines))

@bot_client.on(events.InlineQuery)
async def bot_inline_panel(event):
    if event.sender_id != admin_user_id:
        await event.answer([])
        return
    lang = get_panel_lang()
    result = event.builder.article(
        title=f"❈ {pt('title', lang)}",
        description=pt('choose', lang),
        text=f"**❈ {pt('title', lang)}**\n\n{pt('choose', lang)}",
        buttons=_panel_main_buttons(lang)
    )
    await event.answer([result])


@bot_client.on(events.NewMessage(pattern=r'(?i)^(/panel(?:@\w+)?|/panel_en(?:@\w+)?|/panel_fa(?:@\w+)?|/start(?:\s+panel)?)$'))
async def bot_show_panel(event):
    if event.sender_id != admin_user_id:
        return
    command = (event.raw_text or '').strip().lower()
    if command.startswith('/panel@'):
        try:
            await event.delete()
        except Exception:
            pass
        command = '/panel'
    if command == '/panel_en':
        set_panel_lang('en')
    elif command == '/panel_fa':
        set_panel_lang('fa')
    lang = get_panel_lang()
    await event.reply(f"**❈ {pt('title', lang)}**\n\n{pt('choose', lang)}", buttons=_panel_main_buttons(lang))


@bot_client.on(events.CallbackQuery)
async def bot_handle_clicks(event):
    global ghost_mode_enabled, spoiler_mode_enabled, anti_delete_global_enabled
    if event.sender_id != admin_user_id:
        return
    data = event.data.decode('utf-8')
    lang = get_panel_lang()

    if data == 'panel_language':
        await event.edit(f"**❈ {pt('language', lang)}**\n\n{pt('choose_lang', lang)}", buttons=panel_language_buttons())
        return
    if data == 'panel_lang_fa':
        lang = set_panel_lang('fa')
        await event.edit(f"**❈ {pt('title', lang)}**\n\n{pt('choose', lang)}", buttons=_panel_main_buttons(lang))
        return
    if data == 'panel_lang_en':
        lang = set_panel_lang('en')
        await event.edit(f"**❈ {pt('title', lang)}**\n\n{pt('choose', lang)}", buttons=_panel_main_buttons(lang))
        return

    if data == 'menu_main':
        await event.edit(f"**❈ {pt('title', lang)}**\n\n{pt('choose', lang)}", buttons=_panel_main_buttons(lang))
        return

    if data == 'menu_dashboard':
        rows = await unread_summary()
        unread_total = sum(count for count, _, _ in rows)
        try:
            cache_files = len([x for x in os.listdir(MEDIA_CACHE_DIR) if os.path.isfile(os.path.join(MEDIA_CACHE_DIR, x))])
        except Exception:
            cache_files = 0
        if lang == 'fa':
            text = f"**❈ داشبورد**\n\nآپ‌تایم: {get_uptime(start_time)}\nحافظه: {psutil.virtual_memory().percent}%\nچت‌های خوانده‌نشده: {len(rows)}\nپیام‌های خوانده‌نشده: {unread_total}\nیادداشت‌ها: {len(read_notes(100000))}\nکش ضدحذف: {cache_files}"
        else:
            text = f"**❈ Dashboard**\n\nUptime: {get_uptime(start_time)}\nMemory: {psutil.virtual_memory().percent}%\nUnread chats: {len(rows)}\nUnread messages: {unread_total}\nNotes: {len(read_notes(100000))}\nDeleted cache: {cache_files}"
        buttons = [[pbtn(pt('unread', lang), b'p_unread'), pbtn(pt('health', lang), b'p_health')], [pbtn(pt('refresh', lang), b'menu_dashboard')], [pbtn(pt('back', lang), b'menu_main')]]
        await event.edit(text, buttons=buttons)
        return

    if data == 'menu_notes':
        notes = read_notes(8)
        preview = '\n'.join(notes) if notes else pt('no_notes', lang)
        text = f"**❈ {pt('notes_title', lang)}**\n\n{preview[:2800]}"
        buttons = [[pbtn(pt('new_note', lang), b'p_note_help', 'success'), pbtn(pt('clear_notes', lang), b'p_notes_clear', 'danger')], [pbtn(pt('refresh', lang), b'menu_notes')], [pbtn(pt('back', lang), b'menu_main')]]
        await event.edit(text, buttons=buttons)
        return

    menu_data = {'menu_media','menu_tools','menu_auto','menu_settings','menu_fonts','menu_msg','menu_security','menu_ghost','menu_smart','menu_files','menu_profiles','menu_fun','menu_stats','menu_system'}
    if data in menu_data:
        text, buttons = panel_menu(data, lang)
        await event.edit(text, buttons=buttons)
        return

    elif data == 'p_anim_help':
        await event.answer('Use /anim Your text for an animated message.', alert=True)
    elif data == 'p_auto_read_on':
        _advanced_features._write_flag(_advanced_features.AUTO_READ_FILE, True)
        await event.answer('Auto-read enabled.', alert=True)
    elif data == 'p_auto_read_off':
        _advanced_features._write_flag(_advanced_features.AUTO_READ_FILE, False)
        await event.answer('Auto-read disabled.', alert=True)
    elif data == 'p_auto_reply_on':
        d = _advanced_features._load_json(_advanced_features.AUTO_REPLY_FILE, {'enabled': False, 'text': _advanced_features.DEFAULT_AWAY})
        d['enabled'] = True; _advanced_features._save_json(_advanced_features.AUTO_REPLY_FILE, d); _advanced_features.away_replied.clear()
        await event.answer('Auto-reply enabled.', alert=True)
    elif data == 'p_auto_reply_off':
        d = _advanced_features._load_json(_advanced_features.AUTO_REPLY_FILE, {'enabled': False, 'text': _advanced_features.DEFAULT_AWAY})
        d['enabled'] = False; _advanced_features._save_json(_advanced_features.AUTO_REPLY_FILE, d); _advanced_features.away_replied.clear()
        await event.answer('Auto-reply disabled.', alert=True)
    elif data == 'p_secretary_on':
        _advanced_features._write_flag(_advanced_features.SECRETARY_FILE, True); _advanced_features.away_replied.clear()
        await event.answer('Smart secretary enabled.', alert=True)
    elif data == 'p_secretary_off':
        _advanced_features._write_flag(_advanced_features.SECRETARY_FILE, False); _advanced_features.away_replied.clear()
        await event.answer('Smart secretary disabled.', alert=True)
    elif data == 'p_away_on':
        d = _advanced_features._load_json(_advanced_features.AWAY_FILE, {'enabled': False, 'text': _advanced_features.DEFAULT_AWAY})
        d['enabled'] = True; _advanced_features._save_json(_advanced_features.AWAY_FILE, d); _advanced_features.away_replied.clear()
        await event.answer('Away mode enabled.', alert=True)
    elif data == 'p_away_off':
        d = _advanced_features._load_json(_advanced_features.AWAY_FILE, {'enabled': False, 'text': _advanced_features.DEFAULT_AWAY})
        d['enabled'] = False; _advanced_features._save_json(_advanced_features.AWAY_FILE, d); _advanced_features.away_replied.clear()
        await event.answer('Away mode disabled.', alert=True)
    elif data == 'p_set_log_chat':
        await _advanced_features.set_log_chat(event.chat_id)
        await event.answer('This chat is now the event-log destination.', alert=True)
    elif data == 'p_rename_help':
        await event.answer('Reply to a file and send /renamefile NewName.ext', alert=True)
    elif data == 'p_cover_help':
        await event.answer('Reply to a file with /filecover, then send the cover photo.', alert=True)
    elif data == "p_unread":
        rows = await unread_summary()
        if not rows:
            await event.answer("No unread chats.", alert=True)
        else:
            text = "\n".join(f"• {name}: {count}" for count, name, _ in rows)
            await client.send_message('me', f"**❈ Unread Center**\n\n{text}")
            await event.answer("Unread summary sent to Saved Messages.", alert=True)
    elif data == "p_health":
        await event.answer(f"Health OK | Uptime: {get_uptime(start_time)} | RAM: {psutil.virtual_memory().percent}%", alert=True)
    elif data == "p_note_help":
        await event.answer("Send /note your text in the bot chat. Example: /note Buy a new charger", alert=True)
    elif data == "p_notes_clear":
        open(NOTES_FILE, 'w', encoding='utf-8').close()
        await event.answer("Notes cleared.", alert=True)
    elif data == "p_account":
        try:
            me = await client.get_me()
            name = " ".join(x for x in [getattr(me, "first_name", None), getattr(me, "last_name", None)] if x) or "Unknown"
            username = f"@{me.username}" if me.username else "No username"
            await event.answer(f"**❈ Account\nName: {name}\nUsername: {username}\nID: {me.id}**", alert=True)
        except Exception as e:
            await event.answer(f"**❈ Error: {str(e)[:150]}**", alert=True)
    elif data == "p_uptime":
        await event.answer(f"**❈ Uptime: {get_uptime(start_time)}**", alert=True)
    elif data == "p_now":
        await event.answer(f"**❈ Server time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**", alert=True)
    elif data == "p_read_pv":
        count = 0
        async for dialog in client.iter_dialogs():
            if dialog.is_user:
                await client.send_read_acknowledge(dialog.id); count += 1
        await event.answer(f"**❈ Marked {count} private chats as read.**", alert=True)
    elif data == "p_read_group":
        count = 0
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                await client.send_read_acknowledge(dialog.id); count += 1
        await event.answer(f"**❈ Marked {count} groups as read.**", alert=True)
    elif data == "p_read_channel":
        count = 0
        async for dialog in client.iter_dialogs():
            if dialog.is_channel and not dialog.is_group:
                await client.send_read_acknowledge(dialog.id); count += 1
        await event.answer(f"**❈ Marked {count} channels as read.**", alert=True)
    elif data == "p_cache_info":
        try:
            files = os.listdir(MEDIA_CACHE_DIR)
            size = sum(os.path.getsize(os.path.join(MEDIA_CACHE_DIR, f)) for f in files if os.path.isfile(os.path.join(MEDIA_CACHE_DIR, f)))
            await event.answer(f"**❈ Deleted-media cache: {len(files)} files / {size / 1024:.1f} KB**", alert=True)
        except Exception as e:
            await event.answer(f"**❈ Cache error: {str(e)[:150]}**", alert=True)
    elif data == "p_cache_clear":
        removed = 0
        for name in os.listdir(MEDIA_CACHE_DIR):
            path = os.path.join(MEDIA_CACHE_DIR, name)
            if os.path.isfile(path):
                try:
                    os.remove(path); removed += 1
                except OSError:
                    pass
        await event.answer(f"**❈ Cleared {removed} cached files.**", alert=True)
    elif data in {"p_del_gif", "p_del_sticker", "p_del_photo", "p_del_video"}:
        await event.answer("**❈ Use the matching media command in the target chat to avoid deleting from the wrong conversation.**", alert=True)
    elif data == "p_timename_on":
        with open('settings/time.txt', 'w') as f:
            f.write('True')
        await client(UpdateProfileRequest(last_name=f'{current_time_str}'))
        await event.answer("**❈ Time in Name enabled.**", alert=True)
    elif data == "p_timename_off":
        with open('settings/time.txt', 'w') as f:
            f.write('False')
        await client(UpdateProfileRequest(last_name=''))
        await event.answer("**❈ Time in Name disabled.**", alert=True)
    elif data == "p_timepic_on":
        with open('settings/timepic.txt', 'w') as f:
            f.write('True')
        await event.answer("**❈ Time in Photo enabled.**", alert=True)
    elif data == "p_timepic_off":
        with open('settings/timepic.txt', 'w') as f:
            f.write('False')
        await event.answer("**❈ Time in Photo disabled.**", alert=True)
    elif data == "p_bio_on":
        with open('settings/bioinfo.txt', 'w') as f:
            f.write('True')
        await event.answer("**❈ Dynamic Bio enabled.**", alert=True)
    elif data == "p_bio_off":
        with open('settings/bioinfo.txt', 'w') as f:
            f.write('False')
        await client(UpdateProfileRequest(about=''))
        await event.answer("**❈ Dynamic Bio disabled.**", alert=True)
    elif data == "p_heart_on":
        with open('settings/heart.txt', 'w') as f:
            f.write('True')
        await event.answer("**❈ Heart mode enabled.**", alert=True)
    elif data == "p_heart_off":
        with open('settings/heart.txt', 'w') as f:
            f.write('False')
        await event.answer("**❈ Heart mode disabled.**", alert=True)
    elif data == "p_rname_on":
        with open('settings/rnamest.txt', 'w') as f:
            f.write('True')
        await event.answer("**❈ Random name mode enabled.**", alert=True)
    elif data == "p_rname_off":
        with open('settings/rnamest.txt', 'w') as f:
            f.write('False')
        await event.answer("**❈ Random name mode disabled.**", alert=True)

    elif data == "p_font_bold":
        with open('settings/mode.txt', 'w') as f:
            f.write('Bold')
        await event.answer("**❈ Bold font enabled.**", alert=True)
    elif data == "p_font_mono":
        with open('settings/mode.txt', 'w') as f:
            f.write('Mono')
        await event.answer("**❈ Mono font enabled.**", alert=True)
    elif data == "p_font_mini":
        with open('settings/mode.txt', 'w') as f:
            f.write('Mini')
        await event.answer("**❈ Mini font enabled.**", alert=True)
    elif data == "p_font_farsi":
        with open('settings/mode.txt', 'w') as f:
            f.write('Farsi')
        await event.answer("**❈ Farsi font enabled.**", alert=True)
    elif data == "p_font_fancy":
        with open('settings/mode.txt', 'w') as f:
            f.write('Fancy')
        await event.answer("**❈ Fancy font enabled.**", alert=True)
    elif data == "p_font_circle":
        with open('settings/mode.txt', 'w') as f:
            f.write('Circle')
        await event.answer("**❈ Circle font enabled.**", alert=True)
    elif data == "p_font_subscript":
        with open('settings/mode.txt', 'w') as f:
            f.write('Subscript')
        await event.answer("**❈ Subscript font enabled.**", alert=True)
    elif data == "p_font_double":
        with open('settings/mode.txt', 'w') as f:
            f.write('DoubleStruck')
        await event.answer("**❈ Double-struck font enabled.**", alert=True)
    elif data == "p_font_sansbold":
        with open('settings/mode.txt', 'w') as f:
            f.write('SansBold')
        await event.answer("**❈ Sans-bold font enabled.**", alert=True)
    elif data == "p_font_sans":
        with open('settings/mode.txt', 'w') as f:
            f.write('Sans')
        await event.answer("**❈ Sans font enabled.**", alert=True)
    elif data == "p_font_typewriter":
        with open('settings/mode.txt', 'w') as f:
            f.write('Typewriter')
        await event.answer("**❈ Typewriter font enabled.**", alert=True)
    elif data == "p_font_default":
        with open('settings/mode.txt', 'w') as f:
            f.write('Default')
        await event.answer("**❈ Default font enabled.**", alert=True)
    elif data == "p_font_rnd":
        with open('settings/mode.txt', 'w') as f:
            f.write('rnd')
        await event.answer("**❈ Random font enabled.**", alert=True)

    elif data == "p_antidelete_global_on":
        anti_delete_global_enabled = True
        set_global_anti_delete(True)
        await event.answer("Global anti-delete enabled for private user chats only. Groups/channels/bots are excluded.", alert=True)
    elif data == "p_antidelete_global_off":
        anti_delete_global_enabled = False
        set_global_anti_delete(False)
        await event.answer("Global anti-delete for private user chats disabled.", alert=True)
    elif data == "p_antidelete_on":
        anti_delete_chats.add(event.chat_id)
        await event.answer("**❈ Anti-delete enabled.**", alert=True)
    elif data == "p_antidelete_off":
        anti_delete_chats.discard(event.chat_id)
        await event.answer("**❈ Anti-delete disabled.**", alert=True)
    elif data == "p_antidelete_list":
        await event.answer(f"Global PV anti-delete: {'ON' if anti_delete_global_enabled else 'OFF'} | Per-chat: {len(anti_delete_chats)}", alert=True)

    elif data == "p_ghost_on":
        ghost_mode_enabled = True
        await event.answer("**❈ Ghost mode enabled.**", alert=True)
    elif data == "p_ghost_off":
        ghost_mode_enabled = False
        await event.answer("**❈ Ghost mode disabled.**", alert=True)
    elif data == "p_spoiler_on":
        spoiler_mode_enabled = True
        await event.answer("**❈ Spoiler mode enabled.**", alert=True)
    elif data == "p_spoiler_off":
        spoiler_mode_enabled = False
        await event.answer("**❈ Spoiler mode disabled.**", alert=True)

    elif data == "p_words_list":
        words_text = "\n".join(blocked_words) if blocked_words else "Empty"
        await event.answer(words_text[:200], alert=True)
    elif data == "p_watch_list":
        watch_text = "\n".join(watch_keywords) if watch_keywords else "Empty"
        await event.answer(watch_text[:200], alert=True)

    elif data == "p_block_start":
        pending_input[admin_user_id] = "block"
        await event.answer("**❈ Send the numeric ID or @username here in a separate message.**", alert=True)
    elif data == "p_unblock_start":
        pending_input[admin_user_id] = "unblock"
        await event.answer("**❈ Send the numeric ID or @username here in a separate message.**", alert=True)

    elif data == "p_hafez":
        try:
            response = requests.get('https://hafez-dxle.onrender.com/fal')
            hdata = response.json()
            interpretation = hdata.get('interpreter', 'فالی پیدا نشد.')
            await event.answer(interpretation[:200], alert=True)
        except Exception as e:
            await event.answer(f"**❈ Error: {e}**", alert=True)

    elif data == "p_stats_today":
        msg = f"**❈ Messages: {daily_stats['messages_today']}\nUsers: {len(daily_stats['unique_senders'])}**"
        await event.answer(msg, alert=True)
    elif data == "p_mem":
        mem_usage = psutil.virtual_memory().percent
        await event.answer(f"💾 Memory Usage: {mem_usage}%", alert=True)
    elif data == "p_ping":
        await event.answer("**❈ Self client is online and responding.**", alert=True)
    elif data == "p_reload":
        await client.send_message('me', '**❈ Reloading from panel...**')
        os.execv(sys.executable, ['python'] + sys.argv)
    elif data == "p_support":
        await event.answer(f"**❈ Support: @{SUPPORT_USERNAME}**", alert=True)
    elif data == "p_logout_confirm":
        await event.answer("**❈ To actually log out, use /logout directly. This button is only a warning.**", alert=True)
    else:
        await event.answer("**❈ This option is informational only.**", alert=True)

@bot_client.on(events.NewMessage)
async def bot_handle_pending_input(event):
    if event.sender_id != admin_user_id:
        return
    if event.raw_text and event.raw_text.startswith('/'):
        return
    action = pending_input.get(admin_user_id)
    if not action:
        return
    target = event.raw_text.strip()
    try:
        entity = await client.get_entity(target)
    except Exception:
        try:
            entity = await client.get_entity(int(target))
        except Exception as e:
            await event.reply(f"**❈ User not found: {e}**")
            pending_input[admin_user_id] = None
            return

    if action == "block":
        await client(functions.contacts.BlockRequest(entity.id))
        await event.reply(result_ok(f"User {target} blocked."))
    elif action == "unblock":
        await client(functions.contacts.UnblockRequest(entity.id))
        await event.reply(result_ok(f"User {target} unblocked."))

    pending_input[admin_user_id] = None

scheduled_jobs = {}

async def run_scheduled_job(job_id, target, text, minutes):
    while True:
        await asyncio.sleep(minutes * 60)
        try:
            await client.send_message(target, text)
        except Exception as e:
            await client.send_message(admin_user_id, f"**❈ Scheduler error #{job_id}: {e}**")

@client.on(events.NewMessage(pattern=r'(?i)^زمانبند (\d+) (.+)$'))
async def start_scheduled_post(event):
    if event.sender_id != admin_user_id:
        return
    if not event.is_reply:
        await event.reply("**❈ Reply to the text you want to repeat, then use: /schedule [minutes] [chat]**")
        return
    minutes = int(event.pattern_match.group(1))
    if minutes < 1:
        await event.reply("**❈ Schedule interval must be at least 1 minute.**")
        return
    target = event.pattern_match.group(2).strip()
    replied = await event.get_reply_message()
    text_to_send = replied.raw_text
    if not text_to_send:
        await event.reply("**❈ The replied message has no text.**")
        return
    try:
        entity = await client.get_entity(target)
    except Exception:
        try:
            entity = await client.get_entity(int(target))
        except Exception as e:
            await event.reply(f"**❈ Target chat not found: {e}**")
            return
    job_id = (max(scheduled_jobs.keys()) + 1) if scheduled_jobs else 1
    task = client.loop.create_task(run_scheduled_job(job_id, entity, text_to_send, minutes))
    scheduled_jobs[job_id] = {'task': task, 'target': target, 'minutes': minutes, 'text': text_to_send}
    await event.reply(f"**❈ Schedule #{job_id} enabled: every {minutes} minutes to {target}**")

@client.on(events.NewMessage(pattern='(?i)^لیست زمانبندها$'))
async def list_scheduled_jobs(event):
    if event.sender_id != admin_user_id:
        return
    if not scheduled_jobs:
        await event.reply("**❈ No active schedules.**")
        return
    lines = ["📅 زمانبندهای فعال:"]
    for jid, info in scheduled_jobs.items():
        lines.append(f"#{jid} → هر {info['minutes']} دقیقه به {info['target']}")
    await event.reply("\n".join(lines))

@client.on(events.NewMessage(pattern=r'(?i)^حذف زمانبند (\d+)$'))
async def delete_scheduled_job(event):
    if event.sender_id != admin_user_id:
        return
    job_id = int(event.pattern_match.group(1))
    job = scheduled_jobs.get(job_id)
    if not job:
        await event.reply("**❈ Schedule not found.**")
        return
    job['task'].cancel()
    del scheduled_jobs[job_id]
    await event.reply(f"**❈ Schedule #{job_id} deleted.**")

async def _background(coro, name):
    try:
        await coro
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("Background task failed: %s", name)


async def run_app():
    global anti_delete_global_enabled
    anti_delete_global_enabled = is_global_anti_delete_enabled()
    logger.info("Starting self client...")
    await client.connect()
    if not await client.is_user_authorized():
        raise RuntimeError(
            "Telegram user session is not authorized. On Render, set SESSION_STRING to a valid user session."
        )
    me = await client.get_me()
    logger.info("Self client connected as %s (%s)", getattr(me, "username", None), me.id)
    await _advanced_features.restore_log_chat()

    logger.info("Starting helper bot...")
    await bot_client.start(bot_token=bot_token)
    logger.info("Helper bot connected")

    for coro, name in (
        (update_first_name(), "update_first_name"),
        (update_last_name(), "update_last_name"),
        (update_about(), "update_about"),
        (update_profile_photo(), "update_profile_photo"),
        (send_daily_report(), "send_daily_report"),
        (_advanced_features.advanced_profile_watch_loop(), "advanced_profile_watch_loop"),
        (bot_client.run_until_disconnected(), "helper_bot"),
    ):
        client.loop.create_task(_background(coro, name))

    # Send welcome only after the self client is authenticated.
    await send_welcome_message()
    logger.info("Startup completed")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        client.loop.run_until_complete(run_app())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
