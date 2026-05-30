import discord
from discord import ui
from discord.ext import commands
from discord import app_commands
import json
import os
import sys
import asyncio
import uuid
import logging
import functools

logging.basicConfig(
    filename="bot/bot.log",
    level=logging.INFO
)
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot/bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.join(os.getcwd(), "bot"))

try:
    import paypayu
    PAYPAY_AVAILABLE = True
    logger.info("paypayu.py ロード完了")
except ImportError as e:
    logger.warning(f"paypayu.py が見つかりません: {e}")
    PAYPAY_AVAILABLE = False
except Exception as e:
    logger.warning(f"paypayu.py ロード失敗: {e}")
    PAYPAY_AVAILABLE = False

BOT_TOKEN = os.environ.get("BOT_TOKEN", "MTQ4NDg3NTI2MDM1NTQxMjE1OQ.Gg8yRL.rjJF-NGh4u60ujdymm37C5SMi_I_Pz25bvs0m0")
ADMIN_IDS_RAW = os.environ.get("ADMIN_IDS", "1474696025947242569")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit()] if ADMIN_IDS_RAW else []
ALLOWED_CHANNEL_IDS = []

PAYPAY_DATA_FILE = "bot/paypay_data.json"
ORDER_LOG_FILE = "bot/order_log.json"
SETTINGS_FILE = "bot/settings.json"
PRICE_FILE = "bot/price_overrides.json"

CLONE_PRICE_DEFAULT       = 100
FULL_EDIT_PRICE_DEFAULT   = 500
RECOVERY_PRICE_DEFAULT    = 300

CHARA_UNLOCK_PRICE_DEFAULT  = 50
CHARA_LVMAX_PRICE_DEFAULT   = 50
CHARA_FORM_PRICE_DEFAULT    = 50



ITEM_CONFIG = {
    "catfood_50000":      {"label": "猫缶 50,000個",              "price": 50},
    "xp_max":             {"label": "XP 99,999,999",             "price": 50},
    "np_max":             {"label": "NP 9,999",                  "price": 50},
    "nyan_ticket_999":    {"label": "にゃんチケット 999枚",       "price": 50},
    "rare_tickets_999":   {"label": "レアチケット 999枚",         "price": 50},
    "platinum_29":        {"label": "プラチナチケット 29枚",      "price": 50},
    "legend_29":          {"label": "レジェンドチケット 29枚",    "price": 50},
    "platinum_shard_90":  {"label": "プラチナのかけら 90個",      "price": 50},
    "leadership_999":     {"label": "リーダーシップ 999個",       "price": 50},
    "battle_items_999":   {"label": "バトルアイテム全種 999個",   "price": 50},
    "matatabi_998":       {"label": "マタタビ全種 998個",         "price": 100},
    "cats_eye_999":       {"label": "キャッツアイ全種 999個",     "price": 100},
    "nekovitan_999":      {"label": "ネコビタン全種 999個",       "price": 50},
    "castle_parts_999":   {"label": "城素材全種 999個",           "price": 50},
    "event_ticket_999":   {"label": "イベントチケット 999枚",     "price": 100},
    "honnou_99":          {"label": "本能玉全種 99個",            "price": 250},
    "dungeon_medal_99":   {"label": "地底迷宮メダル全種 99個",    "price": 100},
    "main_clear":         {"label": "メインステージ全クリア+お宝金",   "price": 100},
    "zombie_clear":       {"label": "メインゾンビステージ全クリア",    "price": 300},
    "old_legend_clear":   {"label": "旧レジェンド全クリア",           "price": 300},
    "true_legend_clear":  {"label": "真レジェンド全クリア",           "price": 300},
    "zero_legend_clear":  {"label": "零レジェンド全クリア",           "price": 300},
    "makai_clear":        {"label": "魔界編全クリア",                 "price": 300},
    "event_clear":        {"label": "イベントステージ全クリア",       "price": 500},
    "all_char_unlock":    {"label": "全キャラ開放",               "price": 100},
    "error_char_delete":  {"label": "エラーキャラ削除",           "price": 100},
    "all_char_lv_max":    {"label": "全キャラLvMAX",              "price": 100},
    "all_char_max_form":  {"label": "全キャラ最大形態",           "price": 100},
    "all_honnou_max":     {"label": "全キャラ本能全開放",         "price": 250},
    "telop_delete":       {"label": "開放テロップ削除",           "price": 0},
    "slot_max":           {"label": "編成スロット数最大拡張",     "price": 50},
    "medal_all":          {"label": "にゃんこメダル全開放",       "price": 100},
    "enemy_book_all":     {"label": "敵キャラ図鑑全開放",         "price": 100},
    "user_rank_all":      {"label": "ユーザーランク報酬全受取",   "price": 50},
    "playtime_max":       {"label": "プレイ時間カンスト",         "price": 200},
    "gold_pass":          {"label": "ゴールド会員化",             "price": 200},
    "facility_max":       {"label": "施設LvMAX",                 "price": 100},
    "gamatoto_max":       {"label": "ガマトトLvMAX",              "price": 200},
    "gamatoto_legend":    {"label": "ガマトト助手全員レジェンド", "price": 200},
    "ad_free":            {"label": "広告非表示（β）",            "price": 50},
    "ototo_max":          {"label": "オトート全城強化LvMAX",      "price": 200},
    "shrine_max":         {"label": "にゃんこ神社LvMAX",         "price": 100},
}

def load_paypay_data() -> dict:
    if os.path.exists(PAYPAY_DATA_FILE):
        try:
            with open(PAYPAY_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_paypay_data(data: dict):
    with open(PAYPAY_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_order_log() -> list:
    import datetime
    if os.path.exists(ORDER_LOG_FILE):
        try:
            with open(ORDER_LOG_FILE, "r", encoding="utf-8") as f:
                log = json.load(f)
        except json.JSONDecodeError:
            return []
    else:
        return []
    cutoff = datetime.datetime.now() - datetime.timedelta(days=1)
    log = [e for e in log if datetime.datetime.fromisoformat(e["timestamp"]) > cutoff]
    return log

def log_order(user_id: int, username: str, items: list, amount: int, status: str):
    import datetime
    log = load_order_log()
    log.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "user_id": str(user_id),
        "username": username,
        "items": items,
        "amount": amount,
        "status": status,
    })
    with open(ORDER_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=4, ensure_ascii=False)
    logger.info(f"[ORDER] {username}({user_id}) {items} {amount}円 [{status}]")

