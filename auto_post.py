#!/usr/bin/env python3
"""
もぐもぐキッズプロジェクト 自動投稿システム
- Claude APIでキャプション・ハッシュタグを自動生成
- テーマに合ったフォルダから未使用写真を選択（重複なし）
- ドラフトをJSONで保存
- Meta Graph APIで自動投稿
"""

import json
import os
import random
import time
import requests
import anthropic
from datetime import datetime
from pathlib import Path

# ===== パス設定 =====
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
DRAFTS_DIR = BASE_DIR / "drafts"
LOGS_DIR = BASE_DIR / "logs"
IMAGES_DIR = BASE_DIR / "images"
POSTED_PHOTOS_PATH = BASE_DIR / "posted_photos.json"

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/mogmogkids2026-pixel/instagram-auto-post/main/images"

# ディレクトリが存在しない場合は作成
DRAFTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)
for folder in ["dental", "food", "product", "farm", "kids"]:
    (IMAGES_DIR / folder).mkdir(exist_ok=True)

# ===== テーマ → フォルダ マッピング =====
THEME_TO_FOLDER = {
    "食育Tips":      "food",
    "噛む力・口腔発達": "dental",
    "野菜嫌い克服":   "farm",
    "米粉クッキー紹介": "product",
    "育児応援メッセージ": "kids",
    "言語発達と食事":  "dental",
    "季節の食育":    "farm",
}


def load_config():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return {
            "claude": {
                "api_key": os.environ["ANTHROPIC_API_KEY"],
                "model": "claude-haiku-4-5-20251001",
            },
            "instagram": {
                "access_token": os.environ.get("INSTAGRAM_ACCESS_TOKEN", ""),
                "ig_user_id": os.environ.get("INSTAGRAM_USER_ID", ""),
            },
        }
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m')}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


# ===== コンテンツテーマ定義 =====
CONTENT_THEMES = [
    {
        "type": "食育Tips",
        "prompt": "子どもの食育に関するワンポイントアドバイスを1つ紹介する投稿を作成してください。歯科医師・言語聴覚士監修の専門的な視点を含め、パパママが明日から実践できる内容にしてください。"
    },
    {
        "type": "噛む力・口腔発達",
        "prompt": "子どもの噛む力・口腔発達に関する投稿を作成してください。歯科医師監修の観点から、噛むことの重要性や、もぐもぐスティックのような適切な固さの食べ物が与える効果について触れてください。"
    },
    {
        "type": "野菜嫌い克服",
        "prompt": "子どもの野菜嫌いを楽しく克服するヒントについての投稿を作成してください。野菜ソムリエの視点から、野菜の旬・色・形への興味を引き出す工夫を1〜2個紹介してください。"
    },
    {
        "type": "米粉クッキー紹介",
        "prompt": "もぐもぐキッズプロジェクトの『米粉クッキーもぐもぐスティック』を紹介する投稿を作成してください。グルテンフリー・噛む力を育てる・食育につながるという3つの特徴を自然な形で伝えてください。宣伝感が強くなりすぎないよう、子どもの食育への想いをベースにしてください。"
    },
    {
        "type": "育児応援メッセージ",
        "prompt": "子育て中のパパママへの応援メッセージ投稿を作成してください。完璧な食事を目指さなくていい、一緒に食卓を楽しむことが食育の第一歩、というポジティブなメッセージを込めてください。"
    },
    {
        "type": "言語発達と食事",
        "prompt": "言語聴覚士監修の観点から、食事と言語発達の関係についての投稿を作成してください。咀嚼（そしゃく）・口の動かし方・言葉の発達がつながっているという気づきをわかりやすく伝えてください。"
    },
    {
        "type": "季節の食育",
        "prompt": f"現在の季節（{datetime.now().month}月）に合わせた旬の食材を使った子ども向け食育の投稿を作成してください。旬の食材名・その食材の食育的な価値・子どもに伝えられる豆知識を含めてください。"
    },
]

HASHTAGS_POOL = [
    "#食育", "#もぐもぐキッズ", "#歯科医師監修", "#言語聴覚士",
    "#米粉クッキー", "#グルテンフリー", "#噛む力", "#口腔発達",
    "#野菜ソムリエ", "#食育指導士", "#子どもの食育", "#離乳食",
    "#幼児食", "#子育てママ", "#子育てパパ", "#育児", "#子育て",
    "#食育活動", "#食育インストラクター", "#子どもの健康",
    "#もぐもぐスティック", "#食育ブック", "#幼稚園", "#保育園",
    "#子どもごはん", "#おやつ", "#米粉", "#グルテンフリーおやつ",
]


# ===== 写真管理（重複なし選択） =====

