import json
import os
import sys
from datetime import datetime

QUEUE_THRESHOLD = 10
GENERATE_COUNT = 20

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


def main():
    queue = load_json(QUEUE_PATH)

    if len(queue) >= QUEUE_THRESHOLD:
        print(f"[INFO] キュー残り{len(queue)}件。補充不要。")
        return

    print(f"[INFO] キュー残り{len(queue)}件。{GENERATE_COUNT}件生成します。")

    history = load_json(HISTORY_PATH)
    recent_texts = [p.get("text", "")[:60] for p in history[-30:]]
    today = datetime.now().strftime("%Y%m%d")

    prompt = f"""あなたはThreads投稿ライターです。@sessi.life というアカウントの投稿を{GENERATE_COUNT}件作ってください。

## キャラクター設定
- 穏やかでかわいらしい女の子
- 一人称は「わたし」または一人称なし
- 「僕」「俺」は絶対禁止
- 「おはよう」「おやすみ」「こんにちは」などの挨拶は禁止
- 自然な話し言葉・ひらがな多め・やわらかいトーン

## 投稿内容のルール
- 全体の8割は日常・気持ち系（カフェ、季節、好きなもの、気づき、ひとり時間など）
- 全体の2割は旅行サービス紹介（必ず末尾に #PR をつけること）
- 旅行系の内容：国内ホテルがお得に取れる・海外5つ星ホテルに無料で泊まれる仕組みがある・気になる人はDMで聞いてというスタイル
- ハッシュタグは各投稿の末尾に2〜5個
- 1投稿100〜200文字程度
- 改行を使って読みやすく

## 禁止事項
- 挨拶（おはよう・おやすみ・こんにちは・こんばんは）
- 大げさな表現・嘘の数字
- 旅行系投稿で「ネットワークビジネス」と書くこと

## 直近の投稿（重複を避けること）
{json.dumps(recent_texts, ensure_ascii=False)}

## 出力形式
JSON配列のみ出力してください。説明文・コードブロック記号は不要です。

[
  {{
    "id": "{today}_001",
    "text": "投稿本文（ハッシュタグ含む）"
  }}
]"""

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[SKIP] ANTHROPIC_API_KEY が見つかりません。スキップします。")
        sys.exit(0)

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()

    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    new_posts = json.loads(response_text)

    existing_ids = {str(p.get("id")) for p in queue + history}
    for i, post in enumerate(new_posts, 1):
        post["id"] = f"{today}_{i:03d}"
        while post["id"] in existing_ids:
            i += 1
            post["id"] = f"{today}_{i:03d}"
        existing_ids.add(post["id"])

    queue.extend(new_posts)
    save_json(QUEUE_PATH, queue)
    print(f"[OK] {len(new_posts)}件追加。キュー合計: {len(queue)}件")


if __name__ == "__main__":
    main()