def _load_all_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def _save_all_settings(data: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_settings(guild_id: int) -> dict:
    return _load_all_settings().get(str(guild_id), {})

def save_settings(guild_id: int, data: dict):
    all_s = _load_all_settings()
    all_s[str(guild_id)] = data
    _save_all_settings(all_s)

def _load_all_price_overrides() -> dict:
    if os.path.exists(PRICE_FILE):
        try:
            with open(PRICE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def _save_all_price_overrides(data: dict):
    with open(PRICE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_price_overrides(guild_id: int) -> dict:
    return _load_all_price_overrides().get(str(guild_id), {})

def save_price_overrides(guild_id: int, data: dict):
    all_p = _load_all_price_overrides()
    all_p[str(guild_id)] = data
    _save_all_price_overrides(all_p)

def get_price(key: str, guild_id: int) -> int:
    ov = load_price_overrides(guild_id)
    default = ITEM_CONFIG[key]["price"] if key in ITEM_CONFIG else 50
    return ov.get(key, default)

def get_special_price(key: str, default: int, guild_id: int) -> int:
    ov = load_price_overrides(guild_id)
    return ov.get(key, default)

def get_jisseki_channel_id(guild_id: int):
    settings = load_settings(guild_id)
    val = settings.get("jisseki_channel_id")
    return int(val) if val else None

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def load_allowed_users() -> list[str]:
    data = _load_all_settings()
    return data.get("_global", {}).get("allowed_users", [])

def save_allowed_users(users: list[str]):
    data = _load_all_settings()
    if "_global" not in data:
        data["_global"] = {}
    data["_global"]["allowed_users"] = users
    _save_all_settings(data)

def is_allowed_user(user_id: int) -> bool:
    return str(user_id) in load_allowed_users()

def can_use_command(user_id: int) -> bool:
    return is_admin(user_id) or is_allowed_user(user_id)

def load_free_users() -> list[str]:
    data = _load_all_settings()
    return data.get("_global", {}).get("free_users", [])

def save_free_users(users: list[str]):
    data = _load_all_settings()
    if "_global" not in data:
        data["_global"] = {}
    data["_global"]["free_users"] = users
    _save_all_settings(data)

def is_free_user(user_id: int) -> bool:
    return is_admin(user_id) or str(user_id) in load_free_users()

def load_allowed_guilds() -> list[str]:
    data = _load_all_settings()
    return data.get("_global", {}).get("allowed_guilds", [])

def save_allowed_guilds(guilds: list[str]):
    data = _load_all_settings()
    if "_global" not in data:
        data["_global"] = {}
    data["_global"]["allowed_guilds"] = guilds
    _save_all_settings(data)

def is_allowed_guild(guild_id: int) -> bool:
    return str(guild_id) in load_allowed_guilds()

def load_home_guild() -> str | None:
    data = _load_all_settings()
    return data.get("_global", {}).get("home_guild_id", None)

def save_home_guild(guild_id: str | None):
    data = _load_all_settings()
    if "_global" not in data:
        data["_global"] = {}
    if guild_id is None:
        data["_global"].pop("home_guild_id", None)
    else:
        data["_global"]["home_guild_id"] = guild_id
    _save_all_settings(data)

def is_home_guild(guild_id: int) -> bool:
    hg = load_home_guild()
    return hg is not None and str(guild_id) == hg

_valid_cat_max_cache: int | None = None

def _get_valid_cat_max() -> int:
    global _valid_cat_max_cache
    if _valid_cat_max_cache is not None:
        return _valid_cat_max_cache
    HARDCODED_MAX = 674
    try:
        import urllib.request, re
        url = "https://battlecats-db.com/unit/"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode("utf-8", errors="ignore")
        ids = [int(m) for m in re.findall(r'/unit/(\d+)\.html', html)]
        if ids:
            max_id = max(ids) + 1
            if 500 <= max_id <= 2000:
                _valid_cat_max_cache = max_id
                logger.info(f"battlecats-db 有効キャラID最大値: {max_id}")
                return max_id
    except Exception as e:
        logger.warning(f"battlecats-db取得失敗、fallback={HARDCODED_MAX}: {e}")
    _valid_cat_max_cache = HARDCODED_MAX
    return HARDCODED_MAX


def _sv(save_file, attr: str, value: int):
    try:
        obj = getattr(save_file, attr)
        try:
            obj.value = value
            return
        except (AttributeError, TypeError):
            pass
        try:
            setattr(save_file, attr, value)
            return
        except (TypeError, AttributeError):
            pass
        try:
            obj.set(value)
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"_sv({attr}, {value}) 失敗: {e}")


def _sv_list(save_file, attr: str, value: int):
    try:
        lst = getattr(save_file, attr)
        for i in range(len(lst)):
            try:
                lst[i].value = value
            except (AttributeError, TypeError):
                try:
                    lst[i] = value
                except (TypeError, AttributeError):
                    try:
                        lst[i].set(value)
                    except Exception:
                        pass
    except Exception as e:
        logger.warning(f"_sv_list({attr}, {value}) 失敗: {e}")


def _iter_cats(save_file):
    try:
        cats_obj = save_file.cats
        for attr in ("cats", "data", "_cats", "items"):
            try:
                lst = getattr(cats_obj, attr, None)
                if lst is not None and hasattr(lst, "__iter__"):
                    return list(lst)
            except Exception:
                pass
        try:
            return list(cats_obj)
        except Exception:
            pass
    except Exception:
        pass
    return []


def _auto_run(func, save_file, inputs: list):
    import sys, io
    fallback = (
        ["1", "10", "y", "999", "4", "0", "1", "10", "y", "999", "4", "0"] * 20
    )
    responses = list(inputs) + fallback
    fake_stdin = io.StringIO("\n".join(str(r) for r in responses) + "\n")
    old_stdin, old_stdout, old_stderr = sys.stdin, sys.stdout, sys.stderr
    sys.stdin  = fake_stdin
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        func(save_file)
    except (EOFError, StopIteration, SystemExit):
        pass
    except Exception as e:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        logger.warning(f"[_auto_run] {getattr(func, '__name__', str(func))} エラー: {e}")
        return
    finally:
        sys.stdin  = old_stdin
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def _clear_chapters(sf, chapters, name, logger):
    try:
        ctype = type(chapters).__name__

        if hasattr(chapters, "clear_stage"):
            total_maps = len(chapters.chapters)
            cleared = 0
            for mid in range(total_maps):
                try: total_stars = chapters.get_total_stars(mid)
                except: total_stars = 1
                for star in range(total_stars):
                    try: total_stages = chapters.get_total_stages(mid, star)
                    except: total_stages = 48
                    try: chapters.set_total_stages(mid, total_stages)
                    except: pass
                    for stage in range(total_stages):
                        try: chapters.clear_stage(mid, star, stage, 1, True)
                        except: pass
                cleared += 1
            logger.info(f"{name}: {cleared}ch 完了")
            return cleared

        logger.info(f"{name} ctype={ctype}")
        if ctype == "ExChapters" or hasattr(chapters, "stages") and not hasattr(chapters, "chapters"):
            cleared = 0
            try:
                ch_list = chapters.chapters
            except:
                ch_list = []
            for _ci, ch in enumerate(ch_list):
                try:
                    stages = ch.stages
                    for st in stages:
                        _set = False
                        for _iattr in ("_clear_amount", "__clear_amount", "_ClearAmount", "_clear_count"):
                            _v = st.__dict__.get(_iattr) or getattr(st, _iattr, None)
                            if _v is not None and hasattr(_v, "value"):
                                try: _v.value = 1; _set = True; break
                                except: pass
                        if not _set:
                            try: st.clear_amount = 1
                            except: pass
                    cleared += 1
                except: pass
            logger.info(f"{name}: {cleared}ch 完了")
            return cleared

        if ctype == "Outbreaks" or hasattr(chapters, "clear_outbreak"):
            cleared = 0
            try:
                try: chapters.read_chapters()
                except: pass
                ch_list = chapters.chapters
                for _oi, ob in enumerate(ch_list):
                    _tid = None
                    for _fn_args in [(), (sf,)]:
                        try:
                            _t = ob.get_true_id(*_fn_args)
                            if _t is not None: _tid = int(_t); break
                        except: pass
                    if _tid is None:
                        try:
                            _raw = ob.id
                            _tid = int(_raw.value) if hasattr(_raw,"value") else int(_raw)
                        except: pass
                    if _tid is None: _tid = _oi
                    for _try_tid in [_tid, _oi, _oi + 1]:
                        try:
                            chapters.clear_outbreak(_try_tid)
                            cleared += 1; break
                        except Exception as _e:
                            if _oi < 2: logger.warning(f"{name} clear_outbreak({_try_tid}) error: {_e}")
                    else:
                        cleared += 1
            except Exception as _e:
                logger.warning(f"{name} outbreaks error: {_e}")
            logger.info(f"{name}: {cleared}ch 完了")
            return cleared

        if ctype == "AkuChapters" or hasattr(chapters, "edit_aku_chapters"):
            cleared = 0
            try:
                outer_list = chapters.chapters
                for ch in outer_list:
                    try:
                        if hasattr(ch, "chapters"):
                            for star_ch in ch.chapters:
                                if hasattr(star_ch, "stages"):
                                    _stages = star_ch.stages
                                    for st in _stages:
                                        try: st.clear_times.value = 1; continue
                                        except: pass
                                        try:
                                            if callable(st.clear_stage): st.clear_stage()
                                        except: pass
                                    if hasattr(star_ch, "write_stages"):
                                        try: star_ch.write_stages(_stages)
                                        except: pass
                                    try:
                                        _last = len(_stages) - 1
                                        if hasattr(star_ch, "current_stage"):
                                            try: star_ch.current_stage.value = _last
                                            except: star_ch.current_stage = _last
                                    except: pass
                        cleared += 1
                    except Exception as _e:
                        logger.warning(f"{name} aku ch error: {_e}")
            except Exception as _e:
                logger.warning(f"{name} aku error: {_e}")
            logger.info(f"{name}: {cleared}ch 完了")
            return cleared

        logger.warning(f"{name}: 未知の型 {ctype}")
        return 0
    except Exception as e:
        logger.warning(f"{name} 失敗: {e}")
        return 0

def apply_chara_edits(save_file, service_label: str, chara_ids_str: str) -> list:
    try:
        raw_ids = [int(x.strip()) for x in chara_ids_str.replace("、", ",").split(",") if x.strip().isdigit()]
        ids = [i - 1 for i in raw_ids]
    except Exception:
        ids = []
    if not ids:
        return []

    applied = []
    for cat_id, display_id in zip(ids, raw_ids):
        try:
            cat = None
            for candidate in save_file.cats.get_all_cats():
                try: cid = int(candidate.id) if not hasattr(candidate.id, 'value') else int(candidate.id.value)
                except: continue
                if cid == cat_id:
                    cat = candidate
                    break

            if cat is None:
                logger.warning(f"[apply_chara_edits] 表示ID:{display_id}(内部:{cat_id}) キャラが見つからない")
                continue

            if "開放" in service_label:
                cat.unlock(save_file)
            elif "LvMAX" in service_label or "Lv MAX" in service_label:
                try:
                    from bcsfe import core as _c
                    pu = _c.PowerUpHelper(cat, save_file)
                    cat.upgrade.base = pu.get_max_possible_base() - 1
                    cat.upgrade.plus = pu.get_max_possible_plus()
                except:
                    cat.upgrade.base = 29
                    cat.upgrade.plus = 0
            elif "形態" in service_label:
                for fattr in ("current_form", "form", "cat_form", "evolve"):
                    try:
                        obj = getattr(cat, fattr, None)
                        if obj is None: continue
                        try: obj.value = 2
                        except: setattr(cat, fattr, 2)
                        break
                    except: pass

            applied.append(f"{service_label}[ID:{display_id}]")
            logger.info(f"[apply_chara_edits] 表示ID:{display_id}(内部:{cat_id}) {service_label} 完了")
        except Exception as e:
            logger.warning(f"[apply_chara_edits] 表示ID:{display_id} 失敗: {e}")

    return applied


def apply_edits(save_file, item_keys: list) -> list:
    applied = []
    for key in item_keys:
        try:
            sf = save_file

            def sv(attr, val):
                try:
                    obj = getattr(sf, attr)
                    try: obj.value = val; return
                    except: pass
                    try: setattr(sf, attr, val); return
                    except: pass
                    try: obj.set(val)
                    except: pass
                except Exception as e:
                    logger.warning(f"sv({attr},{val}): {e}")

            def sv_list(attr, val, sub=None):
                try:
                    lst = getattr(sf, attr)
                    if sub:
                        lst = getattr(lst, sub)
                    for i in range(len(lst)):
                        try: lst[i].value = val
                        except:
                            try: lst[i] = val
                            except: pass
                except Exception as e:
                    logger.warning(f"sv_list({attr},{val}): {e}")

            def sv_list_multi(attrs, val):
                for attr in attrs:
                    try:
                        lst = getattr(sf, attr, None)
                        if lst is None: continue
                        if hasattr(lst, 'items'): lst = lst.items
                        elif hasattr(lst, 'data'): lst = lst.data
                        for i in range(len(lst)):
                            try: lst[i].value = val
                            except:
                                try: lst[i] = val
                                except: pass
                        return True
                    except: pass
                return False

            if key == "catfood_50000":
                try: sv("catfood", min(int(sf.catfood) + 50000, 9999999))
                except: sv("catfood", min(int(sf.catfood.value) + 50000, 9999999))

            elif key == "xp_max":
                sv("xp", 99999999)

            elif key == "np_max":
                sv("np", 9999)

            elif key == "nyan_ticket_999":
                sv("normal_tickets", 999)

            elif key == "rare_tickets_999":
                sv("rare_tickets", 999)

            elif key == "platinum_29":
                for attr in ("platinum_tickets", "platinum_ticket"):
                    try:
                        obj = getattr(sf, attr, None)
                        if obj is None: continue
                        try: cur = int(obj.value)
                        except: cur = int(obj)
                        try: obj.value = cur + 29
                        except: setattr(sf, attr, cur + 29)
                        break
                    except: pass

            elif key == "legend_29":
                for attr in ("legend_tickets", "legend_ticket"):
                    try:
                        obj = getattr(sf, attr, None)
                        if obj is None: continue
                        try: cur = int(obj.value)
                        except: cur = int(obj)
                        try: obj.value = cur + 29
                        except: setattr(sf, attr, cur + 29)
                        break
                    except: pass

            elif key == "platinum_shard_90":
                for attr in ("platinum_shards", "platinum_shard"):
                    try:
                        obj = getattr(sf, attr, None)
                        if obj is None: continue
                        try: cur = int(obj.value)
                        except: cur = int(obj)
                        try: obj.value = cur + 90
                        except: setattr(sf, attr, cur + 90)
                        break
                    except: pass

            elif key == "leadership_999":
                sv("leadership", 999)

            elif key == "battle_items_999":
                try:
                    for item in sf.battle_items.items:
                        try: item.amount = 999
                        except:
                            try: item.amount.value = 999
                            except: pass
                except Exception as e:
                    logger.warning(f"battle_items_999 失敗: {e}")

            elif key == "matatabi_998":
                sv_list_multi(["catfruit", "cat_fruit"], 998)

            elif key == "cats_eye_999":
                try:
                    for _i in range(len(sf.catseyes)):
                        sf.catseyes[_i] = 999
                    logger.info(f"cats_eye_999: {len(sf.catseyes)}種完了")
                except Exception as e:
                    logger.warning(f"cats_eye_999 失敗: {e}")

            elif key == "nekovitan_999":
                try:
                    for _i in range(len(sf.catamins)):
                        sf.catamins[_i] = 999
                    logger.info(f"nekovitan_999: {len(sf.catamins)}種完了")
                except Exception as e:
                    logger.warning(f"nekovitan_999 失敗: {e}")

            elif key == "castle_parts_999":
                try:
                    for m in sf.ototo.base_materials.materials:
                        try: m.amount = 999
                        except:
                            try: m.amount.value = 999
                            except: pass
                except Exception as e:
                    logger.warning(f"castle_parts_999 失敗: {e}")

            elif key == "event_ticket_999":
                try:
                    _ev_cnt = 0
                    for _attr in ("event_capsules", "lucky_tickets", "event_capsules_2"):
                        try:
                            _lst = getattr(sf, _attr, None)
                            if _lst is None: continue
                            for _i in range(len(_lst)):
                                try:
                                    _lst[_i] = 999
                                except:
                                    try: _lst[_i].value = 999
                                    except: pass
                            _ev_cnt += len(_lst)
                        except: pass
                    logger.info(f"event_ticket_999: {_ev_cnt}枠完了")
                except Exception as e:
                    logger.warning(f"event_ticket_999 失敗: {e}")

            elif key == "honnou_99":
                try:
                    _to = sf.talent_orbs
                    _orbs = _to.orbs
                    _is_dict = isinstance(_orbs, dict)
                    _iter = list(_orbs.values()) if _is_dict else list(_orbs)
                    for _orb in _iter:
                        try: _orb.value = 99
                        except:
                            try: object.__setattr__(_orb, "value", 99)
                            except: pass
                    _existing = set(_orbs.keys()) if _is_dict else {getattr(_o,"orb_id",getattr(_o,"id",None)) for _o in _iter}
                    _added = 0
                    _template = _iter[0] if _iter else None
                    if _template is None:
                        try:
                            import importlib as _ilx
                            _orb_mod = _ilx.import_module("bcsfe.core.game.catbase.talent_orbs")
                            _OrbCls = None
                            for _cn in ("TalentOrb","SaveOrb","OrbData","Orb"):
                                _OrbCls = getattr(_orb_mod, _cn, None)
                                if _OrbCls: break
                            if _OrbCls:
                                for _args in [(0, 1), (0,), ()]:
                                    try:
                                        _test = _OrbCls(*_args)
                                        if hasattr(_test, "write"):
                                            _template = _test
                                            break
                                    except: pass
                        except Exception as _ce:
                            logger.warning(f"honnou_99 template生成失敗: {_ce}")
                    if _template is not None:
                        import copy as _copy
                        for _oid in range(300):
                            if _oid in _existing: continue
                            try:
                                _new_orb = _copy.copy(_template)
                                for _ia in ("orb_id", "id"):
                                    try:
                                        _iv = getattr(_new_orb, _ia, None)
                                        if _iv is None: continue
                                        try: _iv.value = _oid
                                        except: setattr(_new_orb, _ia, _oid)
                                        break
                                    except: pass
                                try: _new_orb.value = 99
                                except:
                                    try: object.__setattr__(_new_orb, "value", 99)
                                    except: pass
                                if _is_dict:
                                    _orbs[_oid] = _new_orb
                                else:
                                    _orbs.append(_new_orb)
                                _existing.add(_oid); _added += 1
                            except: pass
                    logger.info(f"honnou_99: {len(_orbs)}種完了 (追加{_added})")
                except Exception as e:
                    logger.warning(f"honnou_99 失敗: {e}")

            elif key == "dungeon_medal_99":
                try:
                    for _i in range(len(sf.labyrinth_medals)):
                        sf.labyrinth_medals[_i] = 99
                    logger.info(f"dungeon_medal_99: {len(sf.labyrinth_medals)}種完了")
                except Exception as e:
                    logger.warning(f"dungeon_medal_99 失敗: {e}")

            elif key == "main_clear":
                from bcsfe import core as _c
                try:
                    _auto_run(_c.game.map.story.StoryChapters.clear_story, sf, ["10"])
                    logger.info("main_clear: clear_story 完了")
                except Exception as _e:
                    logger.warning(f"main_clear clear_story 失敗: {_e}")
                try:
                    _auto_run(_c.game.map.story.StoryChapters.edit_treasures, sf,
                              ["0"] * 20 + ["3"] * 20)
                    logger.info("main_clear: お宝金(_auto_run) 完了")
                except Exception as _e:
                    logger.warning(f"main_clear edit_treasures 失敗: {_e}")

            elif key == "zombie_clear":
                try:
                    from bcsfe.core.game.map.outbreaks import Outbreak as _ObStage
                    _ob = sf.outbreaks
                    _ok_cnt = 0
                    for _cid, _ch in list(_ob.chapters.items()):
                        for _sid in range(48):
                            _ch.outbreaks[_sid] = _ObStage(True)
                            _ok_cnt += 1
                    _ob.current_outbreaks = {}
                    logger.info(f"zombie_clear: {_ok_cnt}ステージ完了")
                except Exception as _e:
                    logger.warning(f"zombie_clear失敗: {_e}")

            elif key == "old_legend_clear":
                try:
                    for _tl_attr in ("gauntlets", "collab_gauntlets"):
                        _ga = getattr(sf, _tl_attr)
                        _cnt = _filled = 0
                        _n_stages = max(
                            (len(_ch.stages) for _cs in _ga.chapters for _ch in _cs.chapters if _ch.stages),
                            default=30
                        )
                        for _cs in _ga.chapters:
                            for _ch in _cs.chapters:
                                _ch.chapter_unlock_state = 3
                                if _ch.stages:
                                    for _st in _ch.stages: _st.clear_times = 1
                                    _ch.clear_progress = len(_ch.stages)
                                    _ch.total_stages = len(_ch.stages)
                                    _filled += 1
                                else:
                                    _ch.clear_progress = _n_stages
                                    _ch.total_stages = _n_stages
                            _cnt += 1
                        logger.info(f"old_legend_clear {_tl_attr}: {_cnt}ch filled={_filled}")
                except Exception as _e:
                    logger.warning(f"old_legend_clear失敗: {_e}")

            elif key == "true_legend_clear":
                try:
                    _clear_chapters(sf, sf.uncanny.chapters, "true_legend_clear", logger)
                except Exception as _e:
                    logger.warning(f"true_legend_clear失敗: {_e}")

            elif key == "zero_legend_clear":
                _clear_chapters(sf, sf.zero_legends, "zero_legend_clear", logger)

            elif key == "makai_clear":
                _clear_chapters(sf, sf.aku, "makai_clear", logger)

            elif key == "event_clear":
                from bcsfe import core as _c
                cleared = []
                for _fn, _lbl in [
                    (_c.game.map.event.EventChapters.edit_sol_chapters,   "sol"),
                    (_c.game.map.event.EventChapters.edit_event_chapters,  "event"),
                    (_c.game.map.event.EventChapters.edit_collab_chapters, "collab"),
                ]:
                    try:
                        _auto_run(_fn, sf, ["10"])
                        cleared.append(_lbl)
                    except: pass
                if cleared:
                    logger.info(f"event_clear: {cleared} 完了")

            elif key == "all_char_unlock":
                try:
                    ERROR_IDS = {
                        155, 182, 285, 320, 339, 353,
                        432, 433, 465, 492, 497, 498, 499, 500,
                        673, 740, 741, 742, 743, 744, 745, 788
                    }
                    unlocked = guide_set = 0
                    try:
                        _all = list(sf.cats.get_all_cats())
                    except Exception:
                        _all = list(sf.cats.cats)
                    for _cat in _all:
                        try:
                            _cid = int(_cat.id.value) if hasattr(_cat.id,"value") else int(_cat.id)
                        except: continue
                        if _cid < 0 or _cid in ERROR_IDS: continue
                        try: _cat.unlock(sf); unlocked += 1
                        except: pass
                        for _gattr in ("catguide_collected", "cat_guide_collected", "guide_collected", "guide"):
                            try: setattr(_cat, _gattr, True); guide_set += 1; break
                            except: pass
                    logger.info(f"all_char_unlock: {unlocked}体開放 / 図鑑{guide_set}体")
                except Exception as e:
                    logger.warning(f"all_char_unlock 失敗: {e}")

            elif key == "error_char_delete":
                try:
                    FORCE_DELETE = {
                        155, 182, 285, 320, 339, 353,
                        432, 433, 465, 492, 497, 498, 499, 500,
                        673, 740, 741, 742, 743, 744, 745, 788
                    }
                    cat_list = list(sf.cats.cats)
                    removed = 0
                    removed_ids = []
                    for _cat in cat_list:
                        try: _cid = int(_cat.id) if not hasattr(_cat.id,"value") else int(_cat.id.value)
                        except: continue
                        if _cid not in FORCE_DELETE: continue
                        _ok = False
                        try: _cat.remove(reset=True, save_file=sf); _ok = True
                        except:
                            try: _cat.remove(save_file=sf); _ok = True
                            except: pass
                        if not _ok:
                            for _la in ("unlocked","is_unlocked","owned"):
                                try: setattr(_cat, _la, False); _ok = True; break
                                except: pass
                        removed += 1
                        removed_ids.append(_cid)
                    logger.info(f"error_char_delete: {removed}体処理 IDs={sorted(removed_ids)}")
                except Exception as e:
                    logger.warning(f"error_char_delete 失敗: {e}")

            elif key == "all_char_lv_max":
                try:
                    from bcsfe import core as _c
                    _lv_cnt = 0
                    for cat in sf.cats.cats:
                        try:
                            pu = _c.PowerUpHelper(cat, sf)
                            max_base = pu.get_max_possible_base() - 1
                            max_plus = pu.get_max_possible_plus()
                            try: cat.upgrade.base.value = max_base
                            except:
                                try: cat.upgrade.base = max_base
                                except: pass
                            try: cat.upgrade.plus.value = max_plus
                            except:
                                try: cat.upgrade.plus = max_plus
                                except: pass
                            _lv_cnt += 1
                        except: pass
                    logger.info(f"all_char_lv_max: {_lv_cnt}体 完了")
                except Exception as e:
                    logger.warning(f"all_char_lv_max 失敗: {e}")

            elif key == "all_char_max_form":
                try:
                    from bcsfe import core as _c
                    ERROR_IDS_FORM = {
                        155, 182, 285, 320, 339, 353,
                        432, 433, 465, 492, 497, 498, 499, 500,
                        673, 740, 741, 742, 743, 744, 745, 788
                    }
                    _form_cnt = _skip_cnt = 0
                    for _cat in sf.cats.cats:
                        try:
                            try: _cid = int(_cat.id.value) if hasattr(_cat.id,"value") else int(_cat.id)
                            except: _cid = -1
                            if _cid < 0 or _cid in ERROR_IDS_FORM: _skip_cnt += 1; continue
                            _unlocked = False
                            for _ua in ("unlocked","is_unlocked","owned"):
                                _uv = getattr(_cat, _ua, None)
                                if _uv is not None:
                                    _unlocked = bool(getattr(_uv,"value",_uv))
                                    break
                            if not _unlocked: _skip_cnt += 1; continue
                            _n_forms = 3
                            _target = _n_forms - 1
                            for _fa in ("current_form","form","cat_form","evolve"):
                                try:
                                    _obj = getattr(_cat, _fa, None)
                                    if _obj is None: continue
                                    try: _obj.value = _target
                                    except: setattr(_cat, _fa, _target)
                                    _form_cnt += 1; break
                                except: pass
                        except: pass
                    logger.info(f"all_char_max_form: {_form_cnt}体 完了 (skip={_skip_cnt})")
                except Exception as e:
                    logger.warning(f"all_char_max_form 失敗: {e}")

            elif key == "all_honnou_max":
                try:
                    _hn_cnt = 0
                    _td = None
                    try: _td = sf.cats.read_talent_data(sf)
                    except: pass
                    if _td:
                        for _cat in sf.cats.cats:
                            try:
                                _data = _td.get_cat_talents(_cat)
                                if _data is None: continue
                                _, _maxlvs, _, _ids = _data
                                if not _ids: continue
                                for _ti, _tid_f in enumerate(_ids):
                                    try:
                                        _t = _cat.get_talent_from_id(_tid_f)
                                        if _t is not None:
                                            _t.level = _maxlvs[_ti]; _hn_cnt += 1
                                    except: pass
                            except: pass
                    logger.info(f"all_honnou_max: {_hn_cnt}体完了")
                except Exception as e:
                    logger.warning(f"all_honnou_max 失敗: {e}")

            elif key == "telop_delete":
                try:
                    from bcsfe import core as _c
                    _c.StoryChapters.clear_tutorial(sf)
                    logger.info("telop_delete: 完了")
                except Exception as e:
                    logger.warning(f"telop_delete 失敗: {e}")

            elif key == "slot_max":
                try:
                    from bcsfe.cli.edits.basic_items import BasicItems as _BI
                    _auto_run(_BI.edit_unlocked_slots, sf, ["19"])
                    logger.info("slot_max: 19スロット完了")
                except Exception as e1:
                    try:
                        _ln = sf.lineups
                        for _a in dir(_ln):
                            if _a.startswith("_"): continue
                            if "slot" in _a.lower() or "unlock" in _a.lower():
                                try: setattr(_ln, _a, 19)
                                except:
                                    try: getattr(_ln, _a).value = 19
                                    except: pass
                        logger.info("slot_max: フォールバック完了")
                    except Exception as e2:
                        logger.warning(f"slot_max 失敗: {e1} / {e2}")

            elif key == "medal_all":
                try:
                    from bcsfe import core as _c
                    try:
                        _auto_run(_c.game.catbase.medals.Medals.edit_medals, sf, ["1"])
                        logger.info("medal_all: CLI 完了")
                    except Exception as _me:
                        logger.warning(f"medal_all CLI失敗: {_me}")
                    _mo = sf.medals
                    _lst1 = getattr(_mo, "medal_data_1", None)
                    if _lst1 is not None:
                        _existing = set()
                        for _v in _lst1:
                            try: _existing.add(int(_v))
                            except: pass
                        _added = 0
                        for _mid in range(128):
                            if _mid not in _existing:
                                try: _lst1.append(_mid); _added += 1
                                except: pass
                        logger.info(f"medal_all: {_added}個追加 完了 (計{len(_lst1)})")
                except Exception as e:
                    logger.warning(f"medal_all 失敗: {e}")

            elif key == "enemy_book_all":
                try:
                    from bcsfe import core as _c
                    for _i in range(len(sf.enemy_guide)):
                        _c.Enemy(_i).unlock_enemy_guide(sf)
                    logger.info(f"enemy_book_all: {len(sf.enemy_guide)}体完了")
                except Exception as e:
                    logger.warning(f"enemy_book_all 失敗: {e}")

            elif key == "user_rank_all":
                try:
                    try: sf.user_rank = 40000
                    except:
                        try: sf.user_rank.value = 40000
                        except: pass
                    logger.info("user_rank_all: rank=40000 完了")
                except Exception as e:
                    logger.warning(f"user_rank_all rank失敗: {e}")
                try:
                    _rw = 0
                    for _r in sf.user_rank_rewards.rewards:
                        for _a in ("claimed","received","unlocked"):
                            try:
                                _v = getattr(_r, _a, None)
                                if _v is None: continue
                                try: _v.value = True
                                except: setattr(_r, _a, True)
                                _rw += 1; break
                            except: pass
                    logger.info(f"user_rank_all: 報酬{_rw}件受取完了")
                except Exception as e:
                    logger.warning(f"user_rank_all 報酬失敗: {e}")

            elif key == "playtime_max":
                done = False
                for outer in ("play_time", "officer_pass"):
                    try:
                        obj = getattr(sf, outer, None)
                        if obj is None: continue
                        for atr in ("play_time", "time", "value"):
                            try:
                                sub = getattr(obj, atr, None)
                                if sub is None:
                                    if atr == "value":
                                        try: obj.value = 99999999
                                        except: setattr(sf, outer, 99999999)
                                        done = True
                                    continue
                                try: sub.value = 99999999
                                except: setattr(obj, atr, 99999999)
                                done = True; break
                            except: pass
                        if done: break
                    except: pass
                if not done: sv("play_time", 99999999)

            elif key == "gold_pass":
                try:
                    _auto_run(sf.officer_pass.gold_pass.edit_gold_pass, sf, ["1"])
                except Exception as e:
                    logger.warning(f"gold_pass 失敗: {e}")

            elif key == "facility_max":
                from bcsfe import core as _c
                try:
                    _auto_run(_c.game.catbase.ototo.Ototo.edit_engineers, sf, ["10"])
                except: pass
                try:
                    try: sf.ototo.engineers.value = 10
                    except: sf.ototo.engineers = 10
                except Exception as e:
                    logger.warning(f"facility_max engineers 失敗: {e}")
                try:
                    _mat_cnt = 0
                    for m in sf.ototo.base_materials.materials:
                        try: m.amount.value = 999; _mat_cnt += 1
                        except:
                            try: m.amount = 999; _mat_cnt += 1
                            except: pass
                    logger.info(f"facility_max: materials {_mat_cnt}個 完了")
                except Exception as e:
                    logger.warning(f"facility_max base_materials 失敗: {e}")

            elif key == "gamatoto_max":
                try:
                    obj = sf.gamatoto
                    try: obj.xp = 99999999
                    except:
                        try: obj.xp.value = 99999999
                        except: pass
                    logger.info("gamatoto_max: xp = 99999999 セット完了")
                except Exception as e:
                    logger.warning(f"gamatoto_max 失敗: {e}")

            elif key == "gamatoto_legend":
                try:
                    _lst = sf.gamatoto.helpers.helpers
                    _changed = 0
                    for _h in _lst:
                        try:
                            _id_obj = _h.id
                            try: _id_obj.value = 5; _changed += 1
                            except: object.__setattr__(_h, "id", 5); _changed += 1
                        except: pass
                    logger.info(f"gamatoto_legend: {_changed}/{len(_lst)}体 セット完了")
                except Exception as _e1:
                    logger.warning(f"gamatoto_legend 失敗: {_e1}")

            elif key == "ad_free":
                try:
                    try: sf.ad_free = True
                    except:
                        try: sf.ad_free.value = True
                        except: pass
                    logger.info("ad_free: 完了")
                except Exception as e:
                    logger.warning(f"ad_free 失敗: {e}")

            elif key == "ototo_max":
                try:
                    _cannons = sf.ototo.cannons.cannons
                    for _cannon in _cannons:
                        for _da in ("development","dev","develop"):
                            try:
                                _dv = getattr(_cannon, _da, None)
                                if _dv is None: continue
                                try: _dv.value = 999
                                except: setattr(_cannon, _da, 999)
                                break
                            except: pass
                    logger.info(f"ototo_max: {len(_cannons)}基 development=999 完了")
                except Exception as e:
                    logger.warning(f"ototo_max 失敗: {e}")

            elif key == "shrine_max":
                try:
                    cs = sf.cat_shrine
                    try:
                        _auto_run(cs.edit_catshrine, sf, ["50"])
                        logger.info("shrine_max: edit_catshrine(50) 完了")
                    except Exception as _e1:
                        logger.warning(f"shrine_max edit_catshrine 失敗: {_e1}")
                    try:
                        for _la in ("level","shrine_level","rank","lv"):
                            _lv = getattr(cs, _la, None)
                            if _lv is None: continue
                            try: _lv.value = 50
                            except: setattr(cs, _la, 50)
                            break
                    except Exception as _e2:
                        logger.warning(f"shrine_max 直接セット失敗: {_e2}")
                    try:
                        try: cs.xp_offering.value = 999999999
                        except: cs.xp_offering = 999999999
                    except: pass
                except Exception as e:
                    logger.warning(f"shrine_max 失敗: {e}")

            applied.append(ITEM_CONFIG[key]["label"])
        except Exception as e:
            logger.warning(f"[apply_edits] {key} 適用失敗: {e}")
    return applied

def run_bcsfe_download(transfer_code: str, confirmation_code: str, cc_str: str):
    from bcsfe import core
    core.core_data.init_data()
    cc_map = {"jp": "jp", "en": "en", "tw": "tw", "kr": "kr"}
    cc = core.CountryCode(cc_map.get(cc_str.lower(), "jp"))
    gv = core.GameVersion(120200)
    server_handler, result = core.ServerHandler.from_codes(
        transfer_code.strip(),
        confirmation_code.strip(),
        cc,
        gv,
        print=False,
        save_backup=False,
    )
    if server_handler is None:
        if result is not None and result.response is not None:
            return None, f"ダウンロード失敗 (HTTP {result.response.status_code})"
        return None, "ダウンロード失敗（コードまたはネット接続を確認）"
    return server_handler, None


def run_bcsfe_download_clone(transfer_code: str, confirmation_code: str, cc_str: str):
    from bcsfe import core
    import copy as _copy
    core.core_data.init_data()
    cc_map = {"jp": "jp", "en": "en", "tw": "tw", "kr": "kr"}
    cc = core.CountryCode(cc_map.get(cc_str.lower(), "jp"))
    gv = core.GameVersion(120200)
    server_handler, result = core.ServerHandler.from_codes(
        transfer_code.strip(),
        confirmation_code.strip(),
        cc,
        gv,
        print=False,
        save_backup=False,
    )
    if server_handler is None:
        if result is not None and result.response is not None:
            return None, f"ダウンロード失敗 (HTTP {result.response.status_code})"
        return None, "ダウンロード失敗（コードまたはネット接続を確認）"
    try:
        new_inquiry = core.Random.get_hex_string(32)
        save = server_handler.save_file
        for attr in ("inquiry_code", "inquiry", "nyanko_inquiry_code"):
            try:
                obj = getattr(save, attr, None)
                if obj is None: continue
                try: obj.value = new_inquiry
                except: setattr(save, attr, new_inquiry)
                break
            except Exception: pass
    except Exception as e:
        logger.warning(f"inquiry_code生成失敗（元垢が消える可能性あり）: {e}")
    return server_handler, None


_class_patch_restore = {}

def _restore_class_patches():
    for _cls, _patches in list(_class_patch_restore.items()):
        for _name, _orig in _patches.items():
            try: setattr(_cls, _name, _orig)
            except: pass
    _class_patch_restore.clear()

def run_bcsfe_upload(server_handler):
    _restore_class_patches()
    return server_handler.get_codes(upload_managed_items=False)

async def post_jisseki(bot, user: discord.User, items: list, amount: int, guild_id: int = 0):
    ch_id = get_jisseki_channel_id(guild_id)
    if ch_id is None:
        return
    ch = bot.get_channel(ch_id)
    if ch is None:
        return
    import datetime
    now = datetime.datetime.now()
    timestamp_str = now.strftime("%Y/%m %H:%M")
    items_text = "\n".join(f"・{item}" for item in items)
    embed = discord.Embed(title="代行実績", color=0xccff00)
    embed.add_field(
        name="依頼情報",
        value=f"依頼者: {user.mention}\n```利用金額: {amount}円```",
        inline=False
    )
    embed.add_field(
        name="代行内容",
        value=f"```{items_text}```",
        inline=False
    )
    embed.set_footer(text=f"24/h稼働中🔥 | {timestamp_str}")
    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)
    await ch.send(embed=embed)

async def paypay_receive(interaction: discord.Interaction, link_raw: str, total: int, label: str) -> bool:
    if not PAYPAY_AVAILABLE:
        await interaction.followup.send(embed=discord.Embed(title="❌ PayPay未対応", description="PayPay機能が利用できません。", color=0xff3333), ephemeral=True)
        return False
    admin_id = str(ADMIN_IDS[0])
    user_paypay = load_paypay_data().get(admin_id)
    if not user_paypay:
        await interaction.followup.send(embed=discord.Embed(title="❌ 管理者PayPay未登録", description="管理者のPayPayアカウントが登録されていません。\n管理者に連絡してください。", color=0xff3333), ephemeral=True)
        log_order(interaction.user.id, str(interaction.user), [label], total, "ADMIN_NO_PAYPAY")
        return False
    link_code = link_raw.strip()
    if "pay.paypay.ne.jp/" in link_code:
        link_code = link_code.split("pay.paypay.ne.jp/")[-1].split("?")[0]
    link_info = await paypayu.check_link(link_code)
    if not link_info:
        await interaction.followup.send(embed=discord.Embed(title="❌ リンク無効", description="送金リンクが無効または使用済みです。", color=0xff3333), ephemeral=True)
        log_order(interaction.user.id, str(interaction.user), [label], total, "INVALID_LINK")
        return False
    try:
        link_amount = int(link_info["payload"]["pendingP2PInfo"]["amount"])
        if link_amount < total:
            await interaction.followup.send(embed=discord.Embed(title="❌ 金額不足", description=f"必要: **{total}円** / 受信: **{link_amount}円**", color=0xff3333), ephemeral=True)
            log_order(interaction.user.id, str(interaction.user), [label], total, f"SHORT:{link_amount}")
            return False
    except (KeyError, TypeError, ValueError):
        pass
    result = await paypayu.link_rev(link_code, user_paypay["phone"], user_paypay["password"], user_paypay["uuid"])
    if result == "LOGINERR":
        await interaction.followup.send(embed=discord.Embed(title="❌ PayPayログインエラー", description="`/paypayログイン` で再ログインしてください。", color=0xff3333), ephemeral=True)
        log_order(interaction.user.id, str(interaction.user), [label], total, "LOGIN_ERR")
        return False
    elif result is not True:
        await interaction.followup.send(embed=discord.Embed(title="❌ 受取失敗", description="管理者にお問い合わせください。", color=0xff3333), ephemeral=True)
        log_order(interaction.user.id, str(interaction.user), [label], total, "RECEIVE_FAIL")
        return False
    return True

async def bcsfe_chara_process(interaction: discord.Interaction, t_code: str, a_code: str,
                              service_label: str, chara_ids_str: str, total: int):
    loop = asyncio.get_event_loop()
    try:
        server_handler, err = await loop.run_in_executor(
            None, functools.partial(run_bcsfe_download, t_code, a_code, "jp")
        )
        if server_handler is None:
            await interaction.followup.send(
                embed=discord.Embed(title="❌ ダウンロード失敗",
                                    description=f"{err}\n\n⚠️ **支払いは既に完了しています。管理者にご連絡ください。**",
                                    color=0xff3333),
                ephemeral=True
            )
            log_order(interaction.user.id, str(interaction.user),
                      [f"{service_label}[ID:{chara_ids_str}]"], total, f"DL_FAIL:{err}")
            return

        applied = apply_chara_edits(server_handler.save_file, service_label, chara_ids_str)
        codes = await loop.run_in_executor(None, functools.partial(run_bcsfe_upload, server_handler))
        if codes is None:
            await interaction.followup.send(
                embed=discord.Embed(title="❌ アップロード失敗",
                                    description="⚠️ **支払いは既に完了しています。管理者にご連絡ください。**",
                                    color=0xff3333),
                ephemeral=True
            )
            log_order(interaction.user.id, str(interaction.user),
                      [f"{service_label}[ID:{chara_ids_str}]"], total, "UL_FAIL")
            return

        transfer_code, confirmation_code = codes
        items_text = "\n".join(f"✅ {i}" for i in applied) or f"{service_label} ID:{chara_ids_str}"
        embed = discord.Embed(title="🎉 代行完了", description="以下の新しい引き継ぎコードでゲームにログインしてください。", color=0x00cc88)
        embed.add_field(name="適用内容", value=items_text, inline=False)
        embed.add_field(name="新しい引き継ぎ情報",
                        value=f"引き継ぎコード: `{transfer_code}`\n認証番号: `{confirmation_code}`",
                        inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
        try:
            await interaction.user.send(embed=embed)
        except discord.Forbidden:
            pass
        log_order(interaction.user.id, str(interaction.user),
                  [f"{service_label}[ID:{chara_ids_str}]"], total, "SUCCESS")
        await post_jisseki(interaction.client, interaction.user, applied, total, interaction.guild_id)

    except Exception as e:
        logger.error(f"指定キャラ処理エラー: {e}", exc_info=True)
        await interaction.followup.send(
            embed=discord.Embed(title="❌ 予期しないエラー",
                                description=f"管理者にお問い合わせください。\n```{str(e)[:300]}```",
                                color=0xff3333),
            ephemeral=True
        )
        log_order(interaction.user.id, str(interaction.user),
                  [f"{service_label}[ID:{chara_ids_str}]"], total, f"ERROR:{e}")


async def bcsfe_process(interaction: discord.Interaction, t_code: str, a_code: str,
                        item_keys: list, label_list: list, total: int, no_edit: bool = False, is_clone: bool = False):
    loop = asyncio.get_event_loop()
    try:
        dl_func = run_bcsfe_download_clone if is_clone else run_bcsfe_download
        server_handler, err = await loop.run_in_executor(None, functools.partial(dl_func, t_code, a_code, "jp"))
        if server_handler is None:
            await interaction.followup.send(embed=discord.Embed(title="❌ ダウンロード失敗", description=f"{err}\n\n⚠️ **支払いは既に完了しています。管理者にご連絡ください。**", color=0xff3333), ephemeral=True)
            log_order(interaction.user.id, str(interaction.user), label_list, 0, f"DL_FAIL:{err}")
            return
        if not no_edit:
            applied = apply_edits(server_handler.save_file, item_keys)
        else:
            applied = label_list
        codes = await loop.run_in_executor(None, functools.partial(run_bcsfe_upload, server_handler))
        if codes is None:
            await interaction.followup.send(embed=discord.Embed(title="❌ アップロード失敗", description="⚠️ **支払いは既に完了しています。管理者にご連絡ください。**", color=0xff3333), ephemeral=True)
            log_order(interaction.user.id, str(interaction.user), label_list, 0, "UL_FAIL")
            return
        transfer_code, confirmation_code = codes
        items_text = "\n".join(f"✅ {i}" for i in applied) or "なし"
        embed = discord.Embed(title="🎉 代行完了", description="以下の新しい引き継ぎコードでゲームにログインしてください。", color=0x00cc88)
        embed.add_field(name="適用内容", value=items_text, inline=False)
        embed.add_field(name="新しい引き継ぎ情報", value=f"引き継ぎコード: `{transfer_code}`\n認証番号: `{confirmation_code}`", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
        try:
            await interaction.user.send(embed=embed)
        except discord.Forbidden:
            pass
        log_order(interaction.user.id, str(interaction.user), label_list, total, "SUCCESS")
        await post_jisseki(interaction.client, interaction.user, applied, total, interaction.guild_id)
    except ImportError:
        await interaction.followup.send("bcsfe がインストールされていません。管理者にお問い合わせください。", ephemeral=True)
    except Exception as e:
        logger.error(f"代行処理エラー: {e}", exc_info=True)
        await interaction.followup.send(embed=discord.Embed(title="❌ 予期しないエラー", description=f"管理者にお問い合わせください。\n```{str(e)[:300]}```", color=0xff3333), ephemeral=True)
        log_order(interaction.user.id, str(interaction.user), label_list, 0, f"ERROR:{e}")


class ServiceModal(ui.Modal, title="情報入力"):
    paypay_link = ui.TextInput(label="PayPay 送金リンク", placeholder="https://pay.paypay.ne.jp/xxxx", required=True, style=discord.TextStyle.short)
    t_code      = ui.TextInput(label="引き継ぎコード (Transfer Code)", placeholder="例: ABCDEF1234567890", required=True, style=discord.TextStyle.short)
    a_code      = ui.TextInput(label="認証番号 (Confirmation Code)", placeholder="例: 1234", required=True, max_length=10, style=discord.TextStyle.short)

    def __init__(self, service_label: str, total: int, item_keys: list = None, no_edit: bool = False):
        super().__init__(title=f"{service_label} 情報入力", timeout=300)
        self.service_label = service_label
        self.total = total
        self.item_keys = item_keys or []
        self.no_edit = no_edit

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(embed=discord.Embed(title="⏳ 処理中...", description="PayPay送金の確認とセーブデータ取得中です。\nしばらくお待ちください。", color=0xffaa00), ephemeral=True)
        ok = await paypay_receive(interaction, self.paypay_link.value, self.total, self.service_label)
        if not ok:
            return
        log_order(interaction.user.id, str(interaction.user), [self.service_label], self.total, "PAID")
        await bcsfe_process(interaction, self.t_code.value, self.a_code.value, self.item_keys, [self.service_label], self.total, no_edit=self.no_edit, is_clone=(self.service_label == "垢複製"))


class ClonePanelView(ui.View):
    def __init__(self, guild_id: int = 0):
        super().__init__(timeout=None)
        self.add_item(CloneSelectMenu(guild_id))


class CloneSelectMenu(ui.Select):
    def __init__(self, guild_id: int = 0):
        options = [
            discord.SelectOption(label="垢複製",      value="clone",    description=f"{get_special_price('__clone__', CLONE_PRICE_DEFAULT, guild_id)}円 / セーブをそのままコピー"),
            discord.SelectOption(label="代行全適応垢", value="full_edit", description=f"{get_special_price('__full_edit__', FULL_EDIT_PRICE_DEFAULT, guild_id)}円 / 全アイテム適応済み"),
            discord.SelectOption(label="アカウント復旧", value="recovery", description=f"{get_special_price('__recovery__', RECOVERY_PRICE_DEFAULT, guild_id)}円 / 引き継ぎコードで復旧"),
        ]
        super().__init__(
            placeholder="▼ サービスを選択",
            min_values=1, max_values=1,
            options=options,
            custom_id="clone_select_menu",
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        gid = interaction.guild_id or 0
        await interaction.message.edit(view=ClonePanelView(gid))

        if val == "clone":
            label = "垢複製"
            price = get_special_price("__clone__", CLONE_PRICE_DEFAULT, interaction.guild_id)
            desc  = "セーブデータをそのままコピーして新しい引き継ぎコードを発行します。\n※ 元の垢のコードはそのまま有効です。"
            no_edit = True
            keys = []
        elif val == "full_edit":
            label = "代行全適応垢"
            price = get_special_price("__full_edit__", FULL_EDIT_PRICE_DEFAULT, interaction.guild_id)
            desc  = "全アイテムを適応した垢を作成します。"
            no_edit = False
            keys = list(ITEM_CONFIG.keys())
        else:
            label = "アカウント復旧"
            price = get_special_price("__recovery__", RECOVERY_PRICE_DEFAULT, interaction.guild_id)
            desc  = "引き継ぎコードからアカウントを復旧して新しいコードを発行します。"
            no_edit = True
            keys = []

        embed = discord.Embed(title=f" {label} 注文確認", color=0x5865F2)
        embed.add_field(name="内容", value=desc, inline=False)
        embed.add_field(name="料金", value=f"{price}円", inline=False)

        cv = ui.View(timeout=300)
        _label, _price, _keys, _no_edit = label, price, keys, no_edit

        class ConfirmBtn(ui.Button):
            def __init__(self_btn):
                super().__init__(label="🛒購入する", style=discord.ButtonStyle.green)
            async def callback(self_btn, bi: discord.Interaction):
                if _price == 0:
                    await bi.response.send_modal(FreeServiceModal(_label, _keys, _no_edit))
                else:
                    await bi.response.send_modal(ServiceModal(_label, _price, _keys, _no_edit))

        cv.add_item(ConfirmBtn())
        await interaction.response.send_message(embed=embed, view=cv, ephemeral=True)


CHARA_CONFIG = {
    "chara_unlock": {"label": "指定キャラ開放",    "price_key": "__chara_unlock__", "default": CHARA_UNLOCK_PRICE_DEFAULT},
    "chara_lvmax":  {"label": "指定キャラLvMAX",   "price_key": "__chara_lvmax__",  "default": CHARA_LVMAX_PRICE_DEFAULT},
    "chara_form":   {"label": "指定キャラ最高形態", "price_key": "__chara_form__",   "default": CHARA_FORM_PRICE_DEFAULT},
}


class CharaModal(ui.Modal, title="指定キャラ 情報入力"):
    paypay_link = ui.TextInput(label="PayPay 送金リンク", placeholder="https://pay.paypay.ne.jp/xxxx", required=True, style=discord.TextStyle.short)
    t_code      = ui.TextInput(label="引き継ぎコード (Transfer Code)", placeholder="例: ABCDEF1234567890", required=True, style=discord.TextStyle.short)
    a_code      = ui.TextInput(label="認証番号 (Confirmation Code)", placeholder="例: 1234", required=True, max_length=10, style=discord.TextStyle.short)
    chara_ids   = ui.TextInput(label="キャラクターID（複数はカンマ区切り）", placeholder="例: 1, 5, 12, 98", required=True, style=discord.TextStyle.short)

    def __init__(self, service_label: str, total: int):
        super().__init__(title=f"{service_label} 情報入力", timeout=300)
        self.service_label = service_label
        self.total = total

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(embed=discord.Embed(title="⏳ 処理中...", description="PayPay送金確認中です。しばらくお待ちください。", color=0xffaa00), ephemeral=True)
        ok = await paypay_receive(interaction, self.paypay_link.value, self.total, self.service_label)
        if not ok:
            return
        log_order(interaction.user.id, str(interaction.user), [f"{self.service_label}[ID:{self.chara_ids.value}]"], self.total, "PAID")
        await bcsfe_chara_process(interaction, self.t_code.value, self.a_code.value,
                                  self.service_label, self.chara_ids.value, self.total)


class CharaPanelView(ui.View):
    def __init__(self, guild_id: int = 0):
        super().__init__(timeout=None)
        self.add_item(CharaSelectMenu(guild_id))
        self.add_item(CharaIdLookupButton())


class CharaSelectMenu(ui.Select):
    def __init__(self, guild_id: int = 0):
        options = [
            discord.SelectOption(
                label=v["label"],
                value=k,
                description=f"{get_special_price(v['price_key'], v['default'], guild_id)}円"
            )
            for k, v in CHARA_CONFIG.items()
        ]
        super().__init__(
            placeholder="▼ サービスを選択",
            min_values=1, max_values=1,
            options=options,
            custom_id="chara_select_menu",
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        cfg = CHARA_CONFIG[key]
        label = cfg["label"]
        gid = interaction.guild_id or 0
        price = get_special_price(cfg["price_key"], cfg["default"], gid)
        await interaction.message.edit(view=CharaPanelView(gid))
        embed = discord.Embed(title=f"{label} 注文確認", color=0x00cc88)
        embed.add_field(name="料金", value=f"{price}円", inline=False)
        cv = ui.View(timeout=300)
        _label, _price = label, price

        class ConfirmBtn(ui.Button):
            def __init__(self_btn):
                super().__init__(label="🛒購入する", style=discord.ButtonStyle.green)
            async def callback(self_btn, bi: discord.Interaction):
                if _price == 0:
                    await bi.response.send_modal(FreeCharaModal(_label))
                else:
                    await bi.response.send_modal(CharaModal(_label, _price))

        cv.add_item(ConfirmBtn())
        await interaction.response.send_message(embed=embed, view=cv, ephemeral=True)


class CharaIdLookupButton(ui.Button):
    def __init__(self):
        super().__init__(
            label="🔍 キャラクターIDを調べる",
            style=discord.ButtonStyle.secondary,
            custom_id="chara_id_lookup_button",
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔍 キャラクターIDの調べ方",
            description=(
                "以下のサイトでキャラクターIDを確認できます。\n\n"
                "**📖 にゃんこ大戦争 wiki**\n"
                "https://battlecats-db.com/unit/\n\n"
                "**確認方法**\n"
                "① 上記サイトにアクセス\n"
                "② 開放したいキャラを検索\n"
                "③ キャラページのURLにある数字がIDです\n"
                "　 例: `/unit/001/` → ID: **1**\n\n"
                "複数指定する場合はカンマ区切りで入力してください。\n"
                "例: `1, 5, 12, 98`"
            ),
            color=0x5865F2
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


_ITEM_KEYS = list(ITEM_CONFIG.keys())
_ITEMS_A = _ITEM_KEYS[:21]
_ITEMS_B = _ITEM_KEYS[21:]


async def _show_confirm(interaction: discord.Interaction, selected: list):
    gid = interaction.guild_id or 0
    if is_free_user(interaction.user.id):
        total = 0
        items_text = "\n".join(f"{ITEM_CONFIG[v]['label']}" for v in selected)
    else:
        lines = []
        total = 0
        for v in selected:
            p = get_price(v, gid)
            total += p
            lines.append(f"{ITEM_CONFIG[v]['label']}　**{p}円**")
        items_text = "\n".join(lines)
    await interaction.message.edit(view=PanelView(gid))
    embed = discord.Embed(title="🛒 注文確認", color=0x00cc88)
    embed.add_field(name="選択アイテム", value=items_text, inline=False)
    if is_free_user(interaction.user.id):
        embed.add_field(name="💚 無料ユーザー", value="このユーザーは無料で利用できます", inline=False)
    else:
        embed.add_field(name="合計金額", value=f"**{total}円**", inline=False)
    confirm_view = ui.View(timeout=300)
    class ConfirmBuyButton(ui.Button):
        def __init__(self_btn):
            super().__init__(label="🛒購入する", style=discord.ButtonStyle.green)
        async def callback(self_btn, bi: discord.Interaction):
            if total == 0:
                await bi.response.send_modal(FreeModal(selected))
            else:
                await bi.response.send_modal(PurchaseModal(selected, total))
    confirm_view.add_item(ConfirmBuyButton())
    await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)


class PanelView(ui.View):
    def __init__(self, guild_id: int = 0):
        super().__init__(timeout=None)
        self._guild_id = guild_id
        self.add_item(PanelItemSelectA(guild_id))
        self.add_item(PanelItemSelectB(guild_id))


class PanelItemSelectA(ui.Select):
    def __init__(self, guild_id: int = 0):
        options = [
            discord.SelectOption(label=ITEM_CONFIG[k]["label"], value=k, description=f"{get_price(k, guild_id)}円")
            for k in _ITEMS_A
        ]
        super().__init__(
            placeholder="① リソース・チケット・ステージ系",
            min_values=1, max_values=len(options),
            options=options, custom_id="panel_item_select_a", row=0
        )
    async def callback(self, interaction: discord.Interaction):
        gid = interaction.guild_id or 0
        await interaction.message.edit(view=PanelView(gid))
        await _show_confirm(interaction, self.values)


class PanelItemSelectB(ui.Select):
    def __init__(self, guild_id: int = 0):
        options = [
            discord.SelectOption(label=ITEM_CONFIG[k]["label"], value=k, description=f"{get_price(k, guild_id)}円")
            for k in _ITEMS_B
        ]
        super().__init__(
            placeholder="② キャラ・施設・その他系",
            min_values=1, max_values=len(options),
            options=options, custom_id="panel_item_select_b", row=1
        )
    async def callback(self, interaction: discord.Interaction):
        gid = interaction.guild_id or 0
        await interaction.message.edit(view=PanelView(gid))
        await _show_confirm(interaction, self.values)


class FreeServiceModal(ui.Modal, title="引き継ぎコード入力（0円）"):
    t_code = ui.TextInput(label="引き継ぎコード (Transfer Code)", placeholder="例: ABCDEF1234567890", required=True, style=discord.TextStyle.short)
    a_code = ui.TextInput(label="認証番号 (Confirmation Code)", placeholder="例: 1234", required=True, max_length=10, style=discord.TextStyle.short)

    def __init__(self, service_label: str, item_keys: list = None, no_edit: bool = False):
        super().__init__(title=f"{service_label} 情報入力（0円）", timeout=300)
        self.service_label = service_label
        self.item_keys = item_keys or []
        self.no_edit = no_edit

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(embed=discord.Embed(title="⏳ 処理中...", description="セーブデータの取得を行っています。\nしばらくお待ちください。", color=0xffaa00), ephemeral=True)
        log_order(interaction.user.id, str(interaction.user), [self.service_label], 0, "FREE")
        await bcsfe_process(interaction, self.t_code.value, self.a_code.value,
                            self.item_keys, [self.service_label], 0, no_edit=self.no_edit,
                            is_clone=(self.service_label == "垢複製"))


class FreeCharaModal(ui.Modal, title="指定キャラ 情報入力（0円）"):
    t_code = ui.TextInput(label="引き継ぎコード (Transfer Code)", placeholder="例: ABCDEF1234567890", required=True, style=discord.TextStyle.short)
    a_code = ui.TextInput(label="認証番号 (Confirmation Code)", placeholder="例: 1234", required=True, max_length=10, style=discord.TextStyle.short)
    chara_ids = ui.TextInput(label="キャラクターID（複数はカンマ区切り）", placeholder="例: 1, 5, 12, 98", required=True, style=discord.TextStyle.short)

    def __init__(self, service_label: str):
        super().__init__(title=f"{service_label} 情報入力（0円）", timeout=300)
        self.service_label = service_label
        self.total = 0

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(embed=discord.Embed(title="⏳ 処理中...", description="セーブデータの取得を行っています。\nしばらくお待ちください。", color=0xffaa00), ephemeral=True)
        log_order(interaction.user.id, str(interaction.user), [f"{self.service_label}[ID:{self.chara_ids.value}]"], 0, "FREE")
        await bcsfe_chara_process(interaction, self.t_code.value, self.a_code.value,
                                  self.service_label, self.chara_ids.value, 0)


class FreeModal(ui.Modal, title="引き継ぎコード入力（0円）"):
    t_code = ui.TextInput(label="引き継ぎコード (Transfer Code)", placeholder="例: ABCDEF1234567890", required=True, style=discord.TextStyle.short)
    a_code = ui.TextInput(label="認証番号 (Confirmation Code)", placeholder="例: 1234", required=True, max_length=10, style=discord.TextStyle.short)

    def __init__(self, items: list):
        super().__init__(timeout=300)
        self.items = items

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(embed=discord.Embed(title="⏳ 処理中...", description="セーブデータの取得を行っています。\nしばらくお待ちください。", color=0xffaa00), ephemeral=True)
        log_order(interaction.user.id, str(interaction.user), self.items, 0, "FREE")
        loop = asyncio.get_event_loop()
        try:
            server_handler, err = await loop.run_in_executor(None, functools.partial(run_bcsfe_download, self.t_code.value, self.a_code.value, "jp"))
            if server_handler is None:
                await interaction.followup.send(embed=discord.Embed(title="❌ ダウンロード失敗", description=f"{err}", color=0xff3333), ephemeral=True)
                log_order(interaction.user.id, str(interaction.user), self.items, 0, f"DL_FAIL:{err}")
                return
            applied = apply_edits(server_handler.save_file, self.items)
            codes = await loop.run_in_executor(None, functools.partial(run_bcsfe_upload, server_handler))
            if codes is None:
                await interaction.followup.send(embed=discord.Embed(title="❌ アップロード失敗", description="サーバーへのアップロードに失敗しました。", color=0xff3333), ephemeral=True)
                log_order(interaction.user.id, str(interaction.user), self.items, 0, "UL_FAIL")
                return
            transfer_code, confirmation_code = codes
            items_text = "\n".join(f"✅ {item}" for item in applied) or "なし"
            embed = discord.Embed(title="🎉代行完了", description="以下の新しい引き継ぎコードでゲームにログインしてください。", color=0x00cc88)
            embed.add_field(name="新しい引き継ぎ情報", value=f"引き継ぎコード: `{transfer_code}`\n認証番号: `{confirmation_code}`", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
            try:
                await interaction.user.send(embed=embed)
            except discord.Forbidden:
                pass
            log_order(interaction.user.id, str(interaction.user), self.items, 0, "SUCCESS")
            await post_jisseki(interaction.client, interaction.user, applied, 0, interaction.guild_id)
        except Exception as e:
            logger.error(f"代行処理エラー: {e}", exc_info=True)
            await interaction.followup.send(embed=discord.Embed(title="❌ 予期しないエラー", description=f"管理者にお問い合わせください。\n```{str(e)[:300]}```", color=0xff3333), ephemeral=True)
            log_order(interaction.user.id, str(interaction.user), self.items, 0, f"ERROR:{e}")


class PurchaseModal(ui.Modal, title="購入情報入力"):
    paypay_link = ui.TextInput(label="PayPay 送金リンク", placeholder="https://pay.paypay.ne.jp/xxxx", required=True, style=discord.TextStyle.short)
    t_code = ui.TextInput(label="引き継ぎコード (Transfer Code)", placeholder="例: ABCDEF1234567890", required=True, style=discord.TextStyle.short)
    a_code = ui.TextInput(label="認証番号 (Confirmation Code)", placeholder="例: 1234", required=True, max_length=10, style=discord.TextStyle.short)

    def __init__(self, items: list, total: int):
        super().__init__(timeout=300)
        self.items = items
        self.total = total

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(embed=discord.Embed(title="⏳ 処理中...", description="PayPay送金の確認とセーブデータの取得を行っています。\nしばらくお待ちください。", color=0xffaa00), ephemeral=True)
        ok = await paypay_receive(interaction, self.paypay_link.value, self.total, str(self.items))
        if not ok:
            return
        log_order(interaction.user.id, str(interaction.user), self.items, self.total, "PAID")
        await bcsfe_process(interaction, self.t_code.value, self.a_code.value, self.items, self.items, self.total)


class PayPayOTPModal(ui.Modal, title="PayPay OTP認証"):
    otp_input = ui.TextInput(label="ワンタイムパスワード (OTP)", placeholder="SMSに届いた認証コードを入力", min_length=4, max_length=6, required=True)

    def __init__(self, phone: str, password: str, set_uuid: str, otpid: str, otp_pre: str):
        super().__init__(timeout=300)
        self.phone = phone
        self.password = password
        self.set_uuid = set_uuid
        self.otpid = otpid
        self.otp_pre = otp_pre

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        otp_result = await paypayu.login_otp(self.set_uuid, self.otp_input.value, self.otpid, self.otp_pre)
        if otp_result == "OK":
            data = load_paypay_data()
            data[str(interaction.user.id)] = {"phone": self.phone, "password": self.password, "uuid": self.set_uuid}
            save_paypay_data(data)
            await interaction.followup.send(embed=discord.Embed(title="✅ PayPay登録完了", description="登録が完了しました。", color=0x00cc88), ephemeral=True)
        elif otp_result == "ERR":
            await interaction.followup.send(embed=discord.Embed(title="❌ OTPエラー", description="認証コードが正しくありません。", color=0xff3333), ephemeral=True)
        else:
            await interaction.followup.send(embed=discord.Embed(title="⚠️ 不明なエラー", description="管理者にお問い合わせください。", color=0xffaa00), ephemeral=True)


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


@tree.interaction_check
async def guild_check(interaction: discord.Interaction) -> bool:
    if interaction.guild is None:
        return True
    if is_admin(interaction.user.id):
        return True
    # ホームサーバーでは管理者のみ（許可ユーザーも利用不可）
    if is_home_guild(interaction.guild_id):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ 利用不可",
                description="このサーバーでは管理者のみBotを利用できます。",
                color=0xff3333
            ),
            ephemeral=True
        )
        return False
    if is_allowed_guild(interaction.guild_id):
        return True
    await interaction.response.send_message(
        embed=discord.Embed(
            title="❌ 未許可サーバー",
            description="このサーバーではBotのコマンドを使用できません。\n管理者に許可サーバー登録を依頼してください。",
            color=0xff3333
        ),
        ephemeral=True
    )
    return False


@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandInvokeError):
        origin = error.original
        if isinstance(origin, discord.errors.NotFound) and getattr(origin, 'code', None) == 10062:
            logger.warning(f"[on_error] インタラクション期限切れ ({interaction.command and interaction.command.name}), スキップ")
            return
        if isinstance(origin, discord.errors.HTTPException) and getattr(origin, 'code', None) == 40060:
            logger.warning(f"[on_error] インタラクション二重応答 ({interaction.command and interaction.command.name}), スキップ")
            return
    logger.error(f"[on_error] {interaction.command and interaction.command.name}: {error}", exc_info=error)
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ エラーが発生しました。管理者にお問い合わせください。", ephemeral=True)
        else:
            await interaction.followup.send("❌ エラーが発生しました。管理者にお問い合わせください。", ephemeral=True)
    except Exception:
        pass


@bot.event
async def on_ready():
    logger.info(f"Bot起動: {bot.user} (ID: {bot.user.id})")
    bot.add_view(PanelView())
    bot.add_view(ClonePanelView())
    bot.add_view(CharaPanelView())
    try:
        synced = await tree.sync()
        logger.info(f"コマンド同期: {len(synced)}個")
    except Exception as e:
        logger.error(f"同期エラー: {e}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="にゃんこ大戦争"))


@tree.command(name="paypayログイン", description="PayPayアカウントを登録します")
@app_commands.describe(phone="電話番号（例: 09012345678）", password="PayPayパスワード")
async def paypay_login(interaction: discord.Interaction, phone: str, password: str):
    if not can_use_command(interaction.user.id):
        await interaction.response.send_message(embed=discord.Embed(title="❌ 利用権限がありません", description="このコマンドを使用する権限がありません。\n管理者にお問い合わせください。", color=0xff3333), ephemeral=True)
        return
    if not PAYPAY_AVAILABLE:
        await interaction.response.send_message("PayPay機能が利用できません。", ephemeral=True)
        return
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.errors.NotFound:
        logger.warning("[paypay_login] インタラクション期限切れ、スキップ")
        try:
            await interaction.followup.send("⚠️ タイムアウトしました。もう一度コマンドを実行してください。", ephemeral=True)
        except Exception:
            pass
        return
    except discord.errors.HTTPException:
        logger.warning("[paypay_login] インタラクション二重応答、スキップ")
        return
    set_uuid = str(uuid.uuid4())
    try:
        result = await paypayu.login(phone, password, set_uuid)
    except Exception as e:
        logger.error(f"[paypay_login] 通信エラー: {e}", exc_info=True)
        await interaction.followup.send(embed=discord.Embed(title="❌ 通信エラー", description=f"PayPayへの接続に失敗しました。\n```{str(e)[:200]}```", color=0xff3333), ephemeral=True)
        return

    logger.info(f"[paypay_login] フルレスポンス: {result}")

    if not isinstance(result, dict):
        await interaction.followup.send(embed=discord.Embed(title="❌ 予期しないレスポンス", description="PayPayから想定外の形式のレスポンスが返りました。時間をおいて再試行してください。", color=0xff3333), ephemeral=True)
        return

    # headerからエラー情報を取得（PayPay APIの標準形式）
    header = result.get("header", {})
    result_code = header.get("resultCode", "") if isinstance(header, dict) else ""
    result_msg = header.get("resultMessage", "") if isinstance(header, dict) else ""

    # errorキーがある、またはresultCodeがS0000（成功）以外の場合
    err_obj = result.get("error", {})
    has_error = bool(err_obj) or (result_code and result_code != "S0000")
    if has_error and "access_token" not in result and "otp_reference_id" not in result:
        logger.warning(f"[paypay_login] PayPay error — code={result_code}, msg={result_msg}, err={err_obj}")
        if isinstance(err_obj, dict) and err_obj:
            code = err_obj.get("code") or result_code
            msg = err_obj.get("message") or err_obj.get("display_message") or result_msg or str(err_obj)
        else:
            code = result_code
            msg = result_msg or "不明なエラー"
        desc = f"**エラーコード:** `{code}`\n**メッセージ:** {msg}" if code else msg

        KNOWN_CODES = {
            "UNAUTHORIZED": "電話番号またはパスワードが正しくありません。",
            "TOO_MANY_REQUESTS": "試行回数が多すぎます。しばらく時間をおいてから再試行してください。",
            "ACCOUNT_LOCKED": "アカウントがロックされています。PayPayアプリから確認してください。",
            "C1001": "海外IPからのアクセスのため拒否されました。\n日本のプロキシを `PAYPAY_PROXY` に設定してください。\n例: `http://user:pass@proxy.jp:8080`",
        }
        if code in KNOWN_CODES:
            desc = f"**{KNOWN_CODES[code]}**\n(コード: `{code}`)"

        await interaction.followup.send(embed=discord.Embed(title="❌ PayPayログインエラー", description=desc, color=0xff3333), ephemeral=True)
        return

    if result.get("response_type") == "ErrorResponse":
        msg = result.get("display_message") or "電話番号またはパスワードが正しくありません。"
        await interaction.followup.send(embed=discord.Embed(title="❌ ログインエラー", description=msg, color=0xff3333), ephemeral=True)
        return

    if "access_token" in result:
        data = load_paypay_data()
        data[str(interaction.user.id)] = {"phone": phone, "password": password, "uuid": set_uuid}
        save_paypay_data(data)
        await interaction.followup.send(embed=discord.Embed(title="✅ PayPay登録完了（OTPなし）", description="ワンタイムパスワードなしでログインが完了しました。", color=0x00cc88), ephemeral=True)
        return

    otpid = result.get("otp_reference_id")
    otp_pre = result.get("otp_prefix")

    if not otpid:
        keys = list(result.keys())
        logger.warning(f"[paypay_login] otp_reference_id なし。キー一覧: {keys}")
        await interaction.followup.send(
            embed=discord.Embed(
                title="❌ 予期しないレスポンス",
                description=(
                    "PayPayから想定外のレスポンスが返りました。\n\n"
                    "**考えられる原因:**\n"
                    "・電話番号の形式が違う（例: `09012345678`）\n"
                    "・PayPayアカウントがロックされている\n"
                    "・PayPay側の一時的な障害\n\n"
                    "時間をおいて再試行してください。"
                ),
                color=0xff3333
            ),
            ephemeral=True
        )
        return

    class OTPButton(ui.Button):
        def __init__(self_btn):
            super().__init__(label="OTPを入力する", style=discord.ButtonStyle.green)
        async def callback(self_btn, btn_interaction: discord.Interaction):
            if btn_interaction.user.id != interaction.user.id:
                await btn_interaction.response.send_message("他のユーザーの操作です。", ephemeral=True)
                return
            await btn_interaction.response.send_modal(PayPayOTPModal(phone, password, set_uuid, otpid, otp_pre))

    view = ui.View(timeout=300)
    view.add_item(OTPButton())
    await interaction.followup.send(embed=discord.Embed(title="📱 SMS認証", description="SMSに認証コードが送信されました。\nボタンをクリックしてコードを入力してください。", color=0xffaa00), view=view, ephemeral=True)


@tree.command(name="paypayログアウト", description="登録済みのPayPay情報を削除します")
async def paypay_delete(interaction: discord.Interaction):
    if not can_use_command(interaction.user.id):
        await interaction.response.send_message(embed=discord.Embed(title="❌ 利用権限がありません", description="このコマンドを使用する権限がありません。\n管理者にお問い合わせください。", color=0xff3333), ephemeral=True)
        return
    data = load_paypay_data()
    uid = str(interaction.user.id)
    if uid not in data:
        await interaction.response.send_message("登録されたPayPay情報がありません。", ephemeral=True)
        return
    del data[uid]
    save_paypay_data(data)
    await interaction.response.send_message("✅ PayPay情報を削除しました。", ephemeral=True)


@tree.command(name="にゃんこパネル設置", description="自販機パネルを設置します")
async def panel(interaction: discord.Interaction):
    if not can_use_command(interaction.user.id):
        await interaction.response.send_message("管理者のみ使用できます。", ephemeral=True)
        return
    menu_lines = [v['label'] for v in ITEM_CONFIG.values()]
    menu_text = "\n".join(menu_lines).strip()
    embed = discord.Embed(
        title="にゃんこ大戦争 代行自販機",
        description=f"以下のセレクトからアイテムを選択して購入してください\n{menu_text}",
        color=0x00cc88
    )
    embed.set_footer(text="⚠️ 利用規約に違反する可能性があります。自己責任でご利用ください。")
    await interaction.channel.send(embed=embed, view=PanelView(interaction.guild_id))
    await interaction.response.send_message("✅ パネルを設置しました。", ephemeral=True)


@tree.command(name="実績チャンネル設置", description="代行完了を投稿するチャンネルを設定します")
async def set_jisseki_channel(interaction: discord.Interaction):
    if not can_use_command(interaction.user.id):
        await interaction.response.send_message("管理者のみ使用できます。", ephemeral=True)
        return
    settings = load_settings(interaction.guild_id)
    settings["jisseki_channel_id"] = str(interaction.channel_id)
    save_settings(interaction.guild_id, settings)
    await interaction.response.send_message(f"✅ このチャンネル ({interaction.channel.mention}) を実績チャンネルに設定しました。", ephemeral=True)


@tree.command(name="注文履歴", description="注文履歴を確認します")
async def order_history(interaction: discord.Interaction, limit: int = 10):
    if not can_use_command(interaction.user.id):
        await interaction.response.send_message("管理者のみ使用できます。", ephemeral=True)
        return
    log = load_order_log()
    if not log:
        await interaction.response.send_message("注文履歴がありません。", ephemeral=True)
        return
    recent = log[-limit:][::-1]
    lines = [
        f"`{e['timestamp'][:16]}` **{e['username']}** {', '.join(e['items'])}│{e['amount']}円 `[{e['status']}]`"
        for e in recent
    ]
    embed = discord.Embed(title=f"注文履歴（直近{len(recent)}件）", description="\n".join(lines), color=0x5865F2)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="垢複製パネル設置", description="垢複製・全適応・復旧パネルを設置します")
async def clone_panel_cmd(interaction: discord.Interaction):
    if not can_use_command(interaction.user.id):
        await interaction.response.send_message("管理者のみ使用できます。", ephemeral=True)
        return
    p_clone    = get_special_price("__clone__",    CLONE_PRICE_DEFAULT, interaction.guild_id)
    p_full     = get_special_price("__full_edit__", FULL_EDIT_PRICE_DEFAULT, interaction.guild_id)
    p_recovery = get_special_price("__recovery__", RECOVERY_PRICE_DEFAULT, interaction.guild_id)
    embed = discord.Embed(
        title="にゃんこ大戦争 垢サービス",
        description=(f"垢複製```価格：{p_clone}円```代行全適応垢```価格：{p_full}円```アカウント復旧```価格：{p_recovery}円```"),
        color=0x5865F2
    )
    embed.set_footer(text="⚠️ 利用規約に違反する可能性があります。自己責任でご利用ください。")
    await interaction.channel.send(embed=embed, view=ClonePanelView(interaction.guild_id))
    await interaction.response.send_message("✅ 垢複製パネルを設置しました。", ephemeral=True)


@tree.command(name="キャラパネル設置", description="指定キャラ系パネルを設置します")
async def chara_panel_cmd(interaction: discord.Interaction):
    if not can_use_command(interaction.user.id):
        await interaction.response.send_message("管理者のみ使用できます。", ephemeral=True)
        return
    lines = ""
    for v in CHARA_CONFIG.values():
        lines += f"{v['label']}```価格：{get_special_price(v['price_key'], v['default'], interaction.guild_id)}円```"
    embed = discord.Embed(title="指定キャラサービス", description="指定したキャラクターに対してサービスを行います。\n" + lines, color=0x00cc88)
    embed.set_footer(text="⚠️ 利用規約に違反する可能性があります。自己責任でご利用ください。")
    await interaction.channel.send(embed=embed, view=CharaPanelView(interaction.guild_id))
    await interaction.response.send_message("✅ キャラパネルを設置しました。", ephemeral=True)


@tree.command(name="値段変更", description="各サービスの値段を変更します")
async def change_price_cmd(interaction: discord.Interaction):
    if not can_use_command(interaction.user.id):
        await interaction.response.send_message("管理者のみ使用できます。", ephemeral=True)
        return
    embed = discord.Embed(title="値段変更", description="以下のセレクトから変更したいアイテムを選択してください。", color=0xffaa00)
    opts_item_a = [discord.SelectOption(label=v["label"], value=k, description=f"現在: {get_price(k, interaction.guild_id)}円") for k, v in list(ITEM_CONFIG.items())[:21]]
    opts_item_b = [discord.SelectOption(label=v["label"], value=k, description=f"現在: {get_price(k, interaction.guild_id)}円") for k, v in list(ITEM_CONFIG.items())[21:]]
    opts_special = [
        discord.SelectOption(label="垢複製",       value="__clone__",    description=f"現在: {get_special_price('__clone__', CLONE_PRICE_DEFAULT, interaction.guild_id)}円"),
        discord.SelectOption(label="代行全適応垢",  value="__full_edit__", description=f"現在: {get_special_price('__full_edit__', FULL_EDIT_PRICE_DEFAULT, interaction.guild_id)}円"),
        discord.SelectOption(label="アカウント復旧", value="__recovery__", description=f"現在: {get_special_price('__recovery__', RECOVERY_PRICE_DEFAULT, interaction.guild_id)}円"),
    ]
    for v in CHARA_CONFIG.values():
        opts_special.append(discord.SelectOption(label=v["label"], value=v["price_key"], description=f"現在: {get_special_price(v['price_key'], v['default'], interaction.guild_id)}円"))

    price_view = ui.View(timeout=180)
    ov_check = load_price_overrides(interaction.guild_id)
    all_free_now = all(ov_check.get(k, 99) == 0 for k in ITEM_CONFIG.keys())

    def make_price_select(opts, ph, row_num):
        class PS(ui.Select):
            def __init__(self_sel):
                super().__init__(placeholder=ph, min_values=1, max_values=1, options=opts, row=row_num)
            async def callback(self_sel, si: discord.Interaction):
                key = self_sel.values[0]
                if key in ITEM_CONFIG:
                    lbl = ITEM_CONFIG[key]["label"]
                    cur = get_price(key, interaction.guild_id)
                elif key == "__clone__":    lbl, cur = "垢複製",       get_special_price(key, CLONE_PRICE_DEFAULT, si.guild_id)
                elif key == "__full_edit__": lbl, cur = "代行全適応垢", get_special_price(key, FULL_EDIT_PRICE_DEFAULT, si.guild_id)
                elif key == "__recovery__":  lbl, cur = "アカウント復旧", get_special_price(key, RECOVERY_PRICE_DEFAULT, si.guild_id)
                else:
                    cfg = next((v for v in CHARA_CONFIG.values() if v["price_key"] == key), None)
                    lbl = cfg["label"] if cfg else key
                    cur = get_special_price(key, 50, si.guild_id)
                await si.response.send_modal(PriceEditModal(key, lbl, cur))
        return PS()

    class BulkFreeToggleButton(ui.Button):
        def __init__(self_btn, is_free: bool):
            label = "🔓 一括無料 OFF にする（元の値段に戻す）" if is_free else "🆓 一括無料 ON にする（全部0円）"
            style = discord.ButtonStyle.danger if is_free else discord.ButtonStyle.green
            super().__init__(label=label, style=style, row=3)
            self_btn.is_free = is_free
        async def callback(self_btn, bi: discord.Interaction):
            ov = load_price_overrides(bi.guild_id)
            if self_btn.is_free:
                for k in ITEM_CONFIG.keys():
                    ov.pop(k, None)
                for special_key in ["__clone__", "__full_edit__", "__recovery__"]:
                    ov.pop(special_key, None)
                for v in CHARA_CONFIG.values():
                    ov.pop(v["price_key"], None)
                save_price_overrides(bi.guild_id, ov)
                await bi.response.send_message(embed=discord.Embed(title="✅ 一括無料 OFF", description="全アイテムを元の値段に戻しました。", color=0xff9900), ephemeral=True)
            else:
                for k in ITEM_CONFIG.keys():
                    ov[k] = 0
                for special_key in ["__clone__", "__full_edit__", "__recovery__"]:
                    ov[special_key] = 0
                for v in CHARA_CONFIG.values():
                    ov[v["price_key"]] = 0
                save_price_overrides(bi.guild_id, ov)
                await bi.response.send_message(embed=discord.Embed(title="✅ 一括無料 ON", description="全アイテムを **0円** にしました。", color=0x00cc88), ephemeral=True)

    price_view.add_item(make_price_select(opts_item_a, "① 自販機アイテム（前半）", 0))
    price_view.add_item(make_price_select(opts_item_b, "② 自販機アイテム（後半）", 1))
    price_view.add_item(make_price_select(opts_special, "③ 垢サービス・指定キャラ", 2))
    price_view.add_item(BulkFreeToggleButton(all_free_now))
    await interaction.response.send_message(embed=embed, view=price_view, ephemeral=True)


class PriceEditModal(ui.Modal, title="値段を変更"):
    def __init__(self, key: str, label: str, current_price: int):
        super().__init__(timeout=300)
        self.key = key
        self.item_label = label
        self.new_price_input = ui.TextInput(label=f"{label} の新しい値段（円）", placeholder=f"現在: {current_price}円　※数字のみ入力", required=True, max_length=10)
        self.add_item(self.new_price_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            new_price = int(self.new_price_input.value.strip())
            if new_price < 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ 0以上の整数を入力してください。", ephemeral=True)
            return
        overrides = load_price_overrides(interaction.guild_id)
        overrides[self.key] = new_price
        save_price_overrides(interaction.guild_id, overrides)
        await interaction.response.send_message(embed=discord.Embed(title="✅ 値段変更完了", description=f"**{self.item_label}** → **{new_price}円**\nパネルを再設置すると反映されます。", color=0x00cc88), ephemeral=True)
        logger.info(f"値段変更: {self.item_label}({self.key}) → {new_price}円 by {interaction.user}")


@tree.command(name="デバッグ属性確認", description="セーブデータの属性を確認（管理者専用）")
@app_commands.describe(t_code="引き継ぎコード", a_code="認証番号", keyword="調べたいキーワード")
async def debug_attrs_cmd(interaction: discord.Interaction, t_code: str, a_code: str, keyword: str = ""):
    if not can_use_command(interaction.user.id):
        await interaction.response.send_message("管理者のみ使用可能", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    loop = asyncio.get_event_loop()
    server_handler, err = await loop.run_in_executor(None, functools.partial(run_bcsfe_download, t_code, a_code, "jp"))
    if server_handler is None:
        await interaction.followup.send(f"DL失敗: {err}", ephemeral=True); return
    sf = server_handler.save_file
    attrs = [a for a in dir(sf) if not a.startswith("_")]
    if keyword:
        attrs = [a for a in attrs if keyword.lower() in a.lower()]
    lines = []
    for a in attrs[:80]:
        try:
            v = getattr(sf, a)
            t = type(v).__name__
            extra = f"[{len(v)}]" if hasattr(v, "__len__") and not isinstance(v, str) else ""
            lines.append(f"`{a}`: {t}{extra}")
        except: pass
    text = "\n".join(lines) or "該当なし"
    for chunk in [text[i:i+1900] for i in range(0, len(text), 1900)]:
        await interaction.followup.send(chunk, ephemeral=True)


@tree.command(name="お知らせチャンネル設置", description="お知らせを投稿するチャンネルを設定します（管理者専用）")
async def set_announce_channel(interaction: discord.Interaction):
    if not can_use_command(interaction.user.id):
        await interaction.response.send_message("管理者のみ使用できます。", ephemeral=True)
        return
    settings = load_settings(interaction.guild_id)
    settings["announce_channel_id"] = str(interaction.channel_id)
    save_settings(interaction.guild_id, settings)
    await interaction.response.send_message(
        f"✅ このチャンネル ({interaction.channel.mention}) をお知らせチャンネルに設定しました。",
        ephemeral=True
    )


@tree.command(name="お知らせ", description="指定チャンネルにお知らせを投稿します（管理者専用）")
@app_commands.describe(
    タイトル="お知らせのタイトル",
    内容="お知らせの本文",
    種類="お知らせの種類（通常 / 重要 / メンテナンス / 新サービス）",
    全員メンション="@everyoneをつけるか（デフォルト: OFF）"
)
@app_commands.choices(種類=[
    app_commands.Choice(name="📢 通常", value="normal"),
    app_commands.Choice(name="🔴 重要", value="important"),
    app_commands.Choice(name="🔧 メンテナンス", value="maintenance"),
    app_commands.Choice(name="✨ 新サービス", value="new_service"),
    app_commands.Choice(name="💰 値段変更", value="price_change"),
])
async def announce_cmd(
    interaction: discord.Interaction,
    タイトル: str,
    内容: str,
    種類: str = "normal",
    全員メンション: bool = False,
):
    if not can_use_command(interaction.user.id):
        await interaction.response.send_message("管理者のみ使用できます。", ephemeral=True)
        return

    settings = load_settings(interaction.guild_id)
    ch_id = settings.get("announce_channel_id")
    if not ch_id:
        await interaction.response.send_message(
            "❌ お知らせチャンネルが設定されていません。\n`/お知らせチャンネル設置` を先に実行してください。",
            ephemeral=True
        )
        return

    ch = interaction.guild.get_channel(int(ch_id))
    if ch is None:
        await interaction.response.send_message("❌ チャンネルが見つかりません。再度設定してください。", ephemeral=True)
        return

    color_map = {
        "normal":       0x5865F2,
        "important":    0xff3333,
        "maintenance":  0xffaa00,
        "new_service":  0x00cc88,
        "price_change": 0xf5a623,
    }
    prefix_map = {
        "normal":       "📢 お知らせ",
        "important":    "🔴 重要なお知らせ",
        "maintenance":  "🔧 メンテナンス情報",
        "new_service":  "✨ 新サービス追加",
        "price_change": "💰 値段変更のお知らせ",
    }

    import datetime
    embed = discord.Embed(
        title=f"{prefix_map.get(種類, '📢 お知らせ')} — {タイトル}",
        description=内容,
        color=color_map.get(種類, 0x5865F2),
        timestamp=datetime.datetime.now()
    )
    embed.set_footer(text=f"Yu bot | {interaction.user.display_name}")
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)

    content = "@everyone" if 全員メンション else ""
    await ch.send(content=content, embed=embed)
    await interaction.response.send_message(
        f"✅ {ch.mention} にお知らせを投稿しました。",
        ephemeral=True
    )
    logger.info(f"[お知らせ] {interaction.user} → #{ch.name} [{種類}] {タイトル}")


@tree.command(name="売上確認", description="本日の売上・注文数・サービス別内訳を表示します（管理者専用）")
@app_commands.describe(days="集計対象日数（デフォルト: 1日）")
async def revenue_cmd(interaction: discord.Interaction, days: int = 1):
    if not can_use_command(interaction.user.id):
        await interaction.response.send_message("管理者のみ使用できます。", ephemeral=True)
        return

    import datetime
    await interaction.response.defer(ephemeral=True)

    all_log: list = []
    if os.path.exists(ORDER_LOG_FILE):
        try:
            with open(ORDER_LOG_FILE, "r", encoding="utf-8") as f:
                all_log = json.load(f)
        except json.JSONDecodeError:
            all_log = []

    days = max(1, min(days, 30))
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    period = [e for e in all_log if datetime.datetime.fromisoformat(e["timestamp"]) > cutoff]
    success = [e for e in period if e["status"] == "SUCCESS"]
    paid    = [e for e in period if e["status"] == "PAID"]
    failed  = [e for e in period if e["status"] not in ("SUCCESS", "PAID", "FREE")]
    free    = [e for e in period if e["status"] == "FREE"]

    total_revenue = sum(e.get("amount", 0) for e in success)
    total_orders  = len(success) + len(free)

    service_counts: dict[str, dict] = {}
    for e in success + free:
        for item in e.get("items", []):
            label = item.split("[")[0].strip()
            if label not in service_counts:
                service_counts[label] = {"count": 0, "revenue": 0}
            service_counts[label]["count"] += 1
            service_counts[label]["revenue"] += e.get("amount", 0)

    top_services = sorted(service_counts.items(), key=lambda x: x[1]["revenue"], reverse=True)[:10]

    period_label = "本日" if days == 1 else f"直近{days}日間"
    embed = discord.Embed(
        title=f"📊 売上確認 — {period_label}",
        color=0x00cc88,
        timestamp=datetime.datetime.now()
    )
    embed.add_field(
        name="💰 売上合計",
        value=f"**{total_revenue:,}円**",
        inline=True
    )
    embed.add_field(
        name="📦 完了注文数",
        value=f"**{total_orders}件** （有料{len(success)} / 無料{len(free)}）",
        inline=True
    )
    embed.add_field(
        name="⚠️ 失敗・エラー",
        value=f"{len(failed)}件",
        inline=True
    )

    if top_services:
        breakdown_lines = []
        for label, data in top_services:
            breakdown_lines.append(f"`{label[:20]}` — {data['count']}件 / {data['revenue']:,}円")
        embed.add_field(
            name="🏆 サービス別内訳（売上上位）",
            value="\n".join(breakdown_lines),
            inline=False
        )
    else:
        embed.add_field(name="🏆 サービス別内訳", value="データなし", inline=False)

    if success:
        hourly: dict[int, int] = {}
        for e in success:
            hour = datetime.datetime.fromisoformat(e["timestamp"]).hour
            hourly[hour] = hourly.get(hour, 0) + e.get("amount", 0)
        peak_hour, peak_amount = max(hourly.items(), key=lambda x: x[1])
        embed.add_field(
            name="⏰ ピーク時間帯",
            value=f"{peak_hour:02d}:00 — {peak_amount:,}円",
            inline=True
        )
        avg = total_revenue // len(success) if success else 0
        embed.add_field(name="📈 平均単価", value=f"{avg:,}円", inline=True)

    embed.set_footer(text=f"集計期間: 直近{days}日間 | 全履歴: {len(all_log)}件")
    await interaction.followup.send(embed=embed, ephemeral=True)


@tree.command(name="許可ユーザー追加", description="【管理者】ユーザーをサービス利用許可リストに追加します")
@app_commands.describe(user="追加するユーザー")
async def add_allowed_user(interaction: discord.Interaction, user: discord.Member):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message(embed=discord.Embed(title="❌ 権限エラー", description="このコマンドは管理者のみ使用できます。", color=0xff3333), ephemeral=True)
        return
    users = load_allowed_users()
    uid = str(user.id)
    if uid in users:
        await interaction.response.send_message(
            embed=discord.Embed(title="⚠️ 既に登録済み", description=f"{user.mention} はすでに許可リストに入っています。", color=0xffaa00),
            ephemeral=True
        )
        return
    users.append(uid)
    save_allowed_users(users)
    logger.info(f"[許可ユーザー追加] {user} (ID: {uid}) を追加 by {interaction.user}")
    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ 許可ユーザー追加完了",
            description=f"{user.mention} を許可リストに追加しました。\n現在の許可ユーザー数: **{len(users)}人**",
            color=0x00cc88
        ),
        ephemeral=True
    )


@tree.command(name="許可ユーザー削除", description="【管理者】ユーザーをサービス利用許可リストから削除します")
@app_commands.describe(user="削除するユーザー")
async def remove_allowed_user(interaction: discord.Interaction, user: discord.Member):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message(embed=discord.Embed(title="❌ 権限エラー", description="このコマンドは管理者のみ使用できます。", color=0xff3333), ephemeral=True)
        return
    users = load_allowed_users()
    uid = str(user.id)
    if uid not in users:
        await interaction.response.send_message(
            embed=discord.Embed(title="⚠️ 未登録", description=f"{user.mention} は許可リストに入っていません。", color=0xffaa00),
            ephemeral=True
        )
        return
    users.remove(uid)
    save_allowed_users(users)
    logger.info(f"[許可ユーザー削除] {user} (ID: {uid}) を削除 by {interaction.user}")
    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ 許可ユーザー削除完了",
            description=f"{user.mention} を許可リストから削除しました。\n現在の許可ユーザー数: **{len(users)}人**",
            color=0x00cc88
        ),
        ephemeral=True
    )