def load_posted_photos() -> dict:
    """投稿済み写真の記録を読み込む"""
    if POSTED_PHOTOS_PATH.exists():
        with open(POSTED_PHOTOS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_posted_photos(data: dict):
    """投稿済み写真の記録を保存する"""
    with open(POSTED_PHOTOS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_next_image(theme_type: str) -> str | None:
    """
    テーマに対応するフォルダから未使用の写真を1枚選んで返す。
    全写真を使い切ったらリセットして最初から。
    """
    folder_name = THEME_TO_FOLDER.get(theme_type, "food")
    folder_path = IMAGES_DIR / folder_name

    # 利用可能な写真一覧（jpg/png/JPG/PNG）
    extensions = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]
    photos = []
    for ext in extensions:
        photos.extend(folder_path.glob(ext))
    photo_names = sorted(set(p.name for p in photos))

    if not photo_names:
        log(f"⚠️  images/{folder_name}/ フォルダに画像がありません")
        return None

    # 投稿済み記録を読み込む
    posted = load_posted_photos()
    used_in_folder = posted.get(folder_name, [])

    # 未使用の写真を抽出
    unused = [p for p in photo_names if p not in used_in_folder]

    # 全部使い切ったらリセット
    if not unused:
        log(f"📷 images/{folder_name}/ の全写真を使い切りました。リセットします。")
        used_in_folder = []
        unused = photo_names

    # 未使用の中からランダムに1枚選ぶ
    selected = random.choice(unused)

    # 使用済みに記録して保存
    used_in_folder.append(selected)
    posted[folder_name] = used_in_folder
    save_posted_photos(posted)

    log(f"📷 選択画像: images/{folder_name}/{selected}")
    return f"{GITHUB_RAW_BASE}/{folder_name}/{selected}"


# ===== コンテンツ生成 =====

def generate_content(config: dict, theme: dict) -> dict:
    """Claude APIを使ってInstagram投稿コンテンツを生成する"""
    client = anthropic.Anthropic(api_key=config["claude"]["api_key"])

    system_prompt = """あなたは「もぐもぐキッズプロジェクト」の公式Instagramアカウント担当者です。

アカウント情報：
- 野菜ソムリエ×食育指導士が開発した食育ブランド
- 歯科医師・言語聴覚士監修
- 主な商品：米粉クッキーもぐもぐスティック、食育ブック
- ターゲット：0〜8歳の子どもを持つパパママ、幼稚園・医療機関

投稿のトーン：
- 専門知識をわかりやすく、温かみのある言葉で伝える
- 親が実践しやすい具体的な内容
- 押しつけがましくなく、共感を大切に
- 絵文字を適度に使用（1投稿に3〜5個程度）

出力形式（必ずこの形式で出力）：
CAPTION:
（ここにキャプション本文。200〜400文字程度）

HASHTAGS:
（スペース区切りで10〜15個のハッシュタグ）"""

    user_prompt = f"""以下のテーマでInstagram投稿を1つ作成してください。

テーマ：{theme['type']}
内容指示：{theme['prompt']}

キャプションは自然な会話調で、最後に行動喚起（保存・コメント・フォローなど）を1つ入れてください。"""

    for attempt in range(3):
        try:
            message = client.messages.create(
                model=config["claude"]["model"],
                max_tokens=1024,
                messages=[{"role": "user", "content": user_prompt}],
                system=system_prompt,
            )
            break
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < 2:
                log(f"Claude API混雑中、30秒後リトライ ({attempt+1}/3)...")
                time.sleep(30)
            else:
                raise

    response_text = message.content[0].text

    caption = ""
    hashtags = ""
    if "CAPTION:" in response_text and "HASHTAGS:" in response_text:
        parts = response_text.split("HASHTAGS:")
        caption = parts[0].replace("CAPTION:", "").strip()
        hashtags = parts[1].strip()
    else:
        caption = response_text.strip()
        hashtags = " ".join(random.sample(HASHTAGS_POOL, 12))

    return {
        "theme": theme["type"],
        "caption": caption,
        "hashtags": hashtags,
        "full_text": f"{caption}\n\n{hashtags}",
        "generated_at": datetime.now().isoformat(),
        "posted": False,
        "post_id": None,
    }


def save_draft(content: dict) -> Path:
    """生成したコンテンツをドラフトとして保存する"""
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{content['theme']}.json"
    filepath = DRAFTS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    log(f"ドラフト保存: {filepath.name}")
    return filepath


def post_to_instagram(config: dict, content: dict, image_url: str = None):
    """Meta Graph APIでInstagramに投稿する"""
    access_token = config["instagram"]["access_token"]
    ig_user_id = config["instagram"]["ig_user_id"]

    if not access_token or not ig_user_id:
        log("⚠️  Instagram APIキー未設定のためスキップします")
        return None

    if not image_url:
        log("⚠️  画像URLがないため投稿をスキップします")
        return None

    caption_text = content["full_text"]

    # STEP 1: メディアオブジェクト作成
    create_url = f"https://graph.facebook.com/v21.0/{ig_user_id}/media"
    create_params = {
        "image_url": image_url,
        "caption": caption_text,
        "access_token": access_token,
    }
    res = requests.post(create_url, data=create_params)
    if not res.ok:
        log(f"❌ メディア作成エラー: {res.status_code} {res.text}")
    res.raise_for_status()
    creation_id = res.json()["id"]

    # STEP 2: 投稿を公開
    publish_url = f"https://graph.facebook.com/v21.0/{ig_user_id}/media_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": access_token,
    }
    res = requests.post(publish_url, data=publish_params)
    res.raise_for_status()
    post_id = res.json()["id"]

    log(f"✅ Instagram投稿完了: post_id={post_id}")
    return post_id


def main():
    log("===== 自動投稿システム 起動 =====")
    config = load_config()

    # テーマをランダム選択
    theme = random.choice(CONTENT_THEMES)
    log(f"今回のテーマ: {theme['type']}")

    # コンテンツ生成
    log("Claude APIでコンテンツ生成中...")
    content = generate_content(config, theme)
    log("生成完了")

    # ドラフト保存
    draft_path = save_draft(content)

    # テーマに合った未使用写真を取得
    image_url = get_next_image(theme["type"])

    # Instagram投稿
    post_id = post_to_instagram(config, content, image_url)

    if post_id:
        content["posted"] = True
        content["post_id"] = post_id
        with open(draft_path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        log("✅ 完了: 投稿・ドラフト更新済み")
    else:
        log(f"📁 ドラフト保存済み: {draft_path.name}")
        if not image_url:
            log("   → images/<フォルダ>/ に写真を追加してください")

    log("===== 終了 =====")

    print("\n" + "=" * 50)
    print("【生成されたコンテンツ】")
    print("=" * 50)
    print(content["full_text"])
    print("=" * 50)


if __name__ == "__main__":
    main()
