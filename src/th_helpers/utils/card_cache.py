# card_cache.py
from __future__ import annotations

import io
import json
import os
import shutil
import tempfile
import threading
import zipfile
from typing import Any, Dict, List, Optional, Sequence

import requests

# ---------------- Config ----------------
CACHE_DIR = os.environ.get("POKEMON_CACHE_DIR", os.path.join(os.getcwd(), "data"))
EXTRACT_DIR = os.path.join(CACHE_DIR, "pokemon-tcg-data")   # extracted release

# Cards index (existing behavior)
INDEX_PATH = os.path.join(CACHE_DIR, "cards_by_id.json")    # flat {card_id: card_json}
# Sets index (new)
SETS_INDEX_PATH = os.path.join(CACHE_DIR, "sets_by_ptcgo.json")  # flat {PTCGO_CODE: set_json}

GH_OWNER = os.environ.get("POKEMON_GH_OWNER", "PokemonTCG")
GH_REPO = os.environ.get("POKEMON_GH_REPO", "pokemon-tcg-data")
GH_TOKEN = os.environ.get("GITHUB_TOKEN")  # optional for higher rate limits

RELEASE_TAG = os.environ.get("POKEMON_RELEASE_TAG")        # e.g. "v2.15"
FORCE_REFRESH = os.environ.get("POKEMON_FORCE_REFRESH", "0") == "1"

# ---------------- State -----------------
_lock = threading.RLock()
_loaded = False

_cards_by_id: Dict[str, Dict[str, Any]] = {}
_sets_by_ptcgo: Dict[str, Dict[str, Any]] = {}  # NEW


# ---------------- GitHub helpers --------
def _gh_headers() -> Dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "pokemon-tcg-data-client"}
    if GH_TOKEN:
        h["Authorization"] = f"Bearer {GH_TOKEN}"
    return h


