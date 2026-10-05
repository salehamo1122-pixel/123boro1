"""Salself Mini App: live dashboard + complete feature control."""
from pathlib import Path
import asyncio, datetime, json, os, sys, time
from zoneinfo import ZoneInfo

S = Path("settings")
S.mkdir(exist_ok=True)
TEHRAN = ZoneInfo("Asia/Tehran")


def _main():
    return sys.modules.get("__main__")


def _rf(name):
    try:
        return (S / name).read_text(encoding="utf-8").strip().lower() == "true"
    except Exception:
        return False


def _wf(name, v):
    (S / name).write_text("True" if v else "False", encoding="utf-8")


def _tg(make_coro):
    m = _main(); c = getattr(m, "client", None)
    if not c or not c.loop or not c.loop.is_running():
        return False
    async def _go():
        return await make_coro(c)
    try:
        asyncio.run_coroutine_threadsafe(_go(), c.loop).result(timeout=20)
        return True
    except Exception:
        return False


def _af():
    import add_features
    return add_features


def _json_flag(path_attr):
    def get():
        a = _af(); return bool(a._load_json(getattr(a, path_attr), {}).get("enabled"))
    def set_(v):
        a = _af(); p = getattr(a, path_attr)
        d = a._load_json(p, {"enabled": False, "text": a.DEFAULT_AWAY})
        d["enabled"] = bool(v); a._save_json(p, d); a.away_replied.clear()
    return get, set_


def _file_flag(file_attr):
    def get():
        a = _af(); return a._read_flag(getattr(a, file_attr), False)
    def set_(v):
        a = _af(); a._write_flag(getattr(a, file_attr), bool(v)); a.away_replied.clear()
    return get, set_


def _timename(v):
    _wf("time.txt", v)
    if not v:
        from telethon.tl.functions.account import UpdateProfileRequest
        _tg(lambda c: c(UpdateProfileRequest(last_name="")))


def _bio(v):
    _wf("bioinfo.txt", v)
    if not v:
        from telethon.tl.functions.account import UpdateProfileRequest
        _tg(lambda c: c(UpdateProfileRequest(about="")))


def _main_flag(name):
    def get(): return bool(getattr(_main(), name, False))
    def set_(v): setattr(_main(), name, bool(v))
    return get, set_


def _antidelete_set(v):
    m = _main(); m.anti_delete_global_enabled = bool(v); m.set_global_anti_delete(bool(v))

_ar_get, _ar_set = _json_flag("AUTO_REPLY_FILE")
_aw_get, _aw_set = _json_flag("AWAY_FILE")
_sec_get, _sec_set = _file_flag("SECRETARY_FILE")
_rd_get, _rd_set = _file_flag("AUTO_READ_FILE")
_gh_get, _gh_set = _main_flag("ghost_mode_enabled")
_sp_get, _sp_set = _main_flag("spoiler_mode_enabled")

FEATURES = [
    ("timename", "profile", "ساعت در اسم", "نمایش ساعت ایران کنار نام", "🕒", lambda: _rf("time.txt"), _timename),
    ("timepic", "profile", "ساعت روی عکس", "نمایش ساعت روی عکس پروفایل", "◷", lambda: _rf("timepic.txt"), lambda v: _wf("timepic.txt", v)),
    ("bio", "profile", "بیوی پویا", "ساعت و تاریخ ایران در بیو", "B", lambda: _rf("bioinfo.txt"), _bio),
    ("heart", "profile", "قلب رندوم", "قلب تصادفی کنار ساعت", "♥", lambda: _rf("heart.txt"), lambda v: _wf("heart.txt", v)),
    ("rname", "profile", "نام رندوم", "تغییر خودکار نام", "N", lambda: _rf("rnamest.txt"), lambda v: _wf("rnamest.txt", v)),
    ("antidelete", "security", "ضد حذف", "بازیابی پیام‌های خصوصی حذف‌شده", "A", lambda: bool(getattr(_main(), "anti_delete_global_enabled", False)), _antidelete_set),
    ("ghost", "security", "حالت روح", "خواندن بدون دیده‌شدن", "G", _gh_get, _gh_set),
    ("spoiler", "security", "اسپویلر", "حالت اسپویلر پیام‌ها", "S", _sp_get, _sp_set),
    ("autoread", "automation", "خواندن خودکار", "خواندن خودکار پیام‌ها", "R", _rd_get, _rd_set),
    ("autoreply", "automation", "پاسخ خودکار", "پاسخ خودکار پیام‌های خصوصی", "↩", _ar_get, _ar_set),
    ("away", "automation", "حالت آفلاین", "پیام آفلاین خودکار", "Z", _aw_get, _aw_set),
    ("secretary", "automation", "منشی هوشمند", "مدیریت خودکار پیام‌ها", "M", _sec_get, _sec_set),
    ("ai", "automation", "دستیار هوشمند", "دستیار AI در Saved Messages", "AI", lambda: _af().ai_enabled(), lambda v: _af().set_ai_enabled(v)),
]
CATS = [("profile", "پروفایل"), ("security", "امنیت و حریم خصوصی"), ("automation", "اتوماسیون و هوش مصنوعی")]
BY_ID = {x[0]: x for x in FEATURES}


