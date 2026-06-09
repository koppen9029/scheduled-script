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
NEWS_API_KEY   = os.environ["NEWS_API_KEY"]
CONSUMER_KEY          = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET       = os.environ["CONSUMER_SECRET"]
ACCESS_TOKEN          = os.environ["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET   = os.environ["ACCESS_TOKEN_SECRET"]

# =========================
# NewsAPI 用設定
# =========================
NEWS_URL = "https://newsapi.org/v2/everything"
NEWS_PARAMS = {
    "q": "news",
    "sortBy": "publishedAt",
    "language": "jp",
    "pageSize": 50,
    "apiKey": NEWS_API_KEY
}

# =========================
# ニュース取得
# =========================
def get_news() -> list:
    res = requests.get(NEWS_URL, params=NEWS_PARAMS)
    if res.status_code == 200:
        data = res.json()
        return [
            {"title": a["title"], "description": a["description"]}
            for a in data.get("articles", [])
            if a.get("title") and a.get("description")
        ]
    print("ニュース取得失敗", res.status_code)
    return []

# =========================
# Gemini でツイート生成
# =========================
def generate_tweet(articles: list) -> str:
    if not articles:
        return "ニュースが取得できなかったので静かに過ごしてるよ〜"

    # プロンプト作成
    prompt = (
        "以下のニュース一覧から、倫理的・不適切な内容を除外して"
        "日本語で140文字以内のツイート文を1つだけ生成してください:\n"
    )
    for a in articles:
        prompt += f"\n- {a['title']} — {a['description']}"

    # Gemini API クライアント
    client = genai.Client(api_key=GEMINI_API_KEY)

    # 生成
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=150),
    )

    text = response.text or ""
    text = text.strip()

    # 空文字 or 短すぎる場合はフォールバック
    if len(text) < 5:
        first = articles[0]["title"]
        return f"ニュース眺めてたら「{first[:30]}」って見出しあって、今日も世界は騒がしい〜"

    return text

# =========================
# Twitter 投稿
# =========================
def post_tweet(text: str) -> bool:
    url = "https://api.twitter.com/2/tweets"
    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    resp = requests.post(url, json={"text": text}, auth=auth)
    if resp.status_code == 201:
        print("投稿成功！")
        return True
    print("ツイート失敗:", resp.status_code, resp.text)
    return False

# =========================
# メイン
# =========================
def main():
    articles = get_news()
    print("記事数:", len(articles))
    tweet = generate_tweet(articles)
    print("生成ツイート:", tweet)
    post_tweet(tweet)

if __name__ == "__main__":
    main()