@tree.command(name="無料ユーザー設定", description="【管理者】ユーザーを無料利用リストに追加します")
@app_commands.describe(user="無料設定するユーザー")
async def add_free_user(interaction: discord.Interaction, user: discord.Member):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message(embed=discord.Embed(title="❌ 権限エラー", description="このコマンドは管理者のみ使用できます。", color=0xff3333), ephemeral=True)
        return
    users = load_free_users()
    uid = str(user.id)
    if uid in users:
        await interaction.response.send_message(
            embed=discord.Embed(title="⚠️ 既に登録済み", description=f"{user.mention} はすでに無料ユーザーリストに入っています。", color=0xffaa00),
            ephemeral=True
        )
        return
    users.append(uid)
    save_free_users(users)
    logger.info(f"[無料ユーザー設定] {user} (ID: {uid}) を追加 by {interaction.user}")
    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ 無料ユーザー設定完了",
            description=f"{user.mention} を無料ユーザーリストに追加しました。\n現在の無料ユーザー数: **{len(users)}人**",
            color=0x00cc88
        ),
        ephemeral=True
    )


@tree.command(name="無料ユーザー解除", description="【管理者】ユーザーを無料利用リストから削除します")
@app_commands.describe(user="無料設定を解除するユーザー")
async def remove_free_user(interaction: discord.Interaction, user: discord.Member):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message(embed=discord.Embed(title="❌ 権限エラー", description="このコマンドは管理者のみ使用できます。", color=0xff3333), ephemeral=True)
        return
    users = load_free_users()
    uid = str(user.id)
    if uid not in users:
        await interaction.response.send_message(
            embed=discord.Embed(title="⚠️ 未登録", description=f"{user.mention} は無料ユーザーリストに入っていません。", color=0xffaa00),
            ephemeral=True
        )
        return
    users.remove(uid)
    save_free_users(users)
    logger.info(f"[無料ユーザー解除] {user} (ID: {uid}) を削除 by {interaction.user}")
    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ 無料ユーザー解除完了",
            description=f"{user.mention} を無料ユーザーリストから削除しました。\n現在の無料ユーザー数: **{len(users)}人**",
            color=0x00cc88
        ),
        ephemeral=True
    )


