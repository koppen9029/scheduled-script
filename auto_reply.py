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

# — ② ホームタイムライン取得（除外指定付き & API側フィルタ） —
def get_home_timeline_filtered(user_id, count=50):
    url = f"https://api.twitter.com/2/users/{user_id}/timelines/reverse_chronological"
    params = {
        "max_results": count,
        # API側でリツイート & 返信を除外
        "exclude": "retweets,replies",
        # 追加で詳細を取りたいフィールド
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
    media_list = data.get("includes", {}).get("media", [])
    media_map = {m["media_key"]: m for m in media_list}

    # — 自前フィルタで確実に除外!
    filtered = []
    for t in tweets:
        # referenced_tweets があるとリツイート・返信・引用の可能性があるため除去
        refs = t.get("referenced_tweets", [])
        if any(r["type"] in ["retweeted","replied_to","quoted"] for r in refs):
            continue
        filtered.append(t)

    return filtered, media_map

# — ③ 返信数が最大のツイート選ぶ —
def pick_best_tweet(tweets):
    if not tweets:
        return None
    return max(tweets, key=lambda x: x.get("public_metrics", {}).get("reply_count", 0))

# — ④ Gemini 返信文生成 —
def generate_reply(tweet_text: str, media_urls: list[str]) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = "以下の投稿（テキスト＋画像URL）を見て、自然で丁寧な返信文を日本語で考えてください:\n"
    prompt += f"投稿本文: {tweet_text}\n"
    if media_urls:
        prompt += "画像リンク:\n"
        for url in media_urls:
            prompt += f"{url}\n"
    prompt += "\n返信文:"

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=120),
    )
    text = (response.text or "").strip()

    # 短すぎる場合は投稿しない（フォールバックしない）
    if len(text) < 10:
        print("返信の生成が短すぎるのでスキップ〜")
        return ""
    return text

# — ⑤ リプライ投稿 —
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

    tweets, media_map = get_home_timeline_filtered(user_id)
    best = pick_best_tweet(tweets)
    if not best:
        print("返信対象がないよ〜")
        return

    tweet_id = best["id"]
    text = best["text"]
    print("対象ツイート:", text)

    # — 画像URL を集める —
    media_urls = []
    if best.get("attachments"):
        for key in best["attachments"].get("media_keys", []):
            m = media_map.get(key)
            if m and "url" in m:
                media_urls.append(m["url"])

    # — Gemini で返信文を生成 —
    reply = generate_reply(text, media_urls)
    if not reply:
        return

    print("生成された返信文:", reply)
    post_reply(reply, tweet_id)

if __name__ == "__main__":
    main()
