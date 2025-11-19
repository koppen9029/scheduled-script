# -*- coding: utf-8 -*-
import os
import json
import requests
from requests_oauthlib import OAuth1Session, OAuth1
import google.generativeai as genai

# =========================
# APIキー・トークン設定（環境変数から読み込む）
# =========================
CONSUMER_KEY = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["CONSUMER_SECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = os.environ["ACCESS_TOKEN_SECRET"]

# Gemini(PaLM API)のAPIキー
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

# =========================
# NewsAPIの設定（環境変数から読み込む）
# =========================
NEWS_API_KEY = os.environ["NEWS_API_KEY"]
NEWS_URL = "https://newsapi.org/v2/everything"
NEWS_PARAMS = {
    "q": "news",
    "sortBy": "publishedAt",
    "language": "jp",
    "pageSize": 100,
    "apiKey": NEWS_API_KEY
}

# =========================
# 関数定義
# =========================
def get_news() -> list:
    """
    NewsAPIからニュース記事を取得する関数。
    タイトルとディスクリプションをまとめて返す。
    """
    response = requests.get(NEWS_URL, params=NEWS_PARAMS)
    if response.status_code == 200:
        data = response.json()
        articles = data.get("articles", [])

        # タイトルとDescriptionが存在するもののみ抽出
        article_list = [
            {
                "title": article["title"],
                "description": article["description"]
            }
            for article in articles if article["title"] and article["description"]
        ]
        return article_list
    else:
        print(f"ニュース記事の取得に失敗しました。HTTP Status Code: {response.status_code}")
        return []

def generate_tweet_from_news(articles: list) -> str:
    """
    取得したニュース記事を元にGemini(PaLM API)でツイート文を生成する関数。
    """
    # ニュース記事をプロンプトとして連結
    prompt = (
        "以下のツイート内容から倫理的、モラル的に不適切な内容を除外したうえで面白い話を選んだうえで、"
        "日本語で1つのユニークなまるで人が書いたつぶやきのようなツイート文のみひとつだけ作成してください（140文字程度以内）：\n"
    )
    for article in articles:
        title = article.get("title", "タイトル不明")
        description = article.get("description", "説明なし")
        prompt += f"\n- タイトル: {title}\n  概要: {description}"

    # Gemini(PaLM API)の初期設定
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction="主観的にツイート内容をツイッターの文字数制限内で生成。日本語で。人間のなにげないおもしろツイート風で"
    )

    # テキスト生成（max_output_tokensは必要に応じて調整可能）
    response = model.generate_content(
        [prompt],
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=100  # 生成するトークン数の上限（適宜調整）
        ),
    )

    generated_text = response.text
    return generated_text

def post_tweet(text: str) -> bool:
    """
    生成されたテキストをTwitterに投稿する関数。
    """
    url = "https://api.twitter.com/2/tweets"
    payload = {"text": text}

    # OAuth1認証
    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    response = requests.post(url, json=payload, auth=auth)

    if response.status_code == 201:
        print("ツイートが正常に投稿されました。")
        return True
    else:
        print(f"ツイート投稿エラー: {response.status_code} - {response.text}")
        return False

# =========================
# メイン処理
# =========================
def main():
    # 1. ニュース記事を取得
    articles = get_news()
    if not articles:
        print("ニュース記事が取得できませんでした。処理を終了します。")
        return

    # 2. 取得記事を表示（デバッグ目的）
    print("▼取得したニュース記事一覧（上位5件を表示）")
    for i, article in enumerate(articles[:5], start=1):
        print("-------------------------------------------")
        print(f"記事{i} タイトル:", article["title"])
        print("　内容:", article["description"])

    # 3. ニュース記事からツイート文を生成
    generated_tweet = generate_tweet_from_news(articles)
    print("\n▼生成されたツイート:")
    print(generated_tweet)

    # 4. 生成したツイートを実際に投稿
    post_tweet(generated_tweet)

if __name__ == "__main__":
    main()