@tree.command(name="ホームサーバー設定", description="【管理者】このサーバーをホームサーバーに設定します（許可ユーザー利用不可）")
async def set_home_guild(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message(
            embed=discord.Embed(title="❌ 権限エラー", description="このコマンドは管理者のみ使用できます。", color=0xff3333),
            ephemeral=True
        )
        return
    if interaction.guild is None:
        await interaction.response.send_message(
            embed=discord.Embed(title="⚠️ エラー", description="サーバー内で実行してください。", color=0xffaa00),
            ephemeral=True
        )
        return
    current = load_home_guild()
    sid = str(interaction.guild_id)

    if current == sid:
        # 解除
        save_home_guild(None)
        logger.info(f"[ホームサーバー解除] {interaction.guild.name} (ID: {sid}) by {interaction.user}")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ ホームサーバー解除",
                description=f"**{interaction.guild.name}** のホームサーバー設定を解除しました。\n許可ユーザーも通常通り利用できるようになります。",
                color=0xffaa00
            ),
            ephemeral=True
        )
    else:
        save_home_guild(sid)
        logger.info(f"[ホームサーバー設定] {interaction.guild.name} (ID: {sid}) by {interaction.user}")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ ホームサーバー設定完了",
                description=f"**{interaction.guild.name}** をホームサーバーに設定しました。\n管理者以外（許可ユーザー含む）はこのサーバーでBotを利用できなくなります。\n\n解除するには再度 `/ホームサーバー設定` を実行してください。",
                color=0x00cc88
            ),
            ephemeral=True
        )


