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

# — タイムライン取得（画像URL含む） —
def get_timeline_with_media(count=50):
    url = "https://api.twitter.com/2/users/me/timelines/reverse_chronological"
    params = {
        "max_results": count,
        "tweet.fields": "public_metrics,conversation_id,attachments,text",
        "expansions": "attachments.media_keys",
        "media.fields": "url,type"
    }
    r = requests.get(url, params=params, auth=auth)
    if r.status_code != 200:
        print("取得失敗:", r.status_code, r.text)
        return None

    data = r.json()
    tweets = data.get("data", [])
    includes = data.get("includes", {}).get("media", [])
    # メディア一覧を media_key→オブジェクト辞書に
    media_map = {m["media_key"]: m for m in includes}
    return tweets, media_map

# — 返信数が最大のツイート選ぶ —
def pick_best_tweet(tweets):
    if not tweets:
        return None
    return max(tweets, key=lambda x: x.get("public_metrics", {}).get("reply_count", 0))

# — Gemini で返信文生成（画像URL含めて） —
def generate_reply(tweet_text: str, media_urls: list[str]) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = "以下のツイートと画像から返信を考えて下さい（自然で丁寧な日本語）:\n"
    prompt += f"ツイート本文: {tweet_text}\n"
    if media_urls:
        prompt += "関連画像URL:\n"
        for url in media_urls:
            prompt += f"{url}\n"
    prompt += "\n返信文:"

    # Gemini 生成
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=120),
    )
    text = (response.text or "").strip()
    # フォールバック: 不十分なら "" を返して投稿しない
    if len(text) < 10:
        print("生成した返信が短すぎるのでスキップ…")
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
        print("返信成功！")
        return True
    print("返信失敗:", r.status_code, r.text)
    return False

# — 実行 —
def main():
    result = get_timeline_with_media()
    if not result:
        return
    tweets, media_map = result

    best = pick_best_tweet(tweets)
    if not best:
        print("対象ツイートなし〜")
        return

    tweet_id   = best["id"]
    text       = best["text"]
    print("選択:", text)

    # 画像URLを集める
    media_urls = []
    if best.get("attachments"):
        for key in best["attachments"].get("media_keys", []):
            m = media_map.get(key)
            if m and "url" in m:
                media_urls.append(m["url"])

    # Gemini 返信生成
    reply = generate_reply(text, media_urls)
    if not reply:
        print("返信生成できなかったよ〜")
        return

    print("生成:", reply)
    post_reply(reply, tweet_id)

if __name__ == "__main__":
    main()
