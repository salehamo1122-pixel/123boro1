from .library import *
from .Information import *
from .updater import *

async def send_welcome_message():
    """Send a startup message to Saved Messages and never hide startup errors."""
    try:
        admin_user = await client.get_entity(admin_user_id)
        admin_first_name = getattr(admin_user, "first_name", None) or "دوست عزیز"
        text = (
            f"**❈ خوش آمدی، {admin_first_name}! 👋**\n"
            "**❈ سلف با موفقیت اجرا شد.**\n"
            "**❈ ساخته‌شده توسط @saleh681.**\n"
            f"**❈ پشتیبانی: @{SUPPORT_USERNAME}**"
        )
        await client.send_message("me", text)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Failed to send startup welcome message")
        raise

pic_folder = 'pic/'

def set_user_bio(bio):
    with open('settings/bio.txt', 'w') as f:
        f.write(bio)

def set_user_lname(lname):
    with open('settings/nameinfo.txt', 'w') as f:
        f.write(lname)

def get_user_bio():
    with open('settings/bio.txt', 'r') as f:
        return f.read().strip()

def load_admins():
    try:
        with open('settings/admin.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_admins(admins):
    with open('settings/admin.json', 'w') as file:
        json.dump(admins, file)

def generate_random_filename():
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(10))

def find_matching_filename(message):
    for file in os.listdir(SAVE_FOLDER):
        if message.lower() == os.path.splitext(file)[0].lower():
            return os.path.join(SAVE_FOLDER, file)
    return None

fast_replies_file = 'settings/fast_replies.json'

def load_fast_replies():
    try:
        with open(fast_replies_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_fast_replies(fast_replies):
    with open(fast_replies_file, 'w') as f:
        json.dump(fast_replies, f, indent=4)




def get_uptime(start_time):
    now = datetime.datetime.now()
    uptime = now - start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days} days {hours} hours {minutes} minutes {seconds} seconds"

start_time = datetime.datetime.now()
async def start_command(event):
    if event.sender_id == admin_user_id:
        uptime = get_uptime(start_time)
        message = f"**❈ ربات آنلاین است :)\nمدت فعالیت: {uptime}**"
        await event.edit(message)

async def ping(event):
    if event.sender_id == admin_user_id:
        start_time = datetime.datetime.now()
        await event.delete()
        message = await event.respond('**❈ پونگ!**')
        end_time = datetime.datetime.now()
        response_time = (end_time - start_time).total_seconds() * 1000
        user_link = f'❈[I Never Lose](tg://user?id={admin_user_id})'
        await message.edit(f'**{user_link} ! زمان پاسخ: {response_time:.2f} ms**')

async def mem(event):
    if event.sender_id == admin_user_id:
        memory = psutil.virtual_memory().percent
        await event.edit(f'**❈ مصرف حافظه: {memory} مگابایت**')

MSAVE_DIRECTORY = 'music'

async def sc(event):
    if event.sender_id == admin_user_id:
        if sp is None:
            await event.edit("**❈ اسپاتیفای تنظیم نشده است.**")
            return
        query = event.raw_text[7:].strip()
        if not query:
            await event.edit("**❈ بعد از /gmusic نام آهنگ یا خواننده را بنویس.**")
            return
        results = sp.search(q=query, type='track')
        tracks = results.get('tracks', {}).get('items', [])
        
        if tracks:
            track = tracks[0]
            title = track.get('name', '')
            artist = track.get('artists', [{}])[0].get('name', '')
            url = track.get('external_urls', {}).get('spotify', '')
            views = track.get('popularity', '')
            release_date = track.get('album', {}).get('release_date', '')
            
            await event.delete()
            await download_and_send(track, event, title, artist, views, release_date, url)
        else:
            await event.edit(f'**❈ متأسفانه نتیجه‌ای پیدا نشد.**')

async def download_and_send(track, event, title, artist, views, release_date, url):
    try:
        audio_url = track.get('preview_url')
        
        if audio_url:
            audio_file_path = os.path.join(MSAVE_DIRECTORY, f'{title}.mp3')
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url) as resp:
                    if resp.status == 200:
                        with open(audio_file_path, 'wb') as file:
                            while True:
                                chunk = await resp.content.read(1024)
                                if not chunk:
                                    break
                                file.write(chunk)
                        
                        await event.reply(
                            file=audio_file_path,
                            message=f"**❈ عنوان: {title}\nخواننده: {artist}\nبازدید: {views} هزار\nتاریخ انتشار: {release_date}\n[شنیدن در اسپاتیفای]({url})**",
                        )
                        
                        os.remove(audio_file_path)
                    else:
                        await event.reply(f"دانلود ناموفق بود. کد وضعیت: {resp.status}")
        else:
            await event.reply(f"پیش‌نمایش صوتی موجود نیست.")
    
    except Exception as e:
        await event.reply(f"ناموفق: {str(e)}")


async def tarikh(event):
    if event.sender_id == admin_user_id:
        try:
            jalali_date = JalaliDate.today().strftime('%A %d %B %Y')
            await event.edit(f'**❈ امروز: {jalali_date}**')
        except Exception as e:
            await event.reply(f"دریافت تاریخ ناموفق بود: {str(e)}")

async def gmsg(event):
    if event.sender_id == admin_user_id:
        try:
            await event.delete()
            processing_message = await event.respond("در حال پردازش پیام شما...")

            msg = event.raw_text[6:]
            for i in range(len(msg)):
                await processing_message.edit(f"{msg[:i+1]}")
                await asyncio.sleep(0.3)

            await processing_message.edit(f"{msg} 💚")
        except Exception as e:
            await event.reply(f"پردازش پیام ناموفق بود: {str(e)}")

async def weather(event):
    if event.sender_id == admin_user_id:
        try:
            location = event.raw_text[9:]
            url = f'https://wttr.in/{location}?format=%C\n%t\n%h\n&lang=fa'
            response = requests.get(url)

            if response.status_code == 200:
                weather_data = response.text.split('\n')
                condition = weather_data[0]
                temperature = weather_data[1]
                humidity = weather_data[2]

                message = f'**❈ آب‌وهوای فعلی {location}:**\n\nوضعیت: {condition}\nدما: {temperature}\nرطوبت: {humidity}'
                await event.edit(message)
            else:
                await event.reply('**❈ متأسفانه در دریافت آب‌وهوا خطایی رخ داد.**')
        except Exception as e:
            await event.reply(f'دریافت آب‌وهوا ناموفق بود: {str(e)}')

async def rsong(event):
    if event.sender_id == admin_user_id:
        try:
            channel = '@LiMuTa'
            limit = 100
            messages = await client.get_messages(channel, limit=limit)
            
            audio_messages = [
                m for m in messages 
                if hasattr(m, 'media') 
                and hasattr(m.media, 'document') 
                and m.media.document.mime_type == 'audio/mpeg'
            ]
            
            if audio_messages:
                random_audio_message = random.choice(audio_messages)
                await client.forward_messages(event.chat_id, random_audio_message)
                await event.edit('**❈ آهنگ تصادفی شما ارسال شد!**')
                await asyncio.sleep(0.5)
                await client.delete_messages(event.chat_id, event.id)
            else:
                await event.respond('**❈ پیام صوتی پیدا نشد.**')
        except Exception as e:
            await event.respond(f'دریافت و ارسال آهنگ تصادفی ناموفق بود: {str(e)}')

async def info(event):
    if event.sender_id == admin_user_id:
        try:
            username = event.text[6:].strip()

            if username:
                user = await client.get_entity(username)

                if isinstance(user, User):
                    photo = await client.download_profile_photo(user)

                    if os.path.exists(photo):
                        caption = f"شناسه: {user.id}\nنام: {user.first_name}\nیوزرنیم: @{user.username}"
                        await event.reply(file=photo, message=caption)

                        os.remove(photo)
                    else:
                        await event.edit("**❈ دانلود عکس پروفایل ناموفق بود.**")
                else:
                    await event.edit('**❈ این یوزرنیم متعلق به یک کانال یا گروه است.**')
            else:
                await event.edit('❈ لطفاً یک یوزرنیم وارد کن.')

        except ValueError:
            await event.edit('**❈ یوزرنیم نامعتبر است.**')
        except Exception as e:
            await event.edit(f'دریافت اطلاعات کاربر ناموفق بود: {str(e)}')

async def set_profile_pic(event):
    if event.sender_id == admin_user_id:    
        if event.is_reply:
            try:
                reply = await event.get_reply_message()

                if reply.photo:
                    photo = await client.download_media(reply.photo)

                    with open(photo, 'rb') as f:
                        uploaded_file = await client.upload_file(photo)
                        await client(functions.photos.UploadProfilePhotoRequest(file=uploaded_file))

                    os.remove(photo)  # Remove the photo after it's been uploaded
                    await event.edit(f'**❈ عکس [پروفایل](tg://user?id={admin_user_id}) با موفقیت تغییر کرد!**')
                else:
                    await event.edit('**❈ برای تنظیم عکس پروفایل، روی یک عکس ریپلای کن.**')

            except ValueError:
                await event.edit('**❈ خطا: فرمت رسانه نامعتبر است.**')
            except Exception as e:
                await event.respond(f'**❈ خطا در تغییر عکس پروفایل: {str(e)}**')
        else:
            await event.edit('**❈ برای تنظیم عکس پروفایل، روی یک عکس ریپلای کن.**')

