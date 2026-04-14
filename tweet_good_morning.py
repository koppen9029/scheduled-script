#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import sys
import requests
from requests_oauthlib import OAuth1

# =========================
# X API キー設定（環境変数から取得）
# =========================
CONSUMER_KEY = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["CONSUMER_SECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = os.environ["ACCESS_TOKEN_SECRET"]

# =========================
# おはようポスト候補
# =========================
GOOD_MORNING_TWEETS = [
    "おはようございます！今日もみんなと一緒に楽しい時間を過ごせますように！ #おはようVtuber",
    "おはようございます！新しいスタート、笑顔を忘れずに進もう！ #おはようVtuber",
    "おはようございます！今日も心に輝きを持って、元気いっぱいに！ #おはようVtuber",
    "おはようございます！あなたの笑顔が今日も輝きますように！ #おはようVtuber",
    "おはようございます！今日も自分らしく、一歩ずつ前進しましょう！ #おはようVtuber",
    "おはようございます！元気と笑顔で、今日も一緒に頑張ろう！ #おはようVtuber",
    "おはようございます！みんなが笑顔で溢れる素敵な一日になりますように！ #おはようVtuber",
    "おはようございます！心新たに、今日も新たな挑戦に向かって進もう！ #おはようVtuber",
    "おはようございます！小さな幸せを見つけて、素敵な一日を！ #おはようVtuber",
    "おはようございます！一緒に笑顔で今日も前向きに歩みましょう！ #おはようVtuber",
    "おはようございます！今日も元気と笑顔で、素敵な時間を共有しましょう！ #おはようVtuber",
    "おはようございます！小さな一歩が大きな夢へ繋がりますように！ #おはようVtuber",
    "おはようございます！みんなで支え合いながら、今日も最高の日にしましょう！ #おはようVtuber",
    "おはようございます！心に太陽を、今日も輝く一日を！ #おはようVtuber",
    "おはようございます！一日一善、今日も笑顔で頑張りましょう！ #おはようVtuber",
    "おはようございます！自分のペースで、今日もゆったりと楽しんでね！ #おはようVtuber",
    "おはようございます！新たな挑戦に向かって、今日も踏み出そう！ #おはようVtuber",
    "おはようございます！心からの笑顔が、素敵な一日を創りますように！ #おはようVtuber",
    "おはようございます！小さな喜びを大切に、今日も一緒に歩んでいこう！ #おはようVtuber",
    "おはようございます！今日も新しい発見と素敵な出会いがありますように！ #おはようVtuber"
]

# =========================
# API URL
# =========================
POST_TWEET_URL = "https://api.x.com/2/tweets"
ME_URL = "https://api.x.com/2/users/me"

# =========================
# OAuth1 認証
# =========================
auth = OAuth1(
    CONSUMER_KEY,
    CONSUMER_SECRET,
    ACCESS_TOKEN,
    ACCESS_TOKEN_SECRET
)


def who_am_i() -> dict | None:
    """
    現在のアクセストークンがどのアカウントに紐づいているか確認する。
    """
    print("認証アカウント確認中...")
    try:
        response = requests.get(ME_URL, auth=auth, timeout=30)
        print(f"users/me status: {response.status_code}")
        print(f"users/me response: {response.text}")

        if response.status_code == 200:
            data = response.json().get("data", {})
            user_id = data.get("id")
            name = data.get("name")
            username = data.get("username")
            print(f"認証中アカウント: {name} (@{username}) / id={user_id}")
            return data
        else:
            print("認証アカウント確認に失敗しました。")
            return None

    except requests.RequestException as e:
        print(f"users/me 通信エラー: {e}")
        return None
    except Exception as e:
        print(f"users/me 予期せぬエラー: {e}")
        return None


def post_tweet(text: str) -> bool:
    """
    X APIを用いてポストを投稿する関数。
    成功時は投稿ID・投稿URLを表示する。
    """
    payload = {"text": text}

    print("投稿リクエスト送信中...")
    print(f"投稿本文: {text}")

    try:
        response = requests.post(POST_TWEET_URL, json=payload, auth=auth, timeout=30)

        print(f"post status: {response.status_code}")
        print(f"post response: {response.text}")

        if response.status_code == 201:
            try:
                response_json = response.json()
            except ValueError:
                print("レスポンスJSONの解析に失敗しました。")
                return False

            data = response_json.get("data", {})
            tweet_id = data.get("id")
            tweet_text = data.get("text")

            print("ポストが正常に投稿されました。")
            print(f"投稿ID: {tweet_id}")
            print(f"投稿本文(返却値): {tweet_text}")

            if tweet_id:
                print(f"投稿URL: https://x.com/i/web/status/{tweet_id}")

            return True
        else:
            print("ポスト投稿エラー")
            return False

    except requests.RequestException as e:
        print(f"投稿通信エラー: {e}")
        return False
    except Exception as e:
        print(f"投稿時の予期せぬエラー: {e}")
        return False


def main():
    # まず今の認証先アカウントを確認
    me = who_am_i()
    if me is None:
        print("認証情報の確認に失敗したため終了します。")
        sys.exit(1)

    # ランダムに投稿文を選択
    tweet_text = random.choice(GOOD_MORNING_TWEETS)
    print("選ばれたツイート:", tweet_text)

    # 投稿
    success = post_tweet(tweet_text)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