@tree.command(name="許可サーバー追加", description="【管理者】サーバーIDを入力してBotの使用を許可します")
@app_commands.describe(server_id="許可するサーバーのID（数字）")
async def add_allowed_guild(interaction: discord.Interaction, server_id: str):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message(
            embed=discord.Embed(title="❌ 権限エラー", description="このコマンドは管理者のみ使用できます。", color=0xff3333),
            ephemeral=True
        )
        return
    if not server_id.strip().isdigit():
        await interaction.response.send_message(
            embed=discord.Embed(title="⚠️ 入力エラー", description="サーバーIDは数字のみ入力してください。", color=0xffaa00),
            ephemeral=True
        )
        return
    sid = server_id.strip()
    guilds = load_allowed_guilds()
    if sid in guilds:
        await interaction.response.send_message(
            embed=discord.Embed(title="⚠️ 既に登録済み", description=f"サーバーID `{sid}` はすでに許可リストに入っています。", color=0xffaa00),
            ephemeral=True
        )
        return
    guilds.append(sid)
    save_allowed_guilds(guilds)
    guild_obj = bot.get_guild(int(sid))
    guild_name = guild_obj.name if guild_obj else "（サーバー名不明）"
    logger.info(f"[許可サーバー追加] ID: {sid} ({guild_name}) by {interaction.user}")
    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ 許可サーバー追加完了",
            description=f"サーバー `{guild_name}` (ID: `{sid}`) を許可リストに追加しました。\n現在の許可サーバー数: **{len(guilds)}件**",
            color=0x00cc88
        ),
        ephemeral=True
    )


