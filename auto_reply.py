# -*- coding: utf-8 -*-
import os
import requests
from requests_oauthlib import OAuth1
from google import genai
from google.genai import types

# =========================
# 各種キー・トークン（環境変数）
# =========================
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
CONSUMER_KEY          = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET       = os.environ["CONSUMER_SECRET"]
ACCESS_TOKEN          = os.environ["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET   = os.environ["ACCESS_TOKEN_SECRET"]

auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# =========================
# 自分のユーザーID取得
# =========================
def get_my_user_id() -> str:
    url = "https://api.twitter.com/2/users/me"
    resp = requests.get(url, auth=auth)
    if resp.status_code == 200 and "data" in resp.json():
        return resp.json()["data"]["id"]
    print("ユーザーID取得失敗:", resp.status_code, resp.text)
    return ""

# =========================
# ホームタイムライン取得（除外付き）
# =========================
def get_home_timeline_filtered(user_id: str, count: int = 50) -> tuple[list, dict]:
    """
    リツイート / 返信 を API 側で除外指定しつつ（できるだけ）取得。
    includes.media も展開して画像URL取得できるようにする。
    """
    url = f"https://api.twitter.com/2/users/{user_id}/timelines/reverse_chronological"
    params = {
        "max_results": count,
        "exclude": "retweets,replies",
        "tweet.fields": "public_metrics,attachments,text,referenced_tweets",
        "expansions": "attachments.media_keys",
        "media.fields": "url,type"
    }
    r = requests.get(url, params=params, auth=auth)
    if r.status_code != 200:
        print("タイムライン取得失敗:", r.status_code, r.text)
        return [], {}

    data = r.json()
    tweets = data.get("data", [])
    media_entries = data.get("includes", {}).get("media", [])
    media_map = {m["media_key"]: m for m in media_entries}

    # API の除外指定だけでは混ざる場合があるので念のためフィルタ
    clean = []
    for t in tweets:
        refs = t.get("referenced_tweets", [])
        # リツイート / 返信 / 引用 を除外
        if any(r["type"] in ["retweeted", "replied_to", "quoted"] for r in refs):
            continue
        clean.append(t)
    return clean, media_map

# =========================
# 返信対象を選ぶ
# =========================
def pick_best_tweet(tweets: list) -> dict | None:
    if not tweets:
        return None
    # reply_count が最大のツイートを選ぶ
    return max(tweets, key=lambda x: x.get("public_metrics", {}).get("reply_count", 0))

# =========================
# Gemini で返信生成
# =========================
def generate_reply(tweet_text: str, media_urls: list[str]) -> str:
    """
    Gemini で「そのツイートに対して自然な返信」を生成するプロンプト。
    今の自動ツイートの書き方と同じ流れ・形式で。
    """
    # プロンプト組み立て
    prompt = (
        "以下のツイート内容に対して、"
        "不適切な内容を除外しつつ自然で丁寧な返信文を日本語で140文字以内のツイート文を1つ生成してください。\n"
        "必要なら画像URLも考慮してください。\n\n"
        f"ツイート本文:\n{tweet_text}\n"
    )
    if media_urls:
        prompt += "\n画像URL:\n"
        for url in media_urls:
            prompt += f"- {url}\n"
    prompt += "\n返信文:"

    # Gemini API 呼び出し
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=150),
    )

    # レスポンス整形
    text = (response.text or "").strip()

    # 短すぎる場合は「スキップ」
    if len(text) < 10:
        print("返信文が短すぎるのでスキップ〜")
        return ""
    return text

# =========================
# X / Twitter 投稿（返信）
# =========================
def post_reply(reply_text: str, reply_to_id: str) -> bool:
    """
    POST /2/tweets で reply を投稿する形。
    Gemini 生成と同じ構造なので、既存の投稿方法と同じスタイルです。
    """
    url = "https://api.twitter.com/2/tweets"
    payload = {
        "text": reply_text,
        "reply": {"in_reply_to_tweet_id": reply_to_id}
    }
    resp = requests.post(url, json=payload, auth=auth)
    if resp.status_code == 201:
        print("返信投稿成功！")
        return True
    print("返信失敗:", resp.status_code, resp.text)
    return False

# =========================
# Main
# =========================
def main():
    user_id = get_my_user_id()
    if not user_id:
        return

    tweets, media_map = get_home_timeline_filtered(user_id)
    print("対象候補数:", len(tweets))
    
    target = pick_best_tweet(tweets)
    if not target:
        print("返信対象なし〜")
        return

    tweet_id = target["id"]
    text = target["text"]
    print("返信対象:", text)

    # 画像URL抽出
    media_urls = []
    if target.get("attachments"):
        for key in target["attachments"].get("media_keys", []):
            m = media_map.get(key)
            if m and "url" in m:
                media_urls.append(m["url"])

    # Gemini 返信生成
    reply = generate_reply(text, media_urls)
    if not reply:
        return  # フォールバックは投稿しない

    print("生成返信:", reply)
    post_reply(reply, tweet_id)

if __name__ == "__main__":
    main()
