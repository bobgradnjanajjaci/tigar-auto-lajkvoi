import requests
from comment_finder import find_target_comment
from like_rules import calculate_target_likes

API_KEY = "44358011a5438dfc856eebc5ca4928ee"
PANEL_URL = "https://justanotherpanel.com/api/v2"
SERVICE_ID = 9998

def process_video(video_url: str):
    result = find_target_comment(video_url)

    if not result.get("found"):
        return {"status": "error", "message": "Komentar nije pronađen"}

    target = calculate_target_likes(result["top_likes"])
    if target == 0:
        return {"status": "skip", "message": "Top komentar prejak – skip"}

    my_likes = int(result.get("my_likes") or 0)
    to_send = max(0, target - my_likes)

    if to_send <= 0:
        return {"status": "ok", "message": "Dovoljno lajkova"}

    payload = {
    "key": API_KEY,
    "action": "add",
    "service": SERVICE_ID,
    "link": result["comment_link"],
    "quantity": to_send,
    "username": result["username"]  # 👈 KLJUČNO
}


    try:
        r = requests.post(PANEL_URL, data=payload, timeout=25)
        return {
            "status": "sent",
            "comment_link": result["comment_link"],
            "likes_sent": to_send,
            "response": r.text[:300]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Panel request failed: {e}"
        }

