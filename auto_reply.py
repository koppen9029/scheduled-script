# -*- coding: utf-8 -*-
import os
import requests
from requests_oauthlib import OAuth1
from google import genai
from google.genai import types

# — 環境変数 —
GEMINI_API_KEY      = os.environ["GEMINI_API_KEY"]
CONSUMER_KEY        = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET     = os.environ["CONSUMER_SECRET"]
ACCESS_TOKEN        = os.environ["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = os.environ["ACCESS_TOKEN_SECRET"]

auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# — ① 自分のユーザーIDを取得 —
def get_my_user_id():
    url = "https://api.twitter.com/2/users/me"
    r = requests.get(url, auth=auth)
    if r.status_code == 200 and "data" in r.json():
        return r.json()["data"]["id"]
    print("ユーザーID取得失敗:", r.status_code, r.text)
    return ""

# — ② タイムライン取得（画像URL含む） —
def get_timeline_with_media(user_id, count=50):
    url = f"https://api.twitter.com/2/users/{user_id}/timelines/reverse_chronological"
    params = {
        "max_results": count,
        "tweet.fields": "public_metrics,conversation_id,attachments,text",
        "expansions": "attachments.media_keys",
        "media.fields": "url,type"
    }
    r = requests.get(url, params=params, auth=auth)
    if r.status_code != 200:
        print("タイムライン取得失敗:", r.status_code, r.text)
        return [], {}
    data = r.json()
    tweets = data.get("data", [])
    media_list = data.get("includes", {}).get("media", [])
    media_map = {m["media_key"]: m for m in media_list}
    return tweets, media_map

# — 返信数が最大のツイートを探す —
def pick_best_tweet(tweets):
    if not tweets:
        return None
    return max(tweets, key=lambda x: x.get("public_metrics", {}).get("reply_count", 0))

# — Gemini 返信生成 —
def generate_reply(tweet_text: str, media_urls: list[str]) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = "以下のツイートと画像から自然で丁寧な返信を考えて下さい:\n"
    prompt += f"ツイート本文: {tweet_text}\n"
    if media_urls:
        prompt += "関連画像URL:\n"
        for url in media_urls:
            prompt += f"{url}\n"
    prompt += "\n返信:"

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=120),
    )
    text = (response.text or "").strip()
    # フォールバック: 返信スキップ
    if len(text) < 10:
        print("返信生成が短すぎるのでスキップ〜")
        return ""
    return text

# — 返信投稿 —
def post_reply(reply_text: str, reply_to_id: str) -> bool:
    url = "https://api.twitter.com/2/tweets"
    payload = {
        "text": reply_text,
        "reply": {"in_reply_to_tweet_id": reply_to_id}
    }
    r = requests.post(url, json=payload, auth=auth)
    if r.status_code == 201:
        print("返信投稿成功！")
        return True
    print("返信失敗:", r.status_code, r.text)
    return False

# — 実行 —
def main():
    user_id = get_my_user_id()
    if not user_id:
        return

    tweets, media_map = get_timeline_with_media(user_id)
    best = pick_best_tweet(tweets)
    if not best:
        print("返信対象なし〜")
        return

    tweet_id = best["id"]
    text = best["text"]
    print("対象:", text)

    # 画像URL抽出
    media_urls = []
    if best.get("attachments"):
        for key in best["attachments"].get("media_keys", []):
            m = media_map.get(key)
            if m and "url" in m:
                media_urls.append(m["url"])

    # Gemini 返信生成
    reply = generate_reply(text, media_urls)
    if not reply:
        return

    print("生成:", reply)
    post_reply(reply, tweet_id)

if __name__ == "__main__":
    main()