async def delete_profile_pic(event):
    if event.sender_id == admin_user_id:
        try:
            photos = await client.get_profile_photos('me')
            
            if photos:
                await client(functions.photos.DeletePhotosRequest(id=[InputPhoto(id=photos[0].id, access_hash=photos[0].access_hash, file_reference=photos[0].file_reference)]))
                await event.edit(f'**❈ عکس [پروفایل](tg://user?id={admin_user_id}) با موفقیت حذف شد!**')
            else:
                await event.edit('**❈ عکس پروفایلی برای حذف پیدا نشد.**')
        
        except ValueError:
            await event.edit('**❈ خطا: اطلاعات عکس پروفایل نامعتبر است.**')
        except Exception as e:
            await event.edit(f'**❈ خطا در حذف عکس پروفایل: {str(e)}**')

async def rinfo(event):
    if event.sender_id == admin_user_id:
        try:
            await event.delete()
            if event.is_reply:
                reply = await event.get_reply_message()

                if reply.sender_id:
                    user = await client.get_entity(reply.sender_id)

                    if isinstance(user, types.User):
                        user_full = await client(functions.users.GetFullUserRequest(user.id))
                        user_info = await client(functions.users.GetUsersRequest([user.id]))
                        user_status = user_info[0].status

                        if isinstance(user_status, types.UserStatusOnline):
                            last_seen = "Online"
                        elif isinstance(user_status, types.UserStatusOffline):
                            last_seen = user_status.was_online.astimezone().strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            last_seen = "Recently"

                        common_chats = await client(functions.messages.GetCommonChatsRequest(user_id=user.id, max_id=0, limit=10))
                        groups_count = len(common_chats.chats)

                        bio = user_info[0].about if hasattr(user_info[0], 'about') else "None"

                        photos = await client(functions.photos.GetUserPhotosRequest(user_id=user.id, offset=0, max_id=0, limit=0))
                        profile_count = len(photos.photos) if photos and photos.photos else 0

                        info_text = (
                            f"**❈ نام: ({user.first_name})\nشناسه: (`{user.id}`)\nیوزرنیم: (@{user.username})\nشماره: (***********)\nپروفایل‌ها: ({profile_count})\nوضعیت: ({last_seen})\nگروه‌ها: ({groups_count})\n\nبیو: ({bio})**"
                        )

                        if photos and len(photos.photos) > 0:
                            await client.send_file(event.chat_id, file=photos.photos[0], caption=info_text)
                        else:
                            await client.send_message(event.chat_id, info_text)

                    elif isinstance(user, types.Channel):
                        info_text = f"شناسه: {user.id}\nعنوان: {user.title}\nیوزرنیم: {user.username}\nتوضیحات: {user.description}"
                        await client.send_message(event.chat_id, info_text)

                else:
                    await client.send_message(event.chat_id, '**❈ پیام ریپلای‌شده فرستنده ندارد.**')
            else:
                await client.send_message(event.chat_id, '**❈ برای دریافت اطلاعات فرستنده، روی یک پیام ریپلای کن.**')
        except ValueError:
            await client.send_message(event.chat_id, '**❈ خطا: اطلاعات فرستنده پیام نامعتبر است.**')
        except Exception as e:
            await client.send_message(event.chat_id, f'❈ خطا در دریافت اطلاعات: {str(e)}')

async def delete_recent_messages(event):
    if event.sender_id == admin_user_id:
        try:
            num = int(event.text.split()[1])

            if num > 50:
                await event.respond('**❈ هر بار فقط می‌توانی تا ۵۰ پیام حذف کنی.**')
                return

            messages = await client.get_messages(event.chat_id, limit=num)

            if not messages:
                await event.respond('**❈ پیامی برای حذف پیدا نشد.**')
                return

            deleted_messages = await client.delete_messages(entity=event.chat_id, message_ids=[msg.id for msg in messages], revoke=True)
            await event.respond(f'**❈ {num} پیام با موفقیت حذف شد!**')

        except ValueError:
            await event.respond('**❈ تعداد معتبری برای حذف پیام‌ها وارد کن.**')
        except Exception as e:
            await event.respond(f'**❈ خطا در حذف پیام‌ها: {str(e)}**')

async def sgoogle(event):
    if event.sender_id == admin_user_id:
        query = event.raw_text[9:].strip()
        if not query:
            await event.edit('لطفاً عبارت جستجو را وارد کن.')
            return

        try:
            await event.edit(f'در حال جستجوی «{query}"...')
            search_results = list(search(query, num_results=5))

            if not search_results:
                await event.edit('نتیجه‌ای پیدا نشد.')
                return

            response_text = f'پنج نتیجه برتر برای «{query}»:\n\n'
            for i, result in enumerate(search_results):
                response_text += f'{i + 1}. {result}\n'

            await event.edit(response_text)

        except Exception as e:
            print(f'خطا در جستجوی گوگل: {str(e)}')
            await event.edit('متأسفانه در جستجوی گوگل خطایی رخ داد.')

async def wiki(event):
    if event.sender_id == admin_user_id:
        query = event.raw_text[6:].strip()
        if not query:
            await event.edit('لطفاً عبارت جستجو را وارد کن.')
            return

        try:
            await event.edit(f'در حال جستجوی «{query}» در ویکی‌پدیای فارسی...')
            wikipedia.set_lang('fa')
            page = wikipedia.page(query)
            summary = wikipedia.summary(query)
            response_text = f'عنوان صفحه: {page.title}\n\nخلاصه: {summary}'
            await event.edit(response_text)

        except wikipedia.exceptions.PageError:
            await event.edit(f'صفحه‌ای در ویکی‌پدیا برای «{query}".')

        except wikipedia.exceptions.DisambiguationError as e:
            options = "\n- ".join(e.options[:5])
            await event.edit(f'چند گزینه برای «{query}» پیدا نشد. لطفاً با عبارت دقیق‌تری دوباره تلاش کن.\n\nگزینه‌ها:\n- {options}')

        except Exception as e:
            print(f'خطا در جستجوی ویکی‌پدیا: {str(e)}')
            await event.respond('متأسفانه در جستجوی ویکی‌پدیا خطایی رخ داد.')

async def save_message(event):
    if event.sender_id == admin_user_id:
        try:
            await event.delete()
            reply = await event.get_reply_message()
            
            if reply and reply.media:
                if isinstance(reply.media, types.MessageMediaDocument) or isinstance(reply.media, types.MessageMediaPhoto):
                    file = await client.download_media(reply)
                    caption = f"ذخیره‌شده از @{reply.sender.username}" if reply.sender.username else f"ذخیره‌شده از کاربر با شناسه {reply.sender.id}"
                    await client.send_file('me', file, caption=caption)
                    os.remove(file)
                else:
                    return
            else:
                return

        except Exception as e:
            await event.respond(f"❈ خطا در ذخیره‌سازی: {str(e)}")

async def add_bio(event):
    if event.sender_id == admin_user_id:
        try:
            bio = event.message.text.replace('/addbio', '').strip()
            set_user_bio(bio)
            await event.edit(f"**❈ بیوی شما به این مقدار تغییر کرد: `{bio}` **")

        except Exception as e:
            await event.respond(f"❈ خطا در تغییر بیو: {str(e)}")

async def add_lname(event):
    if event.sender_id == admin_user_id:
        try:
            lname = event.message.text.replace('/addlname', '').strip()
            set_user_lname(lname)
            await event.edit(f"**❈ نام خانوادگی شما به این مقدار تغییر کرد: `{lname}` **")

        except Exception as e:
            await event.respond(f"❈ خطا در تغییر نام خانوادگی: {str(e)}")

async def add_rname(event):
    if event.sender_id == admin_user_id:
        try:
            rname_list = event.message.text.replace('/addrname', '').strip()
            rname_items = rname_list.split(',')
            if len(rname_items) >= 3:
                with open('settings/rname.txt', 'w') as f:
                    f.write(rname_list)
                await event.respond(f"**❈ لیست نام‌های تصادفی به این مقدار تغییر کرد: `{rname_list}` **")
            else:
                await event.respond(f"❈ لطفاً حداقل ۳ مورد را با کاما جدا کرده و وارد کن.")
        
        except Exception as e:
            await event.respond(f"❈ خطا در تغییر لیست نام‌ها: {str(e)}")

async def delete_rname(event):
    if event.sender_id == admin_user_id:
        try:
            with open('settings/rname.txt', 'w') as f:
                f.write('')
            await event.respond("**❈ لیست نام‌ها پاک شد.**")

        except Exception as e:
            await event.respond(f"❈ خطا در پاک کردن لیست نام‌ها: {str(e)}")

async def reload_bot(event):
    if event.sender_id == admin_user_id:
        await event.edit('❈𝑹𝒆𝒍𝒐𝒂𝒅𝒊𝒏𝒈 𝒃𝒐𝒕...')
        await asyncio.sleep(0.5)
        await event.edit('❈𝑹𝒆𝒍𝒐𝒂𝒅 𝑪𝒐𝒎𝒑𝒍𝒊𝒕𝒆𝒅!')
        os.execl(sys.executable, sys.executable, *sys.argv)