def _latest_release_json() -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{GH_OWNER}/{GH_REPO}/releases/latest"
    r = requests.get(url, headers=_gh_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def _tag_release_json(tag: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{GH_OWNER}/{GH_REPO}/releases/tags/{tag}"
    r = requests.get(url, headers=_gh_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def _pick_zip_asset(rel: Dict[str, Any]) -> str:
    # Prefer a .zip asset; fall back to source zipball
    for a in rel.get("assets", []):
        name = (a.get("name") or "").lower()
        if name.endswith(".zip") and a.get("browser_download_url"):
            return a["browser_download_url"]
    if rel.get("zipball_url"):
        return rel["zipball_url"]
    raise RuntimeError("No downloadable zip asset found for this release.")


# ---------------- Disk helpers ----------
def _atomic_write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass


def _load_cards_index_from_disk() -> bool:
    if not os.path.isfile(INDEX_PATH):
        return False
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            _cards_by_id.clear()
            _cards_by_id.update(data)
            return True
    except Exception:
        return False
    return False


def _save_cards_index_to_disk() -> None:
    _atomic_write_text(INDEX_PATH, json.dumps(_cards_by_id, ensure_ascii=False))


def _load_sets_index_from_disk() -> bool:
    if not os.path.isfile(SETS_INDEX_PATH):
        return False
    try:
        with open(SETS_INDEX_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            _sets_by_ptcgo.clear()
            _sets_by_ptcgo.update(data)
            return True
    except Exception:
        return False
    return False


def _save_sets_index_to_disk() -> None:
    _atomic_write_text(SETS_INDEX_PATH, json.dumps(_sets_by_ptcgo, ensure_ascii=False))


# -------------- Extract & index ---------
def _extract_zip_to_dir(zip_bytes: bytes, target_dir: str) -> None:
    if os.path.isdir(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        zf.extractall(target_dir)


def _iter_json_files(root: str) -> List[str]:
    paths: List[str] = []
    for base, _, files in os.walk(root):
        for fn in files:
            if fn.lower().endswith(".json"):
                paths.append(os.path.join(base, fn))
    return paths


def _index_cards_from_extracted(root: str) -> Dict[str, Dict[str, Any]]:
    """
    Build a FLAT {card_id: card_json}. Handles these shapes:
      - [ {...card...}, {...card...} ]
      - { "data": [ {...card...} ] }
      - { "data": { "cards": [ {...card...} ] } }   # some set wrappers
      - { ...single-card... }  (dict with 'id')
    Ignores JSON that doesn't represent cards.
    """
    by_id: Dict[str, Dict[str, Any]] = {}

    def add_card(maybe: Any):
        if isinstance(maybe, dict) and "id" in maybe:
            by_id[str(maybe["id"])] = maybe

    for path in _iter_json_files(root):
        p_norm = path.replace("\\", "/")
        if "/cards/en/" not in p_norm:
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except Exception:
            continue

        if isinstance(obj, list):
            for item in obj:
                add_card(item)
            continue

        if isinstance(obj, dict):
            if "data" in obj:
                data = obj["data"]
                if isinstance(data, list):
                    for item in data:
                        add_card(item)
                    continue
                if isinstance(data, dict) and "cards" in data and isinstance(data["cards"], list):
                    for item in data["cards"]:
                        add_card(item)
                    continue
            if "cards" in obj and isinstance(obj["cards"], list):
                for item in obj["cards"]:
                    add_card(item)
                continue
            add_card(obj)  # last chance: single-card dict

    return by_id


def _index_sets_from_extracted(root: str) -> Dict[str, Dict[str, Any]]:
    """
    Build a FLAT {PTCGO_CODE: set_json} from /sets/en.json inside the extracted repo.
    Expected shapes:
      - [ {...set...}, ... ]
      - { "data": [ {...set...}, ... ] }
    Only entries with a non-empty 'ptcgoCode' are included.
    """
    # Find the sets/en.json file anywhere under the extracted root
    sets_path = None
    for path in _iter_json_files(root):
        p_norm = path.replace("\\", "/")
        if p_norm.endswith("/sets/en.json"):
            sets_path = path
            break
    if not sets_path:
        return {}

    try:
        with open(sets_path, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception:
        return {}

    raw_list: List[Dict[str, Any]] = []
    if isinstance(obj, list):
        raw_list = [x for x in obj if isinstance(x, dict)]
    elif isinstance(obj, dict) and "data" in obj and isinstance(obj["data"], list):
        raw_list = [x for x in obj["data"] if isinstance(x, dict)]

    by_code: Dict[str, Dict[str, Any]] = {}
    for s in raw_list:
        code = s.get("ptcgoCode")
        if isinstance(code, str) and code.strip():
            by_code[code.strip().upper()] = s
    return by_code


# ---------------- Public API ------------
def ensure_loaded(force_refresh: bool = FORCE_REFRESH) -> None:
    """
    Ensure in-memory flat indexes:
      - Cards: {card_id: card_json}
      - Sets:  {PTCGO_CODE: set_json}
    If missing (or forced), fetch the (tagged or latest) GitHub release zip and rebuild both.
    """
    global _loaded
    with _lock:
        if _loaded and not force_refresh:
            return

        if not force_refresh:
            cards_ok = _load_cards_index_from_disk()
            sets_ok = _load_sets_index_from_disk()
            if cards_ok and sets_ok:
                _loaded = True
                return

        # (Re)build from a fresh release
        rel = _tag_release_json(RELEASE_TAG) if RELEASE_TAG else _latest_release_json()
        zip_url = _pick_zip_asset(rel)
        r = requests.get(zip_url, headers=_gh_headers(), timeout=120)
        r.raise_for_status()

        _extract_zip_to_dir(r.content, EXTRACT_DIR)
        flat_cards = _index_cards_from_extracted(EXTRACT_DIR)
        flat_sets = _index_sets_from_extracted(EXTRACT_DIR)

        _cards_by_id.clear()
        _cards_by_id.update(flat_cards)
        _save_cards_index_to_disk()

        _sets_by_ptcgo.clear()
        _sets_by_ptcgo.update(flat_sets)
        _save_sets_index_to_disk()

        _loaded = True


def update_from_release(tag: Optional[str] = None) -> int:
    """
    Force-refresh from a specific tag (e.g., 'v2.15') or latest if None.
    Returns the number of cards indexed (for backward compatibility).
    Note: sets are also refreshed as part of this call.
    """
    global RELEASE_TAG
    if tag:
        RELEASE_TAG = tag
    ensure_loaded(force_refresh=True)
    return len(_cards_by_id)


# ---- Cards lookups (existing API) ----
def get_card(card_id: str) -> Optional[Dict[str, Any]]:
    ensure_loaded()
    return _cards_by_id.get(str(card_id))


def get_total_length(card_id: str) -> Optional[Dict[str, Any]]:
    ensure_loaded()
    return len(_cards_by_id.keys())


def get_cards_by_ids(ids: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    ensure_loaded()
    return {str(cid): _cards_by_id[str(cid)] for cid in ids if str(cid) in _cards_by_id}


# ---- Sets lookups ----
def get_set_by_ptcgo(code: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a set object by its PTCGO code (case-insensitive).
    """
    ensure_loaded()
    if code is None:
        return None
    # TODO build out this mapping better
    if code == 'SVP':
        code = 'PR-SV'
    return _sets_by_ptcgo.get(str(code).strip().upper())


def get_sets_by_ptcgocodes(codes: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    """
    Batch fetch set objects by PTCGO codes (case-insensitive).
    """
    ensure_loaded()
    out: Dict[str, Dict[str, Any]] = {}
    for c in codes:
        k = str(c).strip().upper()
        if k in _sets_by_ptcgo:
            out[k] = _sets_by_ptcgo[k]
    return out


def get_all_sets_map() -> Dict[str, Dict[str, Any]]:
    """
    Return the full {PTCGO_CODE: set_json} mapping.
    """
    ensure_loaded()
    return dict(_sets_by_ptcgo)


# ---------------- Local testing ----------
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Fetch & index Pokémon TCG data (flat by card_id and PTCGO sets).")
    ap.add_argument("--tag", default=None, help="Release tag to fetch (e.g., v2.15). Defaults to latest.")
    ap.add_argument("--force", action="store_true", help="Force refresh even if cached index exists.")
    ap.add_argument("--ids", nargs="*", default=[], help="Card IDs to print after loading.")
    ap.add_argument("--set-codes", nargs="*", default=[], help="PTCGO set codes to print after loading.")
    args = ap.parse_args()

    if args.force:
        FORCE_REFRESH = True

    n_cards = update_from_release(args.tag) if (args.force or args.tag) else (ensure_loaded() or len(_cards_by_id))
    print(f"Loaded {len(_cards_by_id)} cards and {len(_sets_by_ptcgo)} sets.")

    ids = args.ids or list(_cards_by_id.keys())[:5]
    for cid, card in get_cards_by_ids(ids).items():
        print(f"{cid}: {card}")

    if args.set_codes:
        sets = get_sets_by_ptcgocodes(args.set_codes)
        for code, s in sets.items():
            print(f"{code}: {s.get('name')} (id={s.get('id')})")