@tree.command(name="許可サーバー削除", description="【管理者】許可サーバーリストからサーバーを削除します")
async def remove_allowed_guild(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message(
            embed=discord.Embed(title="❌ 権限エラー", description="このコマンドは管理者のみ使用できます。", color=0xff3333),
            ephemeral=True
        )
        return
    guilds = load_allowed_guilds()
    if not guilds:
        await interaction.response.send_message(
            embed=discord.Embed(title="⚠️ リストが空", description="現在許可されているサーバーはありません。", color=0xffaa00),
            ephemeral=True
        )
        return
    options = []
    for sid in guilds:
        guild_obj = bot.get_guild(int(sid))
        name = guild_obj.name if guild_obj else f"ID: {sid}"
        options.append(discord.SelectOption(label=name[:100], value=sid, description=f"ID: {sid}"))

    view = ui.View(timeout=120)
    class GuildRemoveSelect(ui.Select):
        def __init__(self_sel):
            super().__init__(
                placeholder="削除するサーバーを選択...",
                min_values=1,
                max_values=min(len(options), 5),
                options=options[:25]
            )
        async def callback(self_sel, si: discord.Interaction):
            current = load_allowed_guilds()
            removed = []
            for sid in self_sel.values:
                if sid in current:
                    current.remove(sid)
                    guild_obj = bot.get_guild(int(sid))
                    removed.append(guild_obj.name if guild_obj else f"ID: {sid}")
            save_allowed_guilds(current)
            logger.info(f"[許可サーバー削除] {self_sel.values} by {si.user}")
            desc = "\n".join(f"• {n}" for n in removed)
            await si.response.send_message(
                embed=discord.Embed(
                    title="✅ 許可サーバー削除完了",
                    description=f"以下のサーバーを許可リストから削除しました:\n{desc}\n\n残り: **{len(current)}件**",
                    color=0x00cc88
                ),
                ephemeral=True
            )
    view.add_item(GuildRemoveSelect())
    await interaction.response.send_message(
        embed=discord.Embed(
            title="🗑️ 許可サーバー削除",
            description=f"削除するサーバーを選択してください（最大5件同時選択可）\n現在の許可サーバー数: **{len(guilds)}件**",
            color=0xffaa00
        ),
        view=view,
        ephemeral=True
    )


@tree.command(name="許可ユーザー一覧", description="【管理者】現在の許可ユーザーリストを表示します")
async def list_allowed_users(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message(
            embed=discord.Embed(title="❌ 権限エラー", description="このコマンドは管理者のみ使用できます。", color=0xff3333),
            ephemeral=True
        )
        return
    users = load_allowed_users()
    if not users:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="👥 許可ユーザー一覧",
                description="現在許可ユーザーは登録されていません。\n`/許可ユーザー追加` でユーザーを追加できます。",
                color=0xffaa00
            ),
            ephemeral=True
        )
        return
    lines = []
    for i, uid in enumerate(users, 1):
        member = interaction.guild.get_member(int(uid)) if interaction.guild else None
        name = f"{member.display_name} (@{member.name})" if member else f"ID: {uid}"
        lines.append(f"`{i}.` {name}")
    embed = discord.Embed(
        title="👥 許可ユーザー一覧",
        description="\n".join(lines),
        color=0x5865F2
    )
    embed.set_footer(text=f"合計 {len(users)} 人")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="無料ユーザー一覧", description="【管理者】現在の無料ユーザーリストを表示します")
