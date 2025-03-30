#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import random
import requests
from requests_oauthlib import OAuth1

# =========================
# Twitter API キー設定（環境変数から取得）
# =========================
CONSUMER_KEY = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["CONSUMER_SECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = os.environ["ACCESS_TOKEN_SECRET"]

# =========================
# おはようツイートの候補
# =========================
GOOD_MORNING_TWEETS = [
    "おはようございます！今日も一緒に頑張りましょう！✨ #おはようVtuber",
    "おはようございます！新しい一日、笑顔でスタートしましょう！😊 #おはようVtuber",
    "おはようございます！今日も元気いっぱい、楽しい一日をお過ごしください！🌟 #おはようVtuber",
    "おはようございます！心躍る朝の始まりに、最高の笑顔を！💖 #おはようVtuber",
    "おはようございます！今日も自分らしく、輝く一日を！🌈 #おはようVtuber"
]

def post_tweet(text: str) -> bool:
    """
    Twitter APIを用いてツイートを投稿する関数。
    """
    url = "https://api.twitter.com/2/tweets"
    payload = {"text": text}
    
    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    response = requests.post(url, json=payload, auth=auth)
    
    if response.status_code == 201:
        print("ツイートが正常に投稿されました。")
        return True
    else:
        print(f"ツイート投稿エラー: {response.status_code} - {response.text}")
        return False

def main():
    # おはようツイートからランダムに選択
    tweet_text = random.choice(GOOD_MORNING_TWEETS)
    print("選ばれたツイート:", tweet_text)
    post_tweet(tweet_text)

if __name__ == "__main__":
    main()
