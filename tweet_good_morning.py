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