async def list_free_users(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message(
            embed=discord.Embed(title="❌ 権限エラー", description="このコマンドは管理者のみ使用できます。", color=0xff3333),
            ephemeral=True
        )
        return
    users = load_free_users()
    if not users:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="💚 無料ユーザー一覧",
                description="現在無料ユーザーは登録されていません。\n`/無料ユーザー設定` でユーザーを追加できます。",
                color=0xffaa00
            ),
            ephemeral=True
        )
        return
    lines = []
    for i, uid in enumerate(users, 1):
        member = interaction.guild.get_member(int(uid)) if interaction.guild else None
        name = f"{member.display_name} (@{member.name})" if member else f"ID: {uid}"
        lines.append(f"`{i}.` {name}")
    embed = discord.Embed(
        title="💚 無料ユーザー一覧",
        description="\n".join(lines),
        color=0x00cc88
    )
    embed.set_footer(text=f"合計 {len(users)} 人")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="許可ユーザーリセット", description="【管理者】許可ユーザーリストを全員削除してリセットします")
async def reset_allowed_users(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message(
            embed=discord.Embed(title="❌ 権限エラー", description="このコマンドは管理者のみ使用できます。", color=0xff3333),
            ephemeral=True
        )
        return
    users = load_allowed_users()
    count = len(users)
    if count == 0:
        await interaction.response.send_message(
            embed=discord.Embed(title="⚠️ リストが空", description="現在許可ユーザーは登録されていません。", color=0xffaa00),
            ephemeral=True
        )
        return

    confirm_view = ui.View(timeout=60)

    class ConfirmReset(ui.Button):
        def __init__(self_btn):
            super().__init__(label="✅ リセットする", style=discord.ButtonStyle.danger)
        async def callback(self_btn, bi: discord.Interaction):
            save_allowed_users([])
            logger.info(f"[許可ユーザーリセット] {count}人を削除 by {bi.user}")
            await bi.response.edit_message(
                embed=discord.Embed(
                    title="✅ リセット完了",
                    description=f"許可ユーザー **{count}人** を全員削除しました。",
                    color=0x00cc88
                ),
                view=None
            )

    class CancelReset(ui.Button):
        def __init__(self_btn):
            super().__init__(label="キャンセル", style=discord.ButtonStyle.secondary)
        async def callback(self_btn, bi: discord.Interaction):
            await bi.response.edit_message(
                embed=discord.Embed(title="キャンセル", description="リセットをキャンセルしました。", color=0x888888),
                view=None
            )

    confirm_view.add_item(ConfirmReset())
    confirm_view.add_item(CancelReset())
    await interaction.response.send_message(
        embed=discord.Embed(
            title="⚠️ 許可ユーザーリセット確認",
            description=f"現在の許可ユーザー **{count}人** を全員削除します。\nこの操作は取り消せません。本当にリセットしますか？",
            color=0xff9900
        ),
        view=confirm_view,
        ephemeral=True
    )


@tree.command(name="許可サーバー一覧", description="【管理者】現在許可されているサーバーの一覧を表示します")
async def list_allowed_guilds(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message(
            embed=discord.Embed(title="❌ 権限エラー", description="このコマンドは管理者のみ使用できます。", color=0xff3333),
            ephemeral=True
        )
        return
    guilds = load_allowed_guilds()
    if not guilds:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🏠 許可サーバー一覧",
                description="現在許可されているサーバーはありません。\n`/許可サーバー追加` でサーバーIDを登録してください。",
                color=0xffaa00
            ),
            ephemeral=True
        )
        return
    lines = []
    for i, sid in enumerate(guilds, 1):
        guild_obj = bot.get_guild(int(sid))
        name = guild_obj.name if guild_obj else "（サーバー名不明）"
        lines.append(f"`{i}.` **{name}**\nID: `{sid}`")
    embed = discord.Embed(
        title="🏠 許可サーバー一覧",
        description="\n\n".join(lines),
        color=0x5865F2
    )
    embed.set_footer(text=f"合計 {len(guilds)} サーバー")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="proxy確認", description="現在のPayPayプロキシ設定を確認します（管理者専用）")
