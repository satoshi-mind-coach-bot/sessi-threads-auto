import json
import os
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime

QUEUE_PATH = os.path.join(os.path.dirname(__file__), "data", "post_queue.json")
HISTORY_PATH = os.path.join(os.path.dirname(__file__), "data", "post_history.json")


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_thread(token, user_id, text):
    url = f"https://graph.threads.net/v1.0/{user_id}/threads"
    params = {"media_type": "TEXT", "text": text, "access_token": token}
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))


def publish_thread(token, user_id, creation_id):
    url = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
    data = urllib.parse.urlencode({"creation_id": creation_id, "access_token": token}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))


def main():
    token = os.environ.get("THREADS_ACCESS_TOKEN")
    user_id = os.environ.get("THREADS_USER_ID")

    if not token or not user_id:
        print("[ERROR] THREADS_ACCESS_TOKEN または THREADS_USER_ID が設定されていません")
        sys.exit(1)

    queue = load_json(QUEUE_PATH)
    if not queue:
        print("[INFO] キューが空です。投稿する内容がありません。")
        sys.exit(0)

    post = queue.pop(0)
    text = post.get("text", "")
    print(f"[INFO] 投稿開始: {text[:30]}...")

    result = create_thread(token, user_id, text)
    creation_id = result["id"]
    time.sleep(3)
    published = publish_thread(token, user_id, creation_id)
    post_id = published["id"]
    print(f"[OK] 投稿完了: {post_id}")

    history = load_json(HISTORY_PATH)
    post["post_id"] = post_id
    post["posted_at"] = datetime.now().isoformat()
    history.append(post)

    save_json(QUEUE_PATH, queue)
    save_json(HISTORY_PATH, history)
    print(f"[INFO] キュー残り: {len(queue)}件")


if __name__ == "__main__":
    main()