async def backup_chat(event):
    if event.sender_id == admin_user_id:
        chat = await event.get_chat()
        if isinstance(chat, types.Channel):
            filename = f'{chat.id}_backup.txt'
            messages = await client.get_messages(event.chat_id, limit=1500)
            with open(filename, 'w') as f:
                for message in messages:
                    f.write(f'{message.date} - {message.sender_id} - {message.text}\n')
            caption = f'پشتیبان کانال {chat.title if chat.title else "چت بدون نام"}'
            await client.send_file(admin_user_id, filename, caption=caption)
            os.remove(filename)
        elif isinstance(chat, types.User):
            filename = f'{chat.id}_backup.txt'
            messages = await client.get_messages(event.chat_id, limit=1500)
            with open(filename, 'w') as f:
                for message in messages:
                    f.write(f'{message.date} - {message.sender_id} - {message.text}\n')
            if chat.last_name:
                caption = f'پشتیبان چت با {chat.first_name} {chat.last_name}'
            else:
                caption = f'پشتیبان چت با {chat.first_name}'
            await client.send_file(admin_user_id, filename, caption=caption)
            os.remove(filename)
        await event.delete()

def _safe_calculate(expression: str):
    """Evaluate basic arithmetic without executing arbitrary Python code."""
    import ast
    import operator

    operators = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and type(node.op) in operators:
            return operators[type(node.op)](visit(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in operators:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 1000:
                raise ValueError("exponent too large")
            return operators[type(node.op)](left, right)
        raise ValueError("only arithmetic expressions are allowed")

    return visit(ast.parse(expression, mode="eval"))


async def calculator(event):
    if event.sender_id != admin_user_id:
        return
    expression = event.message.text.replace('/calc', '', 1).strip()
    try:
        if not expression:
            raise ValueError("empty expression")
        result = _safe_calculate(expression)
        await event.edit(f"{expression} = {result}")
    except Exception:
        await event.edit("**❈ عبارت محاسباتی نامعتبر است.**")

async def create_channel(event):
    if event.sender_id == admin_user_id:
        channel_name = event.pattern_match.group(1)
        result = await client(CreateChannelRequest(channel_name, 'کانال خصوصی', megagroup=False))
        if result:
            channel_link = f'https://t.me/{channel_name}'
            await event.edit(f"کانال [{channel_name}]({channel_link}) ساخته شد", link_preview=False)
        else:
            await event.edit("ساخت کانال ناموفق بود")


enemy_list = []
user_messages = {}

async def enemy_mode(event):
    if event.sender_id == admin_user_id:
        replied_to = await event.get_reply_message()
        if replied_to:
            sender_id = replied_to.sender_id
            if sender_id not in enemy_list:
                enemy_list.append(sender_id)
                await event.edit(f"**❈ [کاربر](tg://user?id={sender_id}) در حالت سکوت قرار گرفت. همه پیام‌هایش حذف می‌شود.**")
            else:
                await event.edit(f"**❈ [کاربر](tg://user?id={sender_id}) از قبل در حالت سکوت است.**")
        else:
            await event.edit(f"**❈ برای سکوت کاربر، روی پیامش ریپلای کن.**")


async def unenemy_mode(event):
    if event.sender_id == admin_user_id:
        replied_to = await event.get_reply_message()
        if replied_to:
            sender_id = replied_to.sender_id
            if sender_id in enemy_list:
                enemy_list.remove(sender_id)
                await event.edit(f"**❈ [کاربر](tg://user?id={sender_id}) از حالت سکوت خارج شد.**")
            else:
                await event.edit(f"**❈ [کاربر](tg://user?id={sender_id}) در حالت سکوت نیست.**")
        else:
            await event.edit(f"**❈ برای خروج کاربر از سکوت، روی پیامش ریپلای کن.**")

async def tag_all_members(event):
    if event.is_group and event.sender_id == admin_user_id:
        try:
            chat = await event.get_chat()
            if chat.admin_rights and chat.admin_rights.delete_messages:
                members = await client.get_participants(chat)
                tag_string = '**❈ همه اعضا تگ شدند:**\n\n'
                for member in members:
                    tag_string += f'[{member.first_name}](tg://user?id={member.id})\n'
                await event.edit(tag_string, parse_mode='Markdown')
            else:
                await event.respond('**❈ برای استفاده از این دستور باید ادمین چت با دسترسی حذف پیام باشی.**')
        
        except Exception as e:
            await event.respond(f'❈ خطا در تگ کردن اعضا: {str(e)}')

    else:
        await event.edit('**❈ این دستور فقط توسط ادمین و در گروه قابل استفاده است.**')

async def delete_reply(event):
    if event.sender_id == admin_user_id:
        try:
            replied_msg = await event.get_reply_message()
            if replied_msg:
                await replied_msg.delete()
                await event.delete()
            else:
                await event.respond('**❈ برای حذف پیام، روی آن ریپلای کن.**')

        except Exception as e:
            await event.respond(f'❈ خطا در حذف پیام: {str(e)}')

    else:
        await event.respond('**❈ فقط ادمین می‌تواند از این دستور استفاده کند.**')


GAdmins = load_admins()
SAVE_FOLDER = 'save'
silenced_users = []
async def save_user_id(event):
    if event.is_group and event.sender_id == admin_user_id or event.sender_id in GAdmins:
        replied_msg = await event.get_reply_message()
        if replied_msg:
            user_id = replied_msg.sender_id
            if user_id == admin_user_id or user_id in GAdmins:
                await event.delete()
                await event.respond(f"**❈ نمی‌توانی ادمین را سکوت کنی.**")
                return

            if user_id not in silenced_users:
                silenced_users.append(user_id)
                await event.delete()
                await event.respond(f'**❈ کاربر با شناسه [{user_id}](tg://user?id={user_id}) به لیست سکوت اضافه شد.**')
            else:
                await event.delete()
                await event.respond(f'**❈ کاربر با شناسه [{user_id}](tg://user?id={user_id}) از قبل در لیست سکوت است.**')
        else:
            await event.delete()
            await event.respond('برای ذخیره شناسه کاربر، روی پیامش ریپلای کن.')
    else:
        await event.delete()
        await event.respond('این دستور فقط توسط ادمین و در گروه قابل استفاده است.')

async def remove_user_from_silenced(event):
    if event.is_group and event.sender_id == admin_user_id or event.sender_id in GAdmins:
        replied_msg = await event.get_reply_message()
        user_id = None
        if replied_msg:
            user_id = replied_msg.sender_id
        elif event.pattern_match.group(1):
            user_id = int(event.pattern_match.group(1).strip())
        
        if user_id and user_id in silenced_users:
            silenced_users.remove(user_id)
            await event.delete()
            await event.respond(f'**❈ کاربر [{user_id}](tg://user?id={user_id}) از سکوت خارج شد.**')
        else:
            await event.delete()
            await event.respond(f'**❈ کاربر نامعتبر است یا در لیست سکوت نیست.**')
    else:
        await event.delete()
        await event.respond(f'**❈ این دستور فقط در گروه‌ها قابل استفاده است.**')

async def promote_user_to_admin(event):
    if event.is_group and event.sender_id == admin_user_id:
        replied_msg = await event.get_reply_message()
        if replied_msg:
            user_id = replied_msg.sender_id
            if user_id not in GAdmins:
                GAdmins.append(user_id)
                save_admins(GAdmins)
                await event.edit(f'**❈ کاربر {user_id} به ادمین ارتقا یافت.**')
            else:
                await event.edit('**❈ کاربر از قبل ادمین است.**')
        else:
            await event.edit('**❈ برای ارتقای کاربر، روی پیامش ریپلای کن.**')
    else:
        await event.edit('**❈ این دستور فقط توسط ادمین‌های گروه قابل استفاده است.**')

async def demote_admin(event):
    if event.is_group and event.sender_id == admin_user_id:
        replied_msg = await event.get_reply_message()
        if replied_msg:
            user_id = replied_msg.sender_id
            if user_id in GAdmins:
                GAdmins.remove(user_id)
                save_admins(GAdmins)
                await event.edit(f'**❈ کاربر {user_id} از ادمینی برکنار شد.**')
            else:
                await event.edit('**❈ کاربر ادمین نیست.**')
        else:
            await event.edit('**❈ برای برکناری کاربر، روی پیامش ریپلای کن.**')
    else:
        await event.edit('**❈ این دستور فقط توسط ادمین‌های گروه قابل استفاده است.**')

async def generate_password(event):
    if event.sender_id == admin_user_id:
        try:
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            await event.edit(f"**❈ رمز عبور تصادفی: `{password}` **")

        except Exception as e:
            await event.edit(f'❈ خطا در ساخت رمز عبور: {str(e)}')

async def save_video(event):
    if event.reply_to_msg_id and event.sender_id == admin_user_id:
        replied_msg = await event.get_reply_message()
        if isinstance(replied_msg.media, (types.MessageMediaPhoto, types.MessageMediaDocument)):
            media = replied_msg.media
            filename = generate_random_filename()
            save_path = os.path.join(SAVE_FOLDER, filename)
            await client.download_media(media, file=save_path)
            await event.edit(f"**❈ رسانه با این نام ذخیره شد: `{filename}`**")
        else:
            await event.edit(f"**❈ برای ذخیره، روی یک عکس یا ویدیو ریپلای کن.**")
    else:
        await event.edit(f"**❈ برای ذخیره، روی یک عکس یا ویدیو ریپلای کن.**")

async def send_video(event):
    if event.sender_id == admin_user_id:
        message = event.raw_text.replace('/Smedia', '').strip()
        filename = find_matching_filename(message)
        if filename:
            await event.delete()
            await client.send_file(event.chat_id, filename)
            os.remove(filename)
        else:
            await event.edit(f"**❈ فایلی با این نام پیدا نشد: {message}.**")

async def list_saved_media(event):
    if event.sender_id == admin_user_id:
        files = os.listdir(SAVE_FOLDER)
        if files:
            file_names = [os.path.splitext(file)[0] for file in files]
            file_list = '\n'.join(file_names)
            await event.edit(f"**❈ لیست رسانه‌های ذخیره‌شده:**\n`{file_list}`")
        else:
            await event.edit("**❈ رسانه‌ای ذخیره نشده است.**")


fast_replies = load_fast_replies()

async def ffast_replies(event):
    global fast_replies, admin_user_id

    if event.sender_id == admin_user_id:
        text = event.raw_text.replace('/Freplay', '').strip()
        if text.startswith('add'):
            parts = text.split(',', 1)
            if len(parts) == 2:
                keyword = parts[0].strip().replace('add', '').strip()
                reply = parts[1].strip()
                fast_replies[keyword.lower()] = reply
                save_fast_replies(fast_replies)
                await event.edit(f"**❈ پاسخ سریع اضافه شد: {keyword} -> {reply}**")
            else:
                await event.edit(f"**❈ فرمت دستور نامعتبر است. از این الگو استفاده کن: `/Freplay add [کلمه],[پاسخ]`**")
        elif text.startswith('remove'):
            keyword = text.replace('remove', '').strip()
            if keyword.lower() in fast_replies:
                del fast_replies[keyword.lower()]
                save_fast_replies(fast_replies)
                await event.edit(f"**❈ پاسخ سریع حذف شد: {keyword}**")
            else:
                await event.edit(f"**❈ پاسخ سریعی با این کلمه پیدا نشد: {keyword}**")
        else:
            await event.edit("**❈ فرمت دستور نامعتبر است. از `/Freplay add [کلمه],[پاسخ]` یا `/Freplay remove [کلمه]` استفاده کن.**")

async def show_fast_replies(event):
    global fast_replies, admin_user_id

    if event.sender_id == admin_user_id:
        if fast_replies:
            reply_text = "**❈ پاسخ‌های سریع:**\n"
            for keyword, reply in fast_replies.items():
                reply_text += f"- {keyword}: {reply}\n"
        else:
            reply_text = "**❈ پاسخ سریعی وجود ندارد.**"

        await event.edit(reply_text)

async def whois_domain(event):
    if event.sender_id == admin_user_id:
        try:
            text = event.raw_text.strip()
            domain = text.replace('/whois', '').strip()

            if domain:
                domain_info = whois.whois(domain)
                message = f"**Domain: {domain}\n\n**"
                message += f"**Registrar: {domain_info.registrar}\n**"
                message += f"**نام ثبت‌شده: {domain_info.name}\n**"
                message += f"**تاریخ ایجاد: {domain_info.creation_date}\n**"
                message += f"**تاریخ انقضا: {domain_info.expiration_date}\n**"

                message += "**نیم‌سرورها:\n**"
                name_servers = domain_info.name_servers
                if isinstance(name_servers, list):
                    for nameserver in name_servers:
                        message += f"**- {nameserver}\n**"
                else:
                    message += f"**- {name_servers}\n**"

                message += f"**Status: {domain_info.status}\n**"
            else:
                message = "**برای جستجوی whois نام دامنه را وارد کن.**"

        except Exception as e:
            message = f"**خطا در جستجوی whois برای دامنه {domain}\nخطا: {str(e)}**"

        await event.edit(message)

async def show_crypto_prices(event):
    if event.sender_id == admin_user_id:
        cryptos = {
            'Bitcoin (BTC)': 'bitcoin',
            'Tether (USDT)': 'tether',
            'TRON (TRX)': 'tron',
            'Litecoin (LTC)': 'litecoin',
            'Dogecoin (DOGE)': 'dogecoin'
        }
        prices = {}

        for crypto, symbol in cryptos.items():
            response = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd')
            if response.status_code == 200:
                data = response.json()
                prices[crypto] = data[symbol]['usd']
            else:
                await event.edit(f"**❈ دریافت قیمت {crypto} ممکن نشد.**")
                return

        message = "قیمت ارزهای دیجیتال:\n"
        for crypto, price in prices.items():
            message += f"{crypto}: ${price}\n"

        await event.edit(f"**{message}**")

async def replace_words(event):
    if event.sender_id == admin_user_id:
        if not event.is_reply:
            await event.edit('**❈ برای جایگزینی، روی یک پیام ریپلای کن.**')
            return

        replied_msg = await event.get_reply_message()
        if not replied_msg.text:
            await event.edit('**❈ پیام ریپلای‌شده متنی ندارد.**')
            return

        text = replied_msg.text

        args = event.raw_text.split(' ', 1)
        if len(args) == 2:
            replace_words = args[1].split(',')
            if len(replace_words) == 2:
                word1, word2 = map(str.strip, replace_words)
                replaced_text = text.replace(word1, word2)
                await event.edit(replaced_text)
                return

    await event.edit('**❈ دو کلمه را با کاما جدا کرده وارد کن.**')

async def convert_date(event):
    if event.sender_id == admin_user_id:
        args = event.raw_text.split(' ', 1)
        if len(args) != 2:
            await event.edit(f'**❈ تاریخ معتبر را با این فرمت وارد کن: `/Convertdate yyyy/mm/dd`**')
            return

        try:
            date_str = args[1]
            date = datetime.datetime.strptime(date_str, '%Y/%m/%d').date()

            jalali_date = JalaliDate(date)
            shamsi_date_str = jalali_date.strftime('%Y/%m/%d')

            await event.edit(f'**❈ تاریخ تبدیل‌شده: `{shamsi_date_str}`**')
        except ValueError:
            await event.edit(f'**❈ فرمت تاریخ نامعتبر است. از فرمت yyyy/mm/dd استفاده کن.**')

async def set_user_first_name(event):
    if event.sender_id == admin_user_id:
        text = event.message.text
        _, new_first_name = text.split(' ', 1)
        try:
            await client(functions.account.UpdateProfileRequest(
                first_name=new_first_name
            ))
            await event.edit(f'**❈ نام [شما](tg://user?id={admin_user_id}) با موفقیت تغییر کرد.**')
        except Exception as e:
            await event.edit(f'**❈ خطا در تغییر نام: {str(e)}**')

async def get_football_stats(event):
    if event.sender_id == admin_user_id:
        api_key = '23396b8847eb488c9545aafd07374788'
        url = 'https://api.football-data.org/v4/competitions/BL1/standings'
        headers = {'X-Auth-Token': api_key}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()

                league_name = data['competition']['name']
                start_date = data['season']['startDate'].split('-')[0]
                end_date = data['season']['endDate'].split('-')[0]
                season = f"{start_date} - {end_date}"
                standings = data['standings'][0]['table']

                message = f"لیگ فوتبال: {league_name}\nفصل: {season}\n\n"

                for position, team in enumerate(standings, start=1):
                    team_name = team['team']['name']
                    points = team['points']
                    wins = team['won']
                    draws = team['draw']
                    losses = team['lost']

                    message += f"{position}. {team_name}\n"
                    message += f"امتیاز: {points}، برد: {wins}، مساوی: {draws}، باخت: {losses}\n\n"

                await event.edit(f"**{message}**")
            else:
                await event.edit("**دریافت آمار فوتبال ناموفق بود. بعداً دوباره تلاش کن.**")
        except Exception as e:
            await event.edit(f'**خطا در دریافت آمار بوندسلیگا: {str(e)}**')

async def apply_color_filter(event):
    if event.sender_id == admin_user_id:
        if not event.is_reply:
            await event.edit('**❈ برای اعمال فیلتر رنگ، روی یک عکس ریپلای کن.**')
            return

        replied_msg = await event.get_reply_message()
        if not replied_msg.photo:
            await event.edit('**❈ پیام ریپلای‌شده باید عکس باشد.**')
            return

        command_args = event.message.text.split(' ', 1)
        if len(command_args) != 2:
            await event.edit('**❈ نام رنگ معتبر وارد کن.**')
            return

        color_name = command_args[1].lower()

        colors = {
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'purple': (128, 0, 128),
            'orange': (255, 165, 0),
            'pink': (255, 192, 203),
        }

        if color_name not in colors:
            await event.edit('**❈ نام رنگ نامعتبر است.**')
            return

        color_rgb = colors[color_name]

        photo = await replied_msg.download_media()

        img = Image.open(photo)

        img = img.convert('RGB')
        img = Image.blend(img, Image.new('RGB', img.size, color_rgb), alpha=0.5)

        edited_photo_io = BytesIO()
        img.save(edited_photo_io, 'PNG')
        edited_photo_io.seek(0)

        file_name = f"{color_name.capitalize()}.png"

        caption_text = f"**❈ رنگ فیلتر شد: {color_name.capitalize()}**"
        
        await client.send_file(
            event.chat_id,
            edited_photo_io,
            caption=caption_text,
            force_document=False,
            attributes=[types.DocumentAttributeFilename(file_name)]
        )

        os.remove(photo)
        await event.delete()

async def flood_message(event):
    if event.sender_id == admin_user_id:
        count = int(event.pattern_match.group(1))
        texts = event.pattern_match.group(2).split(',')
        for _ in range(count):
            text = random.choice(texts)
            await event.delete()
            await event.respond(text)
            time.sleep(0.2)

async def replay_as_voice(event):
    if event.sender_id == admin_user_id:
        text = event.pattern_match.group(1)
        language = 'en'
        tts = gTTS(text=text, lang=language)
        voice_file_path = 'voice.mp3'
        tts.save(voice_file_path)
        await event.delete()
        await client.send_file(event.chat_id, voice_file_path, voice_note=True)
        os.remove(voice_file_path)

async def set_music_name(event):
    if event.sender_id == admin_user_id:
        name = event.pattern_match.group(1)
        reply_message = await event.get_reply_message()
        if reply_message and reply_message.media:
            try:
                if reply_message.media and hasattr(reply_message.media, 'document'):
                    await event.edit(f"**❈ در حال دانلود . . . **")
                    music = await client.download_media(reply_message)
                    await event.edit(f"**❈ در حال ارسال . **")
                    await asyncio.sleep(0.5)
                    await event.edit(f"**❈ در حال ارسال . . **")
                    await asyncio.sleep(0.5)
                    await event.edit(f"**❈ در حال ارسال . . . **")
                    file_ext = os.path.splitext(music)[1]
                    new_name = f'{name}{file_ext}'
                    new_music = os.path.join(os.path.dirname(music), new_name)
                    os.rename(music, new_music)

                    duration = 0
                    performer = ''
                    for attr in reply_message.document.attributes:
                        if isinstance(attr, DocumentAttributeAudio):
                            duration = attr.duration
                            performer = attr.performer
                            break

                    await event.reply(
                        file=new_music,
                        attributes=[
                            DocumentAttributeAudio(
                                duration=duration,
                                title=name,
                                performer=performer
                            )
                        ]
                    )
                    os.remove(new_music)
                    await asyncio.sleep(0.5)
                    await event.edit(f"**❈ با موفقیت ارسال شد!**")
                else:
                    await event.edit(f"**❈ روی یک پیام موزیک ریپلای کن.**")
            except FileNotFoundError:
                await event.edit(f"**❈ تغییر نام فایل موزیک ناموفق بود.**")

async def take_screenshot(event):
    if event.sender_id == admin_user_id:
        url = event.pattern_match.group(1)
        file_name = f"screenshot_{event.id}.png"
        try:
            api_key = '863fe7'
            screenshot_api_url = f"https://api.screenshotmachine.com/?key={api_key}&url={url}&dimension=1024x768&format=png"
            response = requests.get(screenshot_api_url)
            response.raise_for_status()
            with open(file_name, "wb") as file:
                file.write(response.content)
            await event.edit(f"**❈ در حال ارسال . **")
            await asyncio.sleep(0.5)
            await event.edit(f"**❈ در حال ارسال . . **")
            await asyncio.sleep(0.5)
            await event.edit(f"**❈ در حال ارسال . . . **")
            await event.reply(file=file_name)
            os.remove(file_name)
            await event.edit(f"**❈ با موفقیت ارسال شد!**")
        except Exception as e:
            await event.reply(f"**❈ گرفتن اسکرین‌شات ناموفق بود: {str(e)}**")


SAVE_DIRECTORY_YT = 'videos'
async def download_youtube_video(event):
    if event.sender_id == admin_user_id:
        video_url = event.pattern_match.group(1)
        await event.edit("**❈ در حال دانلود...**")
        try:
            ydl_opts = {
                'outtmpl': os.path.join(SAVE_DIRECTORY_YT, '%(title)s.%(ext)s'),
                'writethumbnail': True,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                'quiet': True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                file_path = ydl.prepare_filename(info)
                thumbnail_path = info['thumbnails'][0]['url']

            thumbnail_filename = os.path.join(SAVE_DIRECTORY_YT, f'{info["title"]}.webp')
            thumbnail_response = requests.get(thumbnail_path)
            with open(thumbnail_filename, 'wb') as thumbnail_file:
                thumbnail_file.write(thumbnail_response.content)

            await event.reply(
                file=file_path,
                message=f"**❈ [ویدیو]({video_url}) با بالاترین کیفیت برای [شما](tg://user?id={admin_user_id})\nنام: {info.get('title')}**",
                supports_streaming=True,
                thumb=thumbnail_filename
            )

            os.remove(file_path)
            os.remove(thumbnail_filename)

            await event.edit("**❈ با موفقیت انجام شد**")
            await asyncio.sleep(3)
            await event.delete()

        except Exception as e:
            await event.reply(f"دانلود ویدیوی یوتیوب ناموفق بود: {str(e)}")

        thumbnail_filename = os.path.join(SAVE_DIRECTORY_YT, f'{info["title"]}.webp')
        if os.path.exists(thumbnail_filename):
            os.remove(thumbnail_filename)

async def proxy_command(event):
    if event.sender_id == admin_user_id:
        try:
            await event.edit("در حال دریافت پروکسی تصادفی...")
            
            url = "https://yebekhe.github.io/MTProtoCollector/proxy/mtproto.json"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                random_proxies = random.sample(data, min(5, len(data)))
                messages = []
                
                for i, proxy in enumerate(random_proxies):
                    proxy_link = proxy.get('link', '')
                    if proxy_link:
                        messages.append(f"**❈ پروکسی تصادفی {i + 1}:\n**{proxy_link}")
                
                if messages:
                    await event.edit("\n\n".join(messages))
                else:
                    await event.edit("**❈ لینک پروکسی پیدا نشد. بعداً دوباره تلاش کن.**")
            else:
                await event.edit("**❈ پاسخ سرور خالی یا نامعتبر است. بعداً دوباره تلاش کن.**")
        except Exception as e:
            await event.edit(f"خطایی رخ داد: {str(e)}")

async def v2ray_command(event):
    if event.sender_id == admin_user_id:
        try:
            await event.edit("در حال دریافت کانفیگ‌های VLESS...")
            
            url = "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/reality"
            response = requests.get(url)
            response.raise_for_status()
            data = response.text.split('\n')
            
            vless_configs = [config.strip() for config in data if config.startswith('vless://')]
            random_configs = random.sample(vless_configs, min(5, len(vless_configs)))
            
            if random_configs:
                messages = [f"**❈ کانفیگ تصادفی VLESS {i + 1}:\n `{config}`**" for i, config in enumerate(random_configs)]
                
                await event.edit("\n\n".join(messages))
            else:
                await event.edit("**❈ فعلاً کانفیگ VLESS پیدا نشد. بعداً دوباره تلاش کن.**")
        except Exception as e:
            await event.edit(f"خطایی رخ داد: {str(e)}")


timezone_cache = {}
async def get_world_time(event):
    if event.sender_id == admin_user_id:
        city_name = event.pattern_match.group(1).capitalize()

        timezone = timezone_cache.get(city_name)
        if not timezone:
            geolocator = Nominatim(user_agent="world_time_bot")
            location = geolocator.geocode(city_name, exactly_one=True, featuretype="P")

            if location:
                tf = TimezoneFinder()
                timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)

                if timezone_str:
                    timezone = pytz.timezone(timezone_str)
                    timezone_cache[city_name] = timezone
                else:
                    reply_message = f"متأسفانه منطقه زمانی {city_name} پیدا نشد"
                    await event.edit(f"**❈{reply_message}**")
                    return
            else:
                reply_message = f"متأسفانه موقعیت {city_name} پیدا نشد"
                await event.edit(f"**❈{reply_message}**")
                return

        current_time = datetime.datetime.now(timezone)
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        reply_message = f"ساعت فعلی در {city_name}: {formatted_time}"

        await event.edit(f"**❈{reply_message}**")


timers = {}
def load_timers():
    if os.path.exists("settings/timers.json"):
        with open("settings/timers.json", "r") as file:
            timers.update(json.load(file))

def save_timers():
    with open("settings/timers.json", "w") as file:
        json.dump(timers, file)

async def create_timer(event):
    if event.sender_id == admin_user_id:
        timer_name = event.pattern_match.group(1)
        timers[timer_name] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_timers()
        await event.edit(f"**❈ تایمر `{timer_name}` ساخته شد.**")

async def delete_timer(event):
    if event.sender_id == admin_user_id:
        timer_name = event.pattern_match.group(1)
        if timer_name in timers:
            del timers[timer_name]
            save_timers()
            await event.edit(f"**❈ تایمر `{timer_name}` حذف شد.**")
        else:
            await event.edit(f"**❈ تایمر `{timer_name}` پیدا نشد.**")

async def list_timers(event):
    if event.sender_id == admin_user_id:
        if timers:
            reply_message = "**لیست تایمرهای ذخیره‌شده:**\n"
            for i, (timer_name, start_time) in enumerate(timers.items(), start=1):
                time_elapsed = datetime.datetime.now() - datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                days = time_elapsed.days
                hours, remainder = divmod(time_elapsed.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                reply_message += f"**{i} - {timer_name}:**\n `{days} روز، {hours} ساعت، {minutes} دقیقه، {seconds} ثانیه`\n"
            await event.edit(reply_message)
        else:
            await event.edit("**❈ تایمری وجود ندارد.**")

async def clean_timers(event):
    if event.sender_id == admin_user_id:
        timers.clear()
        save_timers()
        await event.edit(f"**❈ همه تایمرها حذف شدند.**")

async def download_file(event):
    if event.sender_id == admin_user_id:
        file_url = event.pattern_match.group(1)
        try:
            response = requests.head(file_url)
            if response.status_code == 200 and 'content-length' in response.headers:
                file_size = int(response.headers['content-length'])

                if file_size <= 200 * 1024 * 1024:
                    download_msg = await event.edit("**❈ در حال دانلود فایل...**")
                    file_name = file_url.split("/")[-1]
                    response = requests.get(file_url, stream=True)
                    with open(file_name, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                file.write(chunk)

                    await client.send_file(event.chat_id, file=file_name, caption=f"**❈ آدرس فایل دانلودشده: `{file_url}`**")
                    await download_msg.delete()
                    os.remove(file_name)
                else:
                    await event.edit("**❈ حجم فایل از حد مجاز (`۲۰۰ مگابایت`) بیشتر است.**")
            else:
                await event.edit("**❈ آدرس نامعتبر یا غیرقابل دسترس است.**")
        except Exception as e:
            await event.edit(f"**❈ خطا در دانلود فایل: {str(e)}**")

async def get_ip_info(event):
    if event.sender_id == admin_user_id:
        ip = event.pattern_match.group(1)
        try:
            response = requests.get(f"https://ipinfo.io/{ip}/json")
            data = response.json()
            
            if "ip" in data:
                ip_address = data["ip"]
                city = data.get("city", "")
                region = data.get("region", "")
                country = data.get("country", "")
                org = data.get("org", "")
                
                reply_message = f"**آی‌پی:** `{ip_address}`\n"
                reply_message += f"**شهر:** `{city}`\n" if city else ""
                reply_message += f"**منطقه:** `{region}`\n" if region else ""
                reply_message += f"**کشور:** `{country}`\n" if country else ""
                reply_message += f"**سازمان:** `{org}`\n" if org else ""
                
                await event.edit(reply_message)
            else:
                await event.edit(f"**❈ دریافت اطلاعات آی‌پی ناموفق بود: `{ip}`.**")
                
        except requests.exceptions.RequestException as e:
            await event.edit(f"**❈ خطا در دریافت اطلاعات آی‌پی: `{str(e)}`**")

EXSAVE_DIRECTORY = 'extracted_files'
async def extract_files(event):
    if event.is_reply and event.sender_id == admin_user_id:
        reply_message = await event.get_reply_message()
        if reply_message.media and reply_message.media.document.mime_type == 'application/zip':
            try:
                await event.edit("**❈ در حال استخراج فایل‌ها...**")
                zip_file = await event.client.download_media(reply_message)
                extracted_files = await extract_zip_files(zip_file)
                await delete_files(zip_file)
                await send_extracted_files(event, extracted_files)
                await event.edit("**❈ فایل‌های استخراج‌شده با موفقیت ارسال شدند**")
                await delete_extracted_files(extracted_files)
            except Exception as e:
                await event.edit(f"**❈ استخراج و ارسال فایل‌ها ناموفق بود: {str(e)}**")
        else:
            await event.respond("**❈ برای استخراج، روی یک فایل zip ریپلای کن.**")

async def extract_zip_files(zip_file_path):
    extracted_files = []
    if not os.path.exists(EXSAVE_DIRECTORY):
        os.makedirs(EXSAVE_DIRECTORY)
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(EXSAVE_DIRECTORY)
        extracted_files = zip_ref.namelist()
    return extracted_files

async def delete_files(zip_file):
    if os.path.isfile(zip_file):
        os.remove(zip_file)

async def send_extracted_files(event, extracted_files):
    for file_name in extracted_files:
        file_path = os.path.join(EXSAVE_DIRECTORY, file_name)
        if os.path.isfile(file_path):
            await event.respond(file=file_path)
            await asyncio.sleep(1)

async def delete_extracted_files(extracted_files):
    for file_name in extracted_files:
        file_path = os.path.join(EXSAVE_DIRECTORY, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)
    shutil.rmtree(EXSAVE_DIRECTORY)

TV_CHANNELS = {
    'شبکه ۱': 'https://telewebion.com/live/tv1',
    'شبکه ۲': 'https://telewebion.com/live/tv2',
    'شبکه ۳': 'https://telewebion.com/live/tv3',
    'شبکه ۴': 'https://telewebion.com/live/tv4/',
    'شبکه ۵': 'https://telewebion.com/live/tv5/',
    'رادیو جوان': 'https://mrtv.me/playonline/?id=58&media=cjlKejM3ZlljWXBoS1l4QU80dllzR0RLaTJhT1VLaGNLbUM1S2RpUGUwZFMxU3dRWU42YStSQnJaV2gzMUZzRG5FOXh4SUphS0FtdktaWEJvZlYyUWc9PQ==&subtitle=RTBrZUxqQUJESEEvZy83alpXQ1pDUT09&quality1=&quality2=&quality3=',
    'شبکه نسیم': 'https://telewebion.com/live/nasim/',
    'شبکه ورزش': 'https://telewebion.com/live/varzesh/',
    'شبکه پویا': 'https://telewebion.com/live/pooya/',
    'شبکه سلامت': 'https://telewebion.com/live/salamat/',
}

async def send_tv_channels(event):
    if event.sender_id == admin_user_id :
        channel_list = '\n'.join([f'• {channel}: [تماشا]({link})' for channel, link in TV_CHANNELS.items()])
        message = f"شبکه‌های زنده تلویزیون ایران:\n\n{channel_list}"
        await event.edit(message, link_preview=False)

async def create_qr_code(event):
    if event.sender_id == admin_user_id:
        command = event.raw_text.lower()
        if "به qr" in command or "sqr" in command:
            qr_data = command.replace("به qr", "").replace("sqr", "").strip()
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img.save("qr_code.png")
            await event.edit("**❈ QR کد با موفقیت ساخته شد!**")
            await client.send_file(event.chat_id, "qr_code.png")
            os.remove("qr_code.png")

async def read_qr_code(event):
    if event.is_reply and event.sender_id == admin_user_id:
        replied_msg = await event.get_reply_message()
        if replied_msg.photo:
            try:
                photo = await replied_msg.download_media()

                files = {'file': open(photo, 'rb')}
                url = 'https://zxing.org/w/decode'
                response = requests.post(url, files=files)

                os.remove(photo)

                if response.ok:
                    content = re.search(r'<pre>(.*?)</pre>', response.text)
                    if content:
                        qr_data = content.group(1)
                        await event.edit(f"**❈ محتوای QR کد: {qr_data}**")
                    else:
                        await event.edit("**❈ محتوایی در QR کد پیدا نشد.**")
                else:
                    await event.edit("**❈ خطا در خواندن QR کد.**")
            except Exception as e:
                await event.edit(f"خطا: {str(e)}")
        else:
            await event.edit("**❈ روی پیامی که عکس QR کد دارد ریپلای کن.**")
    else:
        await event.edit("**❈ روی یک پیام ریپلای کن و /readqr را بزن تا QR کد خوانده شود.**")

async def clean_messages_containing_text(event):
    if event.sender_id == admin_user_id:
        command = event.raw_text.lower()
        if "پاکسازی همه" in command or "cleanall" in command:
            text_to_clean = command.split(maxsplit=1)[1].strip()
            if text_to_clean:
                async for message in client.iter_messages(event.chat_id):
                    if message.text and text_to_clean in message.text:
                        await message.delete()
                await event.respond(f"**❈ همه پیام‌های حاوی «{text_to_clean}» حذف شدند.**")
            else:
                await event.edit("**❈ متنی که می‌خواهی جستجو و حذف شود را بنویس.**")

async def join_all_channels(event):
    if event.sender_id == admin_user_id:
        try:
            replied_to_msg = await event.get_reply_message()
            if replied_to_msg and replied_to_msg.reply_markup:
                joined_channels = 0
                for row in replied_to_msg.reply_markup.rows:
                    for button in row.buttons:
                        if button.url:
                            try:
                                entity = await client.get_entity(button.url)
                                if isinstance(entity, types.Channel):
                                    try:
                                        await client(functions.channels.JoinChannelRequest(channel=entity))
                                        await event.edit(f"عضویت در {entity.title}")
                                        joined_channels += 1
                                        await asyncio.sleep(5)  # Delay to prevent rate limits and avoid flooding
                                    except Exception as join_error:
                                        await event.edit(f"عضویت ممکن نشد: {entity.title}: {str(join_error)}. لطفاً دستی عضو شو: {button.url}")
                                        await asyncio.sleep(10)  # Adding delay to prevent flooding
                                        continue
                                else:
                                    await event.edit(f"{entity.title} کانال نیست.")
                            except Exception as entity_error:
                                await event.edit(f"خطا: {str(entity_error)}")
                        else:
                            await event.edit("لینکی در دکمه‌های شیشه‌ای پیدا نشد.")
                
                if joined_channels > 0:
                    await event.edit(f"عضویت در {joined_channels} کانال با موفقیت انجام شد!")
                else:
                    await event.edit("در هیچ کانالی عضو نشدی.")
            
            else:
                await event.edit("روی پیامی که دکمه‌های عضویت کانال دارد ریپلای کن.")
        except Exception as e:
            await event.edit(f"خطایی رخ داد: {str(e)}")

async def set_bot_username(event):
    if event.sender_id == admin_user_id:
        try:
            command_parts = event.raw_text.split(maxsplit=2)
            new_username = command_parts[1]
            
            if not new_username:
                await event.edit(f"**❈ یوزرنیم جدید معتبری وارد کن.**")
                return
            
            try:
                await event.client.get_entity(f'@{new_username}')
                await event.edit(f"**❈ این یوزرنیم قبلاً گرفته شده است. یکی دیگر انتخاب کن.**")
            except Exception:
                await event.client(functions.account.UpdateUsernameRequest(new_username))
                await event.edit(f"**❈ یوزرنیم شما تغییر کرد: @{new_username}**")
        except Exception as e:
            await event.edit(f"خطایی رخ داد: {str(e)}")

async def kick_users(event):
    if event.sender_id == admin_user_id:
        try:
            command_parts = event.raw_text.split()
            users_to_kick = command_parts[1:]
            
            if users_to_kick:
                chat = await event.get_chat()
                chat_id = chat.id
                
                user_ids_to_kick = []
                
                for user_to_kick in users_to_kick:
                    async for user in event.client.iter_participants(chat_id):
                        if isinstance(user, types.User) and (
                            user.username == user_to_kick.lstrip('@') or
                            str(user.id) == user_to_kick
                        ):
                            user_ids_to_kick.append(user.id)
                
                # Kick the users
                if user_ids_to_kick:
                    await event.edit("**❈ در حال اخراج کاربران...**")
                    for user_id in user_ids_to_kick:
                        await event.client(functions.channels.EditBannedRequest(
                            chat_id,
                            user_id,
                            banned_rights=types.ChatBannedRights(
                                until_date=None,
                                view_messages=True,
                                send_messages=True,
                                send_media=True,
                                send_stickers=True,
                                send_gifs=True,
                                send_games=True,
                                send_inline=True,
                                embed_links=True,
                            ),
                        ))
                    await event.edit("**❈ کاربران با موفقیت اخراج شدند!**")
                else:
                    await event.edit("**❈ کاربر معتبری برای اخراج پیدا نشد.**")
            else:
                await event.edit("**❈ یوزرنیم یا شناسه عددی کاربران را برای اخراج وارد کن.**")
        except Exception as e:
            await event.edit(f"خطایی رخ داد: {str(e)}")

async def clean_between_messages(event):
    if event.sender_id == admin_user_id:
        command = event.raw_text.lower()
        if "پاکسازی بین" in command or "cleanb" in command:
            command_parts = command.split()
            if len(command_parts) == 3:
                link1 = command_parts[1]
                link2 = command_parts[2]

                try:
                    message_id1 = int(link1.split('/')[-1])
                    message_id2 = int(link2.split('/')[-1])

                    async for message in client.iter_messages(event.chat_id, min_id=message_id1, max_id=message_id2):
                        await message.delete()

                    await event.edit("**❈ پیام‌های بین دو لینک حذف شدند.**")
                except Exception as e:
                    await event.respond(f"خطایی رخ داد: {str(e)}")
            else:
                await event.reply("**❈ دو لینک پیام را برای حذف پیام‌های بینشان وارد کن.**")


async def Git(event):
    if event.sender_id == admin_user_id:
        message = event.message.message
        repo_link_match = re.search(r'(https://github\.com/[\w\-\.]+/[\w\-\.]+)', message)
        
        if repo_link_match:
            await event.delete()
            repo_link = repo_link_match.group(1)
            user, repo = repo_link.split('/')[-2:]
            response = requests.get(f'https://api.github.com/repos/{user}/{repo}')
            if response.status_code == 200:
                repo_data = response.json()
                zip_url = repo_data['html_url'] + '/archive/refs/heads/' + repo_data['default_branch'] + '.zip'
                zip_response = requests.get(zip_url, stream=True)
                zip_file = f'{repo}-{repo_data["default_branch"]}.zip'
                with open(zip_file, 'wb') as f:
                    shutil.copyfileobj(zip_response.raw, f)
                caption = (
                    f"کاربر: **[{user}]({repo_data['owner']['html_url']})** \n"
                    f"**ستاره‌ها:** ( {repo_data['stargazers_count']} ⭐)\n"
                    f"**نام ریپازیتوری:** {repo}\n"
                    f"**زبان:** {repo_data['language']}\n"
                    f"کلون: ( `git clone {repo_data['clone_url']}&&cd {repo}` )\n"
                    f"توضیحات:\n {repo_data['description']}"
                )
                await client.send_file(event.chat_id, zip_file, caption=caption, force_document=True)
                os.remove(zip_file)
            else:
                await event.edit("**❈ دریافت اطلاعات ریپازیتوری ناموفق بود. از درستی لینک مطمئن شو.**")
        else:
            await event.reply("**❈ لینک معتبر ریپازیتوری گیت‌هاب را وارد کن.**")


async def copycontent(event):
    if event.sender_id == admin_user_id:
        message_text = event.raw_text
        url_match = re.search(r'https://t\.me/(\S+)/(\d+)', message_text)
        if url_match:
            channel_username = url_match.group(1)
            message_id = int(url_match.group(2))
            try:
                message = await client.get_messages(channel_username, ids=message_id)
                if message and message.media:
                    media_path = await client.download_media(message.media)
                    await client.send_file(admin_user_id, media_path)
                    await event.edit("**❈ رسانه ارسال شد**")
                    os.remove(media_path)
                else:
                    await event.edit("**❈ پیام موردنظر رسانه ندارد.**")
            except Exception as e:
                await event.edit(f"**❈ دریافت پیام ناموفق بود. خطا: {str(e)}**")
        else:
            await event.edit("**❈ بعد از دستور، لینک معتبر پست تلگرام را وارد کن.**")

async def read_all_pvs(event):
    if event.sender_id == admin_user_id:
        async for dialog in client.iter_dialogs():
            if dialog.is_user:
                await client.send_read_acknowledge(dialog.id)
        await event.edit("**❈ همه پیام‌های خصوصی خوانده‌شده شدند.**")

async def read_all_groups(event):
    if event.sender_id == admin_user_id:
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                await client.send_read_acknowledge(dialog.id)
        await event.edit("**❈ همه پیام‌های گروه‌ها خوانده‌شده شدند.**")

async def read_all_channels(event):
    if event.sender_id == admin_user_id:
        async for dialog in client.iter_dialogs():
            if dialog.is_channel:
                await client.send_read_acknowledge(dialog.id)
        await event.edit("**❈ همه پیام‌های کانال‌ها خوانده‌شده شدند.**")

async def read_all_bots(event):
    if event.sender_id == admin_user_id:
        async for dialog in client.iter_dialogs():
            if dialog.entity.bot:
                await client.send_read_acknowledge(dialog.id)
        await event.edit("**❈ همه پیام‌های ربات‌ها خوانده‌شده شدند.**")

typing_status = {}
async def start_typing(event):
    if event.sender_id == admin_user_id:
        chat_id = event.chat_id
        typing_status[chat_id] = True
        await event.delete()
        await client.send_message(admin_user_id,f"**❈ حالت در حال تایپ روشن شد در** [چت](tg://user?id={chat_id})")

        while typing_status.get(chat_id, False):
            async with client.action(chat_id, 'typing'):
                await asyncio.sleep(5)

async def stop_typing(event):
    if event.sender_id == admin_user_id:
        chat_id = event.chat_id
        typing_status[chat_id] = False
        await event.delete()
        await client.send_message(admin_user_id,f"**❈ حالت در حال تایپ خاموش شد در** [چت](tg://user?id={chat_id})")

sticker_status = {}
async def start_sticker(event):
    if event.sender_id == admin_user_id:
        chat_id = event.chat_id
        sticker_status[chat_id] = True
        await event.delete()
        await client.send_message(admin_user_id,f"**❈ حالت ارسال استیکر روشن شد در** [چت](tg://user?id={chat_id})")

        while sticker_status.get(chat_id, False):
            async with client.action(chat_id, 'sticker'):
                await asyncio.sleep(5)

async def stop_sticker(event):
    if event.sender_id == admin_user_id:
        chat_id = event.chat_id
        sticker_status[chat_id] = False
        await event.delete()
        await client.send_message(admin_user_id,f"**❈ حالت ارسال استیکر خاموش شد در** [چت](tg://user?id={chat_id})")

game_status = {}
async def start_game(event):
    if event.sender_id == admin_user_id:
        chat_id = event.chat_id
        game_status[chat_id] = True
        await event.delete()
        await client.send_message(admin_user_id,f"**❈ حالت بازی روشن شد در** [چت](tg://user?id={chat_id})")

        while game_status.get(chat_id, False):
            async with client.action(chat_id, 'game'):
                await asyncio.sleep(5)

async def stop_game(event):
    if event.sender_id == admin_user_id:
        chat_id = event.chat_id
        game_status[chat_id] = False
        await event.delete()
        await client.send_message(admin_user_id,f"**❈ حالت بازی خاموش شد در** [چت](tg://user?id={chat_id})")

async def delete_media(event, media_type):
    if event.sender_id == admin_user_id:
        if event.is_private or event.is_group:
            chat_id = event.chat_id
            deleted_count = 0

            async for message in client.iter_messages(chat_id, reverse=True):
                if media_type == 'gif' and message.gif:
                    await message.delete()
                    deleted_count += 1
                elif getattr(message, media_type, None):
                    await message.delete()
                    deleted_count += 1

            await event.edit(f"**❈ حذف شد: {deleted_count} {media_type}(s).**")

async def pvinfo(event):
    if event.sender_id == admin_user_id:
        chat_id = event.chat_id
        try:
            total_messages = 0
            total_media = 0
            total_voices = 0
            total_videos = 0
            total_photos = 0
            total_documents = 0

            async for message in client.iter_messages(chat_id):
                total_messages += 1
                if message.media:
                    total_media += 1
                    if hasattr(message.media, 'document'):
                        if 'video/mp4' in message.media.document.mime_type:
                            total_videos += 1
                        elif 'audio' in message.media.document.mime_type:
                            total_voices += 1
                        else:
                            total_documents += 1
                    elif hasattr(message.media, 'photo'):
                        total_photos += 1

            response = (
                f"**آمار چت:** \n"
                f"**کل پیام‌ها:** `{total_messages}`\n"
                f"**کل رسانه‌ها:** `{total_media}` \n"
                f"**کل عکس‌ها:** `{total_photos}` \n"
                f"**کل ویدیوها:** `{total_videos}` \n"
                f"**کل پیام‌های صوتی:** `{total_voices}` \n"
                f"**کل فایل‌ها:** `{total_documents}` \n"
            )

            await event.edit(response)
        except ValueError as e:
            await event.edit(f"**❈ متأسفانه اطلاعات این چت دریافت نشد. مطمئن شو دسترسی لازم را داری و قبلاً با این چت یا کاربر تعامل داشته‌ای.**")


async def check_domain(event):
    if event.sender_id == admin_user_id:
        await event.edit(f"**❈ در انتظار . . . **")
        message = event.message.message
        domain = message.split(' ')[1] if len(message.split(' ')) > 1 else ''
        if domain:
            url = f'https://api.ineo-team.ir/domainChecker.php?domain={domain}'
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and data.get('status') == 'successfully.':
                    result = data.get('result')
                    if result:
                        reply = f"**{domain} وضعیت :** \n"
                        for tld, info in result.items():
                            reply += f"**{info['domain']}** : `{info['status']['type']}` \n"
                        await event.edit(reply)
                else:
                    await event.edit("**❈ دریافت اطلاعات دامنه ناموفق بود.**")
            else:
                await event.edit("**❈ اتصال به سرویس بررسی دامنه ناموفق بود.**")
        else:
            await event.edit("**❈ بعد از دستور، نام دامنه را وارد کن.**")

async def logout(event):
    if event.sender_id == admin_user_id:
        confirmation_msg = await event.edit("**❈ مطمئنی می‌خواهی خارج شوی؟ برای تأیید بنویس: yes یا بله**")
        
        try:
            for _ in range(30):
                reply = await client.get_messages(entity=event.chat_id, limit=1)
                if reply and reply[0].message.strip().lower() in ('yes', 'بله'):
                    await reply[0].delete()
                    break
                await asyncio.sleep(1)
            else:
                await confirmation_msg.edit("**❌ زمان درخواست خروج تمام شد.**")
                return
        
        except Exception as e:
            print(e)
        
        await confirmation_msg.edit("**❈ در حال خروج...**")
        await asyncio.sleep(3)
        await client.log_out()

def clear_pic_folder():
    files = os.listdir(pic_folder)
    for file in files:
        os.remove(os.path.join(pic_folder, file))

async def tpic_set(event):
    if event.sender_id == admin_user_id:
        try:
            clear_pic_folder()
            if event.is_reply:
                replied_msg = await event.get_reply_message()
                if replied_msg.photo:
                    photo = await client.download_media(replied_msg.photo, pic_folder + 'profile.jpg')
                    await event.edit("**❈ در حال انجام . . .**")
                    if replied_msg.raw_text and '[' in replied_msg.raw_text and ']' in replied_msg.raw_text:
                        caption = replied_msg.raw_text
                        coordinates = [int(coord) for coord in caption[caption.index('[') + 1: caption.index(']')].split(',')]
                        color = caption[caption.index('{') + 1: caption.index('}')]
                        with open('settings/tpic.json', 'w') as f:
                            json.dump({'cordx': coordinates[0], 'cordy': coordinates[1], 'size': coordinates[2], 'color': color}, f)
                        await event.edit("**❈ همه چیز انجام شد ✅**")
        except Exception as e:
            print(f"خطایی رخ داد: {e}")

async def tpic_prv(event):
    if event.sender_id == admin_user_id:
        try:
            await event.delete()
            with open('settings/tpic.json', 'r') as f:
                data = json.load(f)
                cordx = data['cordx']
                cordy = data['cordy']
                size = data['size']
                color_string = data['color']
            with Image.open('pic/profile.jpg') as img:
                draw = ImageDraw.Draw(img)
                font_path = 'fonts/Freshman.ttf'
                font_size = size
                font = ImageFont.truetype(font_path, font_size)
                color = color_string
                position = (cordx, cordy)
                draw.text(position, "TEST", fill=color, font=font)
                img.save('pic/profile_test.jpg', quality=95)
                with open('pic/profile_test.jpg', 'rb') as f:
                    await client.send_file(event.chat_id, f, caption=f"cordx : {cordx}\ncordy : {cordy}\nsize :{size}\ncolor : {color}")
                os.remove('pic/profile_test.jpg')
        except:
            await event.edit("**❈ مشکلی پیش آمد.**")

##########################################################################################
patterns_actions = {
    'timename on': ('settings/time.txt', 'True', '**❈ ساعت در نام روشن شد!**'),
    'timename off': ('settings/time.txt', 'False', '**❈ ساعت در نام خاموش شد!**'),
    'timepic on': ('settings/timepic.txt', 'True', '**❈ ساعت روی عکس روشن شد!**'),
    'timepic off': ('settings/timepic.txt', 'False', '**❈ ساعت روی عکس خاموش شد!**'),
    'bio on': ('settings/bioinfo.txt', 'True', '**❈ بیوی پویا روشن شد!**'),
    'bio off': ('settings/bioinfo.txt', 'False', '**❈ بیوی پویا خاموش شد!**'),
    'bold on': ('settings/mode.txt', 'Bold', '**❈ فونت بولد فعال شد!**'),
    'mini on': ('settings/mode.txt', 'Mini', '**❈ فونت کوچک فعال شد!**'),
    'rnd on': ('settings/mode.txt', 'rnd', '**❈ فونت تصادفی فعال شد!**'),
    'default on': ('settings/mode.txt', 'Default', '**❈ فونت پیش‌فرض فعال شد!**'),
    'mono on': ('settings/mode.txt', 'Mono', '**❈ فونت مونو فعال شد!**'),
    'heart on': ('settings/heart.txt', 'True', '**❈ قلب روشن شد!**'),
    'heart off': ('settings/heart.txt', 'False', '**❈ قلب خاموش شد!**'),
    'rname on': ('settings/rnamest.txt', 'True', '**❈ نام تصادفی روشن شد!**'),
    'rname off': ('settings/rnamest.txt', 'False', '**❈ نام تصادفی خاموش شد!**'),
    'see rname': ('settings/rname.txt', None, '**❈ نام‌های تصادفی : \n**'),
    'see bio': ('settings/bio.txt', None, '**❈ بیوی شما : \n**'),
    'see lname': ('settings/nameinfo.txt', None, '❈ نام خانوادگی شما : \n'),
    'farsi on': ('settings/mode.txt', 'Farsi', '**❈ فونت فارسی فعال شد.**'),
    'fancy on': ('settings/mode.txt', 'Fancy', '**❈ فونت فانتزی فعال شد.**'),
    'circle on': ('settings/mode.txt', 'Circle', '**❈ فونت دایره‌ای فعال شد.**')
}
async def settings(event):
    if event.sender_id == admin_user_id:
        pattern = event.pattern_match.string
        file_path, content, response = patterns_actions[pattern]

        if content is not None:
            with open(file_path, 'w') as f:
                f.write(content)

        if pattern == 'timename off':
            await client(UpdateProfileRequest(last_name=''))

        if pattern == 'timename on':
            await client(UpdateProfileRequest(last_name=f'{current_time_str}'))

        if pattern == 'bio off':
            await client(UpdateProfileRequest(about=''))
        
        if pattern == 'timepic off':
            photos = await client.get_profile_photos('me')
            await client(functions.photos.DeletePhotosRequest(id=[InputPhoto(id=photos[0].id, access_hash=photos[0].access_hash, file_reference=photos[0].file_reference)]))


        if file_path.endswith('.txt'):
            with open(file_path, 'r') as f:
                file_content = f.read()
            if file_content not in ["True", "False", "Bold", "Mono", "Default", "Mini", "rnd"]:
                response += f"`{file_content}`"

        await event.edit(response)
