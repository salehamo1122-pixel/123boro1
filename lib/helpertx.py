from .library import *
from .Information import *


def _help_page(title, lines):
    return "**❈ " + title + "**\n\n" + "\n".join(lines)


async def help_1(event):
    panel = _help_page("Profile & Core Commands", [
        "`timename` on|off : Enable or disable time in your name.",
        "`timepic` on|off : Enable or disable time in your profile picture.",
        "`mini` on : Enable mini font.",
        "`bio` on|off : Enable or disable dynamic bio.",
        "`default` on : Use the default font.",
        "`bold` on : Use bold font.",
        "`mono` on : Use mono font.",
        "`heart` on|off : Enable or disable random hearts.",
        "`rname` on|off : Enable or disable random names.",
        "`see rname` : Show random names.",
        "`see bio` : Show the current bio.",
        "`/addbio` (time,DATE,heart) [text] : Add a bio template.",
        "`/addlname` (time,heart) [text] : Set the last-name template.",
        "`/addrname` [name1,name2,...] : Set random names.",
        "`/delrname` : Delete random names.",
        "`see lname` : Show the last-name template.",
        "`/ping` : Show response time.",
        "`/mem` : Show current memory usage.",
        "`/gmusic` [query] : Search for music and download the available preview.",
        "`/tarikh` : Show today's date.",
        "`/gmsg` [message] : Type a message character by character.",
        "`/weather` [city] : Show current weather information.",
        "`/info` [@username] : Get user information.",
        "`/setprof` : Set the profile picture by replying to an image.",
        "`/rinfo` : Get user information by replying to their message.",
    ])
    await event.edit(panel)


async def help_2(event):
    panel = _help_page("Group & Utility Commands", [
        "`/backupchat` : Back up chat history and media.",
        "`/create_channel` : Create a new channel or group.",
        "`/calc` : Perform simple calculations.",
        "`/silent` : Put a replied user into silent mode.",
        "`/unsilent` : Remove a user from silent mode.",
        "`/tag` : Tag group members.",
        "`/Del` : Delete the replied message.",
        "`/GSilent` : Silence a user in a group.",
        "`/GUnSilent` : Remove group silence.",
        "`/promote` : Promote a user to admin.",
        "`/demote` : Remove a user's admin status.",
        "`/Gmedia` : Save replied video/media for later use.",
        "`/Ggit` [repo link] : Download a GitHub repository.",
        "`/copycontent` [post link] : Save channel posts when forwarding is restricted.",
        "`tpic` (`set` | `prv`) : Set or preview the time profile picture.",
        "`/logout` : Log out the self client.",
        "`/chkdomain` [domain] : Check domain availability.",
    ])
    await event.edit(panel)


async def help_3(event):
    panel = _help_page("Media, Search & Network Commands", [
        "`/Smedia` [Name] : Send saved media by name.",
        "`/Lmedia` : List saved media.",
        "`/Freplay` [add|remove] : Manage fast replies.",
        "`/Lreplay` : List fast replies.",
        "`/whois` [domain] : Get domain information.",
        "`/Scrypto` : Get cryptocurrency prices.",
        "`/sreplace` [key1],[key2] : Replace text in a replied message.",
        "`/Convertdate` [date] : Convert a Gregorian date to Jalali.",
        "`/randnum` [num1]-[num2] : Generate a random number.",
        "`/setname` [name] : Change your first name.",
        "`/sfootball` : Show Bundesliga team status.",
        "`/setcolor` [color] : Apply a color filter to a replied photo.",
        "`/flood` [number] - [text1,text2,...] : Send random messages from the supplied list.",
        "`/orcen` [ENtext] : Convert text to voice.",
        "`/setfname` [name] : Rename a replied music file.",
        "`/screen` [domain] : Take a screenshot of a website.",
        "`/yt` [YouTube link] : Download and send a YouTube video.",
        "`/Sproxy` : Get a free proxy.",
        "`/Sv2ray` : Get a V2Ray server.",
    ])
    await event.edit(panel)


async def help_4(event):
    panel = _help_page("Advanced Commands", [
        "`/time` [capital] : Show the time for a country capital.",
        "`newtimer` [name] : Create a named timer.",
        "`deltimer` [name] : Delete a timer.",
        "`timers` : List timers.",
        "`clean timers` : Delete all timers.",
        "`gfile` [link] : Download a file from a link.",
        "`getip` [ip] : Get IP information.",
        "`/sunextract` : Extract a replied ZIP file.",
        "`Stv` : Get an online TV stream link.",
        "`sqr` : Convert text to a QR code.",
        "`readqr` : Read a QR code.",
        "`cleanall` [txt] : Delete matching messages in a group.",
        "`setusername` [txt] : Set your username.",
        "`kick` [usernames|IDs] : Remove users from a group.",
        "`cleanb` [link1] [link2] : Delete messages between two links.",
        "`/rem` [num] : Delete recent messages up to the specified count.",
        "`/sgoogle` [query] : Search Google for a quick answer.",
        "`/wiki` [query] : Search Wikipedia.",
        "`/save` : Save a chat or log to a file.",
        "`/reload` : Reload the self client.",
        "`ReadAll` : Mark messages as read in selected chat types.",
        "`Del` : Delete selected media types in a chat.",
        "`typing` [on|off] : Toggle typing status in private chats.",
        "`Pvinfo` : Show private-chat information.",
    ])
    await event.edit(panel)
