# Telegram Self Project - Render Ready

این نسخه برای اجرای سلف تلگرام روی Render مرتب شده است.

## نکات مهم
- برای Render از `SESSION_STRING` استفاده کنید. مقدار آن را داخل GitHub یا فایل پروژه قرار ندهید.
- `SESSION_STRING` باید مربوط به همان اکانت تلگرام و یک session معتبر باشد.
- `ADMIN_USER_ID` شناسه عددی ادمین است.
- `HELPER_USERNAME` بدون `@` تنظیم شود.
- `SUPPORT_USERNAME` بدون `@` تنظیم شود.

## متغیرهای Render
```text
API_ID
API_HASH
BOT_TOKEN
ADMIN_USER_ID
SESSION_STRING
HELPER_USERNAME=Sa1selfbot
SUPPORT_USERNAME=Saleh681
```

## اجرا
```text
Build: pip install -r requirements.txt
Start: python main.py
```

نسخه فعلی Startup غیرتعاملی دارد و روی Render منتظر شماره تلفن یا کد ورود نمی‌ماند.

## قابلیت‌های اصلی
پنل Helper، خوشامدگویی Saved Messages، مدیریت پروفایل، فونت زمان، بیو پویا، نام رندوم، ضدحذف و کش رسانه، پیام ویرایش‌شده، Ghost، اسپویلر، آمار، تایمر، زمان‌بند، ابزارهای رسانه و دستورات متنوع موجود در پروژه اصلی.

## Advanced features added

- Auto-read mode: `/autoread on|off`
- Auto-reply mode: `/autoreply on|off` and `/autoreply text ...`
- Away/offline mode: `/away on|off` and `/away text ...`
- Smart secretary: `/secretary on|off`
- Animated messages: `/anim your text`
- Clock styles for dynamic name/bio time: `/clock classic|bold|circle|double|farsi|mini`
- File rename: reply to a file with `/renamefile NewName.ext`
- File cover: reply to a file with `/filecover`, then send a photo
- Event-log destination: run `/setlogchat` inside the target group
- Contact/profile snapshots are checked every 5 minutes and changes are sent to the event-log chat
- Edit/delete and anti-delete notifications can be routed to the event-log chat instead of Saved Messages
- The helper bot `/panel` can be opened in multiple chats/messages.

### Event-log group

For the private group you want to use for notifications, make sure the self account is already a member, open that group, and send `/setlogchat`. The self client stores the chat ID immediately and also keeps one small configuration marker in Saved Messages so the destination can be restored after a Render restart. The actual anti-delete/edit/delete/profile logs go to the configured chat, not Saved Messages.

The invite URL alone is not enough to safely send messages to a private group. The account must already have access to the group.


### Automatic event-log destination
You can set `LOG_CHAT_ID` in Render for a fixed destination, or simply send `/setlogchat` inside the target chat. `/setlogchat` now works from the self client and persists the selected destination through a small Saved Messages configuration marker. The actual anti-delete, edit/delete, and contact/profile alerts are sent to the selected chat, not Saved Messages.