def _safe(fn):
    try: return bool(fn())
    except Exception: return False


def state():
    from control_center import is_master_enabled
    return {
        "master": is_master_enabled(),
        "cats": [{"id": a, "fa": b} for a, b in CATS],
        "features": [{"id": f[0], "cat": f[1], "title": f[2], "desc": f[3], "icon": f[4], "on": _safe(f[5])} for f in FEATURES],
    }


def toggle(fid, enabled):
    f = BY_ID.get(fid)
    if not f: return None
    f[6](bool(enabled)); return _safe(f[5])


def set_master(enabled):
    from control_center import set_master_enabled, after_master_change
    res = set_master_enabled(bool(enabled))
    _tg(lambda c: after_master_change(c, res))
    return res


def _read_int(path):
    try:
        v = Path(path).read_text().strip()
        return None if v in ("max", "") else int(v)
    except Exception:
        return None


def _container_memory():
    """Render/Docker report the HOST's RAM through psutil; prefer the cgroup limit."""
    limit = _read_int("/sys/fs/cgroup/memory.max") or _read_int("/sys/fs/cgroup/memory/memory.limit_in_bytes")
    used = _read_int("/sys/fs/cgroup/memory.current") or _read_int("/sys/fs/cgroup/memory/memory.usage_in_bytes")
    if limit and limit < (1 << 50) and used is not None:
        return used, limit
    import psutil
    vm = psutil.virtual_memory()
    return vm.used, vm.total


def _real_ping_ms():
    """Measure a real round-trip to Telegram through the authenticated helper bot."""
    try:
        import requests
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token:
            return None
        t0 = time.perf_counter()
        r = requests.get(
            f"https://api.telegram.org/bot{token}/getMe",
            timeout=5,
        )
        r.raise_for_status()
        return round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        return None


def _stats():
    import psutil
    now = datetime.datetime.now(TEHRAN)
    try:
        import jdatetime
        j = jdatetime.datetime.fromgregorian(datetime=now)
        date = f"{j.year:04d}/{j.month:02d}/{j.day:02d}"
    except Exception:
        try:
            from persiantools.jdatetime import JalaliDate
            j = JalaliDate.to_jalali(now.year, now.month, now.day)
            date = f"{j.year:04d}/{j.month:02d}/{j.day:02d}"
        except Exception:
            date = f"{now.year:04d}/{now.month:02d}/{now.day:02d}"
    started = getattr(_main(), "PROCESS_STARTED_AT", time.time())
    uptime = max(0, int(time.time() - started))
    d, rem = divmod(uptime, 86400); h, rem = divmod(rem, 3600); mi, s = divmod(rem, 60)
    used, total = _container_memory()
    proc = psutil.Process()
    cpu = proc.cpu_percent(interval=None) / (psutil.cpu_count() or 1)
    m = _main()
    active_features = sum(1 for f in FEATURES if _safe(f[5]))
    me_id = getattr(m, "admin_user_id", None)
    if not me_id:
        try:
            me_id = int(os.getenv("ADMIN_USER_ID", "0")) or None
        except Exception:
            me_id = None
    return {
        "name": "Salself", "online": True, "tehran_time": now.strftime("%H:%M:%S"),
        "date": date, "uptime": f"{d}d {h:02d}h {mi:02d}m {s:02d}s",
        "cpu": round(min(cpu, 100.0), 1), "memory": round(used * 100 / total, 1) if total else 0,
        "ram_used_gb": round(used / (1024 ** 3), 2), "ram_total_gb": round(total / (1024 ** 3), 2),
        "account_id": me_id, "active_features": active_features,
        "telegram_ping_ms": _real_ping_ms(),
    }


