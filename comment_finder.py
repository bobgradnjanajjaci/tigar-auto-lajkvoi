import re
import time
import requests

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# ✅ ciljna fraza + autor (umjesto ["encrypted","money","code"])
REQUIRED_PHRASE = "encrypted money code"
AUTHOR_WORDS = ["ethan", "rothwell"]

REQUEST_TIMEOUT = 6
MAX_PAGES = 1          # ✅ Top-50 gate: jedna strana = 50 komentara
RETRY_COUNT = 1
RETRY_DELAY = 3

_session = requests.Session()

# ✅ Ako želiš NAJPOUZDANIJE: ubaci tačne komentare koje postavljaš
# (ovo je najbolji način kad svi imaju 0 lajkova)
MY_EXACT_COMMENTS = [
    "You have no idea how POWERFUL Encrypted Money Code by Ethan Rothwell is. Read it, it changed my life.",
"Just trust me, Encrypted Money Code by Ethan Rothwell is the book you NEED right now. It changed my life.",
"If you’re looking for a book that truly changes everything, Encrypted Money Code by Ethan Rothwell is it. It will change your life.",
"I can’t even explain it, book called Encrypted Money Code by Ethan Rothwell is different. You NEED this book. It changed my life.",
"I spent so much time struggling on the internet, searching for something that would change my life. All I can say is I finally found it. Encrypted Money Code by Ethan Rothwell is an absolute game-changer. This book is like nothing I've ever seen before.",
"I honestly don’t know where else to say this, but I have to share it here. I found something truly mind-blowing. The book Encrypted Money Code by Ethan Rothwell is on a whole different level, especially for anyone chasing success.",
"No more gatekeeping just go and read the book Encrypted Money Code by Ethan Rothwell and thank me later for changing your life.",
"I used to think making money online was too hard for someone who didn’t know much about it, but this book really worked for me. It’s called Encrypted Money Code by Ethan Rothwell. It helped me succeed and start making money, ngl everyone should read it.",
"Encrypted Money Code by Ethan Rothwell is the only book I’ve read that actually made me feel dangerous. Page 13 is not normal.",
"Plot twist - You seeing this comment about Encrypted Money Code by Ethan Rothwell isn't random - Nothing is.",
"I know it’s cliche to recommend books through comments and say like “it changed my life” or whatever, but I need to recommend this one: Encrypted Money Code by Ethan Rothwell, ngl Insane hidden information there.",
]

def normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

# ✅ Normalizuj listu tačnih komentara jednom (brže)
MY_EXACT_COMMENTS_NORM = {normalize(t) for t in MY_EXACT_COMMENTS if t.strip()}

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
            return r.url
        except Exception:
            return url

def extract_video_id(url: str):
    m = re.search(r"/video/(\d+)", url)
    return m.group(1) if m else None

def fetch_comments(video_id: str):
    comments = []
    cursor = 0

    for _ in range(MAX_PAGES):  # MAX_PAGES=1 -> Top 50
        try:
            r = _session.get(
                "https://www.tiktok.com/api/comment/list/",
                headers=HEADERS,
                params={"aid": 1988, "count": 50, "cursor": cursor, "aweme_id": video_id},
                timeout=REQUEST_TIMEOUT,
            )
            if r.status_code != 200:
                break

            data = r.json()
            batch = data.get("comments") or []
            comments.extend(batch)

            if not data.get("has_more"):
                break

            cursor = int(data.get("cursor") or 0)
        except Exception:
            break

    return comments

def build_comment_link(video_url: str, cid: str) -> str:
    base = video_url.split("?")[0]
    return f"{base}?cid={cid}"

def is_phrase_match(text_norm: str) -> bool:
    # ✅ mora sadržati cijelu frazu + (ethan ili rothwell)
    if REQUIRED_PHRASE not in text_norm:
        return False
    return any(w in text_norm for w in AUTHOR_WORDS)

def is_exact_my_comment(text_norm: str) -> bool:
    # ✅ najpouzdanije kad svi imaju 0 lajkova
    return text_norm in MY_EXACT_COMMENTS_NORM

def find_first_book_mention_top50(video_url: str) -> dict:
    """
    ✅ Vrati PRVI komentar u Top-50 koji spominje knjigu (po ranku),
    i posebno označi ako je to tačno tvoj komentar (exact match).
    """
    video_url = expand_url(video_url)
    video_id = extract_video_id(video_url)
    if not video_id:
        return {"found": False, "reason": "no_video_id"}

    for attempt in range(RETRY_COUNT + 1):
        comments = fetch_comments(video_id)
        if comments:
            top50 = comments[:50]

            # Tražimo "prvi" u top50
            for rank, c in enumerate(top50, start=1):
                text = c.get("text") or ""
                text_norm = normalize(text)

                if not is_phrase_match(text_norm):
                    continue

                cid = c.get("cid")
                username = (c.get("user") or {}).get("unique_id")
                likes = int(c.get("digg_count") or 0)

                return {
                    "found": True,
                    "video_id": video_id,
                    "attempt": attempt + 1,
                    "rank_in_top50": rank,          # ✅ koji je “prvi” po ranku
                    "username": username,           # ✅ koji profil
                    "likes": likes,
                    "cid": cid,
                    "comment_link": build_comment_link(video_url, cid),
                    "matched_text": text,
                    "is_exact_my_comment": is_exact_my_comment(text_norm),  # ✅ da li je jedan od tvojih tačnih komentara
                }

            return {"found": False, "reason": "no_match_in_top50", "video_id": video_id, "attempt": attempt + 1}

        if attempt < RETRY_COUNT:
            time.sleep(RETRY_DELAY)

    return {"found": False, "reason": "no_comments"}

# Ako želiš listu SVIH matchova u Top 50 (da vidiš ima li više tvojih):
def list_all_mentions_top50(video_url: str, limit: int = 10) -> dict:
    video_url = expand_url(video_url)
    video_id = extract_video_id(video_url)
    if not video_id:
        return {"ok": False, "reason": "no_video_id"}

    comments = fetch_comments(video_id)
    top50 = (comments or [])[:50]
    matches = []

    for rank, c in enumerate(top50, start=1):
        text = c.get("text") or ""
        text_norm = normalize(text)
        if not is_phrase_match(text_norm):
            continue

        cid = c.get("cid")
        username = (c.get("user") or {}).get("unique_id")
        likes = int(c.get("digg_count") or 0)

        matches.append({
            "rank_in_top50": rank,
            "username": username,
            "likes": likes,
            "cid": cid,
            "comment_link": build_comment_link(video_url, cid),
            "is_exact_my_comment": is_exact_my_comment(text_norm),
            "text": text,
        })

    return {"ok": True, "video_id": video_id, "matches": matches[:limit], "count": len(matches)}