async def proxy_check_cmd(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message(
            embed=discord.Embed(title="❌ 権限エラー", description="このコマンドは管理者のみ使用できます。", color=0xff3333),
            ephemeral=True
        )
        return

    import os as _os
    raw = _os.environ.get("PAYPAY_PROXY", None)

    if not raw:
        embed = discord.Embed(
            title="🔌 プロキシ設定",
            description="現在プロキシは**未設定**です。\nPayPayリクエストは直接送信されます。",
            color=0xffaa00
        )
    else:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(raw)
            if parsed.password:
                masked = raw.replace(parsed.password, "****")
            else:
                masked = raw
        except Exception:
            masked = raw[:8] + "****"

        embed = discord.Embed(
            title="🔌 プロキシ設定",
            color=0x00cc88
        )
        embed.add_field(name="ステータス", value="✅ 有効", inline=True)
        embed.add_field(name="プロキシURL", value=f"`{masked}`", inline=False)
        embed.set_footer(text="変更するには Secrets タブで PAYPAY_PROXY を更新しボットを再起動してください。")

    await interaction.response.send_message(embed=embed, ephemeral=True)


if __name__ == "__main__":
    if not BOT_TOKEN:
        print("エラー: BOT_TOKEN 環境変数が設定されていません。")
        print("Replit の Secrets タブで BOT_TOKEN を設定してください。")
        sys.exit(1)
    if not ADMIN_IDS:
        print("エラー: ADMIN_IDS 環境変数が設定されていません。")
        print("Replit の Secrets タブで ADMIN_IDS に自分の Discord ID を設定してください。")
        sys.exit(1)
    logger.info("Bot起動中...")
    bot.run(BOT_TOKEN)