def stats(): return _stats()

PAGE = r'''<!doctype html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Salself</title>
<style>
:root{--bg:#0d1117;--card:#141a22;--card2:#19212b;--tx:#f4f7fb;--mut:#8793a4;--line:#26313e;--blue:#2f8cff;--green:#27d17f;--red:#ff5d6c;--gold:#f1c75b;}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}body{margin:0;background:radial-gradient(circle at 50% 8%,#182331 0,#0d1117 48%);color:var(--tx);font-family:system-ui,-apple-system,"Segoe UI",Tahoma,sans-serif;padding-bottom:90px}.wrap{max-width:760px;margin:auto;padding:14px}
.hero{text-align:center;padding:18px 10px 10px}.logo{width:112px;height:112px;margin:auto;border-radius:30px;background:linear-gradient(145deg,#273240,#11171f);display:grid;place-items:center;box-shadow:0 18px 45px #0008;border:1px solid #ffffff12}.plane{font-size:66px;filter:grayscale(1) brightness(2);transform:rotate(-8deg)}h1{margin:12px 0 3px;font-size:42px;letter-spacing:.4px;color:#3294ff}.sub{color:#a7b1bf;font-size:16px}.status{display:flex;align-items:center;justify-content:center;gap:8px;margin:13px 0;color:#dbe5ef}.dot{width:11px;height:11px;border-radius:50%;background:var(--green);box-shadow:0 0 14px #27d17f99}.dot.off{background:var(--red);box-shadow:0 0 14px #ff5d6c77}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:20px;overflow:hidden;margin:12px 0 16px}.metric{background:var(--card);padding:17px 8px;text-align:center;min-width:0}.metric .v{font-size:21px;font-weight:750;white-space:nowrap}.metric .k{color:var(--mut);font-size:12px;margin-top:5px}.card{background:#111821dd;border:1px solid var(--line);border-radius:20px;padding:15px;margin:12px 0;backdrop-filter:blur(8px)}.section-title{font-size:18px;font-weight:800;margin:2px 2px 13px}.master{display:grid;grid-template-columns:1fr 1fr;gap:10px}.btn{border:0;border-radius:15px;padding:14px;font:inherit;font-weight:800;color:#fff;background:var(--card2);border:1px solid var(--line)}.btn.on{background:#163d2b;border-color:#216844}.btn.off{background:#401b21;border-color:#6d2832}.btn.blue{background:#14375f;border-color:#245c94}.btn:active{transform:scale(.985)}
.search{display:flex;gap:9px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:15px;padding:0 13px;margin-bottom:10px}.search input{flex:1;border:0;outline:0;background:transparent;color:var(--tx);font:inherit;padding:13px 0}.tabs{display:flex;gap:6px;margin-bottom:11px}.tabs button{flex:1;background:var(--card);border:1px solid var(--line);border-radius:13px;padding:10px;color:var(--mut);font:inherit;font-weight:700}.tabs button.on{background:#17375c;color:#fff;border-color:#2867a5}.cat{background:var(--card);border:1px solid var(--line);border-radius:17px;overflow:hidden;margin:10px 0}.cathead{padding:14px 15px;background:#171f29;display:flex;align-items:center;gap:8px;font-weight:800}.cathead span:first-child{flex:1}.count{color:var(--mut);font-size:12px}.row{display:flex;align-items:center;gap:11px;padding:12px 13px;border-top:1px solid var(--line)}.icon{width:40px;height:40px;border-radius:12px;background:#1b2734;display:grid;place-items:center;font-weight:800;color:#c9d5e3}.name{flex:1;min-width:0}.name b{display:block;font-size:14px}.name small{display:block;color:var(--mut);font-size:11.5px;margin-top:3px}.switch{width:48px;height:28px;border:0;border-radius:99px;background:#44505e;position:relative;flex:none}.switch:after{content:"";position:absolute;top:3px;right:23px;width:22px;height:22px;border-radius:50%;background:#fff;transition:.18s}.switch.on{background:var(--green)}.switch.on:after{right:3px}.note{color:var(--mut);font-size:12px;line-height:1.7}.refresh{width:100%;margin-top:10px}.toast{position:fixed;left:14px;right:14px;bottom:76px;background:#18212c;border:1px solid var(--line);padding:12px;border-radius:14px;text-align:center;opacity:0;transform:translateY(8px);transition:.2s;pointer-events:none}.toast.show{opacity:1;transform:none}footer{text-align:center;color:#566272;font-size:11px;margin:20px}
@media(max-width:560px){.grid{grid-template-columns:repeat(2,1fr)}h1{font-size:38px}.master{grid-template-columns:1fr 1fr}}
</style></head><body><div class="wrap">
<div id="err" class="card" style="display:none;border-color:#6d2832;direction:ltr;text-align:left;font-size:12px;word-break:break-all"></div>
<div id="noauth" class="card" style="display:none;border-color:#6d2832;text-align:center;line-height:1.9">این صفحه فقط از داخل تلگرام کار می‌کند.<br>ربات را باز کن و دکمه «کنترل پنل» کنار کادر پیام را بزن.</div>
<section class="hero"><div class="logo"><div class="plane">➤</div></div><h1>Salself</h1><div class="sub">مدیریت اکانت تلگرام</div><div class="status"><span id="dot" class="dot"></span><b id="status">آنلاین</b></div></section>
<section class="grid"><div class="metric"><div class="v" id="clock">--:--:--</div><div class="k">ساعت ایران</div></div><div class="metric"><div class="v" id="date">----</div><div class="k">تاریخ ایران</div></div><div class="metric"><div class="v" id="ping">-- ms</div><div class="k">پینگ تلگرام</div></div><div class="metric"><div class="v" id="active">--</div><div class="k">قابلیت فعال</div></div></section>
<section class="card"><div class="section-title">کنترل اصلی</div><div class="master"><button id="masterOn" class="btn on">روشن کردن سلف</button><button id="masterOff" class="btn off">خاموش کردن سلف</button><button id="allOn" class="btn blue">همه قابلیت‌ها روشن</button><button id="allOff" class="btn">همه قابلیت‌ها خاموش</button></div><div class="note" style="margin-top:10px">با خاموش شدن سلف، پنل و Mini App همچنان فعال می‌مانند تا بتوانی دوباره آن را روشن کنی.</div></section>
<section class="card"><div class="section-title">قابلیت‌ها</div><div class="search">⌕<input id="q" placeholder="جستجوی قابلیت..."></div><div class="tabs"><button data-tab="all" class="on">همه</button><button data-tab="on">فعال</button><button data-tab="off">خاموش</button></div><div id="features"></div></section>
<section class="card"><div class="section-title">وضعیت سیستم</div><div class="note">شناسه اکانت: <b id="account">--</b><br>آپ‌تایم: <b id="uptime">--</b><br>CPU: <b id="cpu">--%</b> | RAM: <b id="mem">--%</b><br>حافظه: <b id="ramdetail">--</b><br>آخرین بروزرسانی: <b id="updated">--</b></div><button class="btn refresh" id="refresh">بروزرسانی فوری</button></section>
<footer>Salself Control Center</footer></div><div id="toast" class="toast"></div>
<script>
window.onerror=function(msg,src,line){var e=document.getElementById('err');if(e){e.style.display='block';e.textContent='JS error: '+msg+' (line '+line+')'}};
function getTg(){
 var w=window.Telegram&&window.Telegram.WebApp;if(w)return w;
 var hp=new URLSearchParams((location.hash||'').slice(1));
 return {initData:hp.get('tgWebAppData')||'',ready:function(){},expand:function(){},showConfirm:function(t,cb){cb(confirm(t))}};
}
function boot(){

const tg=getTg();try{tg.ready();tg.expand()}catch(e){}const H={'X-Telegram-Init-Data':tg.initData};let data=null,tab='all',q='',busy=0;if(!tg.initData){document.getElementById('noauth').style.display='block'}
const ask=t=>new Promise(r=>{try{tg.showConfirm(t,r)}catch(e){r(confirm(t))}}),$=x=>document.querySelector(x), toast=x=>{let t=$('#toast');t.textContent=x;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),1700)};
async function api(url,opt={}){let r=await fetch(url,{cache:'no-store',...opt,headers:{...H,...(opt.headers||{})}});let d=await r.json();if(!r.ok||d.ok===false)throw Error(d.error||'خطا');return d}
function render(){if(!data)return;$('#dot').classList.toggle('off',!data.master);$('#status').textContent=data.master?'سلف آنلاین':'سلف خاموش';let fs=data.features.filter(f=>(tab==='all'||(tab==='on')===f.on)&&(!q||((f.title+' '+f.desc).toLowerCase().includes(q))));let cats={};fs.forEach(f=>(cats[f.cat]??=[]).push(f));let names={profile:'پروفایل',security:'امنیت و حریم خصوصی',automation:'اتوماسیون و هوش مصنوعی'};let h='';Object.entries(cats).forEach(([c,arr])=>{let all=data.features.filter(f=>f.cat===c);h+=`<div class="cat"><div class="cathead"><span>${names[c]}</span><span class="count">${all.filter(f=>f.on).length}/${all.length}</span></div>${arr.map(f=>`<div class="row"><div class="icon">${f.icon}</div><div class="name"><b>${f.title}</b><small>${f.desc}</small></div><button class="switch ${f.on?'on':''}" data-id="${f.id}"></button></div>`).join('')}</div>`});$('#features').innerHTML=h||'<div class="note">موردی پیدا نشد.</div>';document.querySelectorAll('.switch').forEach(b=>b.onclick=()=>flip(b.dataset.id))}
async function load(){if(busy||!tg.initData)return;try{data=await api('/api/miniapp/state');render()}catch(e){toast(e.message)}}
async function flip(id){let f=data.features.find(x=>x.id===id),old=f.on;f.on=!old;render();busy++;try{let d=await api('/api/miniapp/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,enabled:f.on})});f.on=d.enabled;tg.HapticFeedback?.impactOccurred('light')}catch(e){f.on=old;toast(e.message)}busy--;render()}
async function master(v){if(!v&&!await ask('سلف خاموش شود؟ تا روشن کردن دوباره هیچ دستوری اجرا نمی‌شود.'))return;try{let d=await api('/api/miniapp/master',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:v})});data.master=d.enabled;render();toast(v?'سلف روشن شد':'سلف خاموش شد')}catch(e){toast(e.message)}}
async function all(v){if(!await ask(v?'همه قابلیت‌ها (از جمله پاسخ خودکار، آفلاین، منشی و AI) روشن شوند؟':'همه قابلیت‌ها خاموش شوند؟'))return;busy++;try{let d=await api('/api/miniapp/all',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:v})});data=d.state;render();toast(v?'همه قابلیت‌ها روشن شدند':'همه قابلیت‌ها خاموش شدند')}catch(e){toast(e.message)}busy--}
async function stats(){if(!tg.initData)return;try{const t0=performance.now();let d=await api('/api/miniapp/stats');const roundTrip=Math.max(0,Math.round(performance.now()-t0));$('#date').textContent=d.date;$('#clock').textContent=d.tehran_time;$('#ping').textContent=(d.telegram_ping_ms==null?'--':d.telegram_ping_ms)+' ms';$('#active').textContent=d.active_features;$('#account').textContent=d.account_id??'--';$('#cpu').textContent=d.cpu+'%';$('#mem').textContent=d.memory+'%';$('#uptime').textContent=d.uptime;$('#ramdetail').textContent=d.ram_used_gb+' / '+d.ram_total_gb+' GB';$('#updated').textContent=d.tehran_time+' | رفت‌وبرگشت '+roundTrip+' ms'}catch(e){}}
$('#masterOn').onclick=()=>master(true);$('#masterOff').onclick=()=>master(false);$('#allOn').onclick=()=>all(true);$('#allOff').onclick=()=>all(false);$('#refresh').onclick=()=>{load();stats()};$('#q').oninput=e=>{q=e.target.value.trim().toLowerCase();render()};document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{tab=b.dataset.tab;document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('on',x===b));render()});
const fmt=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Tehran',hour12:false,hour:'2-digit',minute:'2-digit',second:'2-digit'});function tick(){if(!data||!data._serverTime){$('#clock').textContent=fmt.format(new Date())}}tick();setInterval(tick,1000);load();stats();setInterval(stats,5000);setInterval(load,10000);

}
(function(){var started=false;function go(){if(started)return;started=true;boot()}
 var s=document.createElement('script');s.src='https://telegram.org/js/telegram-web-app.js?63';s.onload=go;s.onerror=go;document.head.appendChild(s);setTimeout(go,2500)})();
</script></body></html>'''
