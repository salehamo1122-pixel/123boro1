"""Central runtime switch for the self client.
Keeps the control bot/Mini App alive while allowing all user-client handlers to be paused.
"""
from pathlib import Path
import functools
import logging

logger = logging.getLogger("kirmigam.control")
SETTINGS = Path("settings")
MASTER_FILE = SETTINGS / "master_enabled.txt"
SETTINGS.mkdir(exist_ok=True)
if not MASTER_FILE.exists():
    MASTER_FILE.write_text("True", encoding="utf-8")

EXEMPT_HANDLERS = {"show_panel", "health_command", "handle_start_command"}


def _load_from_disk():
    try:
        return MASTER_FILE.read_text(encoding="utf-8").strip().lower() == "true"
    except OSError:
        return True


# The flag is checked on every incoming message and every few seconds by the
# background loops, so it is cached in memory instead of re-reading the file.
_enabled = _load_from_disk()


def is_master_enabled():
    return _enabled


def set_master_enabled(enabled: bool):
    global _enabled
    _enabled = bool(enabled)
    try:
        MASTER_FILE.write_text("True" if _enabled else "False", encoding="utf-8")
    except OSError:
        logger.exception("Could not persist master switch")
    return _enabled


def _flag(name):
    try:
        return (SETTINGS / name).read_text(encoding="utf-8").strip().lower() == "true"
    except OSError:
        return False


async def after_master_change(client, enabled: bool):
    """When the self client is switched OFF, stop leaving a frozen clock in the profile."""
    if enabled:
        return
    try:
        from telethon.tl.functions.account import UpdateProfileRequest
        if _flag("time.txt"):
            await client(UpdateProfileRequest(last_name=""))
        if _flag("bioinfo.txt"):
            await client(UpdateProfileRequest(about=""))
    except Exception:
        logger.exception("Could not clean dynamic profile fields after switching OFF")


def install_master_gate(client, exempt_names=None):
    """Wrap every already-registered self-client handler with the master switch.

    The helper bot is a different client, so it remains usable when the self client is off.
    """
    exempt = set(EXEMPT_HANDLERS if exempt_names is None else exempt_names)
    entries = list(client.list_event_handlers())
    installed = 0
    for callback, event_builder in entries:
        if getattr(callback, "_master_gate_wrapper", False):
            continue
        name = getattr(callback, "__name__", "")
        if name in exempt:
            continue

        # updated=() : do NOT copy __dict__. Handlers registered with @events.register carry
        # Telethon's handler attribute, and copying it makes add_event_handler() re-attach
        # every builder again (duplicate executions).
        @functools.wraps(callback, updated=())
        async def gated(event, _callback=callback):
            if not is_master_enabled():
                return
            return await _callback(event)

        gated._master_gate_wrapper = True
        gated._master_gate_original = callback
        try:
            client.remove_event_handler(callback, event_builder)
            client.add_event_handler(gated, event_builder)
            installed += 1
        except Exception:
            logger.exception("Could not gate handler %s", name)
    logger.info("Master gate installed for %s self-client handlers", installed)
    return installed
