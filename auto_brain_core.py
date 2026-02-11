from comment_finder import find_target_comment
from like_rules import calculate_target_likes

# ========= PANEL CONFIG (INFO / DRY-RUN) =========
API_KEY = "bb5b7862f2b2f2f7d43bcddc35f8c15f"
PANEL_URL = "https://smmtigers.com/api/v2"
SERVICE_ID = 4564

def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


def process_video(video_url: str) -> dict:
    """
    SAFE core:
    - pronađe komentar u TOP 50 (po ranku)
    - izračuna target + koliko dodati
    - vrati payload preview + panel info
    - NE šalje request na panel
    """

    result = find_target_comment(video_url)

    # osnovni info o panelu (da uvijek vidiš gdje bi išlo)
    panel_info = {
        "panel_url": PANEL_URL,
        "service_id": SERVICE_ID,
        "api_key_masked": _mask_key(API_KEY),
        "mode": "DRY_RUN_NO_SEND"
    }

    if not result.get("found"):
        return {
            "status": "error",
            "message": "Komentar nije pronađen u TOP 50",
            "panel": panel_info,
            "details": result
        }

    top_likes = int(result.get("top_likes") or 0)
    my_likes = int(result.get("my_likes") or 0)

    target = calculate_target_likes(top_likes)
    if target == 0:
        return {
            "status": "skip",
            "message": "Top komentar prejak – skip",
            "panel": panel_info,
            "result": result,
            "top_likes": top_likes
        }

    to_send = max(0, target - my_likes)

    if to_send <= 0:
        return {
            "status": "ok",
            "message": "Dovoljno lajkova (nema potrebe slati)",
            "panel": panel_info,
            "result": result,
            "top_likes": top_likes,
            "my_likes": my_likes,
            "target_likes": target,
            "likes_to_send": 0
        }

    # ✅ payload koji bi se poslao (ti ga možeš copy/paste u svoju stranicu/panel)
    payload_preview = {
        "key": _mask_key(API_KEY),         # maskirano u outputu
        "action": "add",
        "service": SERVICE_ID,
        "link": result.get("comment_link"),
        "quantity": to_send,
        "username": result.get("username"),
    }

    return {
        "status": "ok",
        "message": "Plan izračunat. Payload pripremljen (nije poslano).",
        "panel": panel_info,
        "video_url": video_url,
        "comment_link": result.get("comment_link"),
        "username": result.get("username"),
        "rank_in_top50": result.get("rank_in_top50"),
        "matched_text": result.get("matched_text"),
        "top_likes": top_likes,
        "my_likes": my_likes,
        "target_likes": target,
        "likes_to_send": to_send,
        "payload_preview": payload_preview
    }
