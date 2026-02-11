import re
import time
import requests

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# ✅ tražimo cijelu frazu + autora
REQUIRED_PHRASE = "encrypted money code"
AUTHOR_WORDS = ["ethan", "rothwell"]

REQUEST_TIMEOUT = 8
RETRY_COUNT = 1
RETRY_DELAY = 3

TOP_N = 50  # ✅ samo top 50

_session = requests.Session()


def normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def expand_url(url: str) -> str:
    url = (url or "").strip()
    if "/video/" in url:
        return url
    try:
        r = _session.head(url, headers=HEADERS, allow_redirects=True, timeout=REQUEST_TIMEOUT)
        return r.url or url
    except Exception:
        try:
            r = _session.get(url, headers=HEADERS, allow_redirects=True, timeout=REQUEST_TIMEOUT)
            return r.url or url
        except Exception:
            return url


def extract_video_id(url: str):
    m = re.search(r"/video/(\d+)", url)
    return m.group(1) if m else None


def fetch_top_comments(video_id: str, limit: int = 50):
    try:
        r = _session.get(
            "https://www.tiktok.com/api/comment/list/",
            headers=HEADERS,
            params={"aid": 1988, "count": min(50, limit), "cursor": 0, "aweme_id": video_id},
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        return data.get("comments") or []
    except Exception:
        return []


def build_comment_link(video_url: str, cid: str) -> str:
    base = video_url.split("?")[0]
    return f"{base}?cid={cid}"


def is_match(text_norm: str) -> bool:
    # mora fraza + (ethan ili rothwell)
    if REQUIRED_PHRASE not in text_norm:
        return False
    return any(w in text_norm for w in AUTHOR_WORDS)


def find_target_comment(video_url: str) -> dict:
    """
    ✅ Stabilna funkcija koju auto_brain_core importuje.
    Vraća PRVI match u TOP 50 (po ranku), jer kad tek pošalješ komentare svi su 0 lajkova.
    """
    video_url = expand_url(video_url)
    video_id = extract_video_id(video_url)

    if not video_id:
        return {"found": False, "reason": "no_video_id"}

    for attempt in range(RETRY_COUNT + 1):
        comments = fetch_top_comments(video_id, limit=TOP_N)
        if comments:
            top = comments[:TOP_N]
            for rank, c in enumerate(top, start=1):
                text = c.get("text") or ""
                text_norm = normalize(text)
                if not is_match(text_norm):
                    continue

                cid = c.get("cid")
                username = (c.get("user") or {}).get("unique_id")
                likes = int(c.get("digg_count") or 0)

                return {
                    "found": True,
                    "video_id": video_id,
                    "attempt": attempt + 1,
                    "rank_in_top50": rank,
                    "my_cid": cid,
                    "username": username,
                    "my_likes": likes,
                    "comment_link": build_comment_link(video_url, cid),
                    "matched_text": text,
                }

            return {"found": False, "reason": "no_match_in_top50", "video_id": video_id, "attempt": attempt + 1}

        if attempt < RETRY_COUNT:
            time.sleep(RETRY_DELAY)

    return {"found": False, "reason": "no_comments"}
