#!/usr/bin/env python3
"""
もぐもぐキッズプロジェクト ブランド画像自動生成
10枚（各フォルダ2枚）を生成してimages/各フォルダに保存
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

BASE_DIR = Path(__file__).parent
IMAGES_DIR = BASE_DIR / "images"
LOGO_PATH = Path("/Users/yutayoshino/Desktop/食育事業/名刺・画像・写真/ロゴ完成版.png")

# ===== ブランドカラー =====
ORANGE      = (232,  96,  30)   # #E8601E
ORANGE_LIGHT= (255, 235, 210)   # 薄オレンジ
GREEN       = (109, 178,  42)   # #6DB22A
GREEN_LIGHT = (235, 248, 220)   # 薄グリーン
GRAY        = (120, 120, 120)
GRAY_LIGHT  = (245, 245, 245)
WHITE       = (255, 255, 255)
CREAM       = (255, 250, 243)
BEIGE       = (253, 243, 231)

SIZE = 1080

# ===== フォント =====
FONT_BOLD    = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_REGULAR = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"

def font(path, size):
    return ImageFont.truetype(path, size)

def load_logo(width=260):
    """ロゴを読み込み、白背景を透明化してリサイズ"""
    try:
        import numpy as np
        img = Image.open(LOGO_PATH).convert("RGBA")
        arr = np.array(img)
        # 白に近いピクセル（RGB全て>240）を透明に
        mask = (arr[:,:,0] > 240) & (arr[:,:,1] > 240) & (arr[:,:,2] > 240)
        arr[mask, 3] = 0
        logo = Image.fromarray(arr)
        ratio = width / logo.width
        h = int(logo.height * ratio)
        return logo.resize((width, h), Image.LANCZOS)
    except Exception as e:
        print(f"  ロゴ読み込み失敗: {e}")
        return None

def paste_logo(img, logo, margin=40):
    """右下にロゴを配置"""
    if logo is None:
        return
    x = SIZE - logo.width - margin
    y = SIZE - logo.height - margin
    if logo.mode == "RGBA":
        img.paste(logo, (x, y), logo)
    else:
        img.paste(logo, (x, y))

def draw_rounded_rect(draw, xy, radius, fill):
    """角丸矩形を描画"""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.ellipse([x1, y1, x1 + radius*2, y1 + radius*2], fill=fill)
    draw.ellipse([x2 - radius*2, y1, x2, y1 + radius*2], fill=fill)
    draw.ellipse([x1, y2 - radius*2, x1 + radius*2, y2], fill=fill)
    draw.ellipse([x2 - radius*2, y2 - radius*2, x2, y2], fill=fill)

def multiline_center(draw, text, y, font_obj, fill, line_spacing=1.3):
    """複数行テキストを中央揃えで描画"""
    lines = text.split("\n")
    bbox = draw.textbbox((0, 0), "あ", font=font_obj)
    line_h = int((bbox[3] - bbox[1]) * line_spacing)
    total_h = line_h * len(lines)
    current_y = y - total_h // 2
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font_obj)
        w = bb[2] - bb[0]
        draw.text(((SIZE - w) // 2, current_y), line, font=font_obj, fill=fill)
        current_y += line_h

def save(img, folder, filename):
    path = IMAGES_DIR / folder / filename
    img.save(path, "JPEG", quality=95)
    print(f"  ✅ {folder}/{filename}")


# ======================================================
# 生成関数 × 10枚
# ======================================================

def make_food_01(logo):
    """食育Tips 01 - オレンジ上部帯 + クリーム背景"""
    img = Image.new("RGB", (SIZE, SIZE), CREAM)
    d = ImageDraw.Draw(img)

    # 上部オレンジ帯
    d.rectangle([0, 0, SIZE, 240], fill=ORANGE)

    # 帯内 装飾円（半透明風）
    d.ellipse([SIZE-200, -80, SIZE+60, 180], fill=(255, 120, 50))
    d.ellipse([-60, -40, 180, 200], fill=(255, 120, 50))

    # 帯タイトル
    d.text((540, 120), "食育 Tips", font=font(FONT_BOLD, 80),
           fill=WHITE, anchor="mm")

    # メイン装飾円（大）
    d.ellipse([200, 300, 880, 820], fill=WHITE)

    # メインテキスト
    multiline_center(d, "毎日の食卓が\n学びの場になる", 540,
                     font(FONT_BOLD, 68), ORANGE)

    # サブテキスト
    multiline_center(d, "専門家監修", 730,
                     font(FONT_REGULAR, 32), GRAY)

    # 下部グリーンライン
    d.rectangle([0, SIZE-12, SIZE, SIZE], fill=GREEN)

    paste_logo(img, logo)
    save(img, "food", "food_01.jpg")


def make_food_02(logo):
    """食育Tips 02 - グリーン左帯 + ホワイト"""
    img = Image.new("RGB", (SIZE, SIZE), WHITE)
    d = ImageDraw.Draw(img)

    # 左グリーン帯
    d.rectangle([0, 0, 160, SIZE], fill=GREEN)

    # 帯内縦テキスト（装飾）
    for i, ch in enumerate("食育"):
        d.text((80, 180 + i * 120), ch,
               font=font(FONT_BOLD, 90), fill=WHITE, anchor="mm")

    # 右側 装飾円（薄グリーン）
    d.ellipse([500, 80, 1060, 640], fill=GREEN_LIGHT)

    # メインテキスト
    multiline_center(d, "今日の\nいただきます", 430,
                     font(FONT_BOLD, 90), GREEN)

    # サブテキスト
    multiline_center(d, "家族で食卓を囲むことが\n食育のはじまりです", 680,
                     font(FONT_REGULAR, 38), GRAY)

    # 下部オレンジライン
    d.rectangle([0, SIZE-12, SIZE, SIZE], fill=ORANGE)

    paste_logo(img, logo)
    save(img, "food", "food_02.jpg")


def make_dental_01(logo):
    """噛む力・口腔発達 01"""
    img = Image.new("RGB", (SIZE, SIZE), WHITE)
    d = ImageDraw.Draw(img)

    # 上部グリーン帯
    d.rectangle([0, 0, SIZE, 220], fill=GREEN)

    # 帯内装飾
    d.ellipse([820, -80, 1160, 260], fill=(130, 200, 60))

    # 帯タイトル
    d.text((120, 110), "噛む力・口腔発達", font=font(FONT_BOLD, 64),
           fill=WHITE, anchor="lm")

    # 大きな「噛」文字（装飾）
    d.text((540, 530), "噛", font=font(FONT_BOLD, 380),
           fill=ORANGE_LIGHT, anchor="mm")

    # オーバーレイテキスト
    multiline_center(d, "しっかり噛むことが\nことばを育てる", 490,
                     font(FONT_BOLD, 72), ORANGE)

    # サブテキスト
    multiline_center(d, "専門家監修", 720,
                     font(FONT_REGULAR, 34), GRAY)

    # 下部オレンジライン
    d.rectangle([0, SIZE-12, SIZE, SIZE], fill=ORANGE)

    paste_logo(img, logo)
    save(img, "dental", "dental_01.jpg")


def make_dental_02(logo):
    """言語発達と食事 02"""
    img = Image.new("RGB", (SIZE, SIZE), GREEN_LIGHT)
    d = ImageDraw.Draw(img)

    # 白い大きな角丸カード
    draw_rounded_rect(d, [80, 100, 1000, 900], 60, WHITE)

    # 上部オレンジアクセントバー（カード内）
    draw_rounded_rect(d, [80, 100, 1000, 230], 60, ORANGE)
    # 下半分を上書き（角丸を角に）
    d.rectangle([80, 165, 1000, 230], fill=ORANGE)

    # タイトル
    d.text((540, 165), "言語発達と食事", font=font(FONT_BOLD, 60),
           fill=WHITE, anchor="mm")

    # 吹き出し円（装飾）
    d.ellipse([340, 280, 740, 580], fill=ORANGE_LIGHT)

    # メインテキスト
    multiline_center(d, "食べることで\n口が動く\n口が動くと\nことばが生まれる", 490,
                     font(FONT_BOLD, 58), ORANGE)

    # サブテキスト
    multiline_center(d, "専門家監修", 730,
                     font(FONT_REGULAR, 36), GRAY)

    paste_logo(img, logo)
    save(img, "dental", "dental_02.jpg")


def make_farm_01(logo):
    """野菜嫌い克服 01 - グリーン全面"""
    img = Image.new("RGB", (SIZE, SIZE), GREEN)
    d = ImageDraw.Draw(img)

    # 装飾円（明るいグリーン）
    d.ellipse([-100, -100, 400, 400], fill=(130, 200, 60))
    d.ellipse([700, 700, 1200, 1200], fill=(130, 200, 60))

    # 下部白い波（台形で代用）
    d.polygon([0, 820, SIZE, 720, SIZE, SIZE, 0, SIZE], fill=WHITE)

    # メインテキスト（白）
    multiline_center(d, "やさいって\nたのしい！", 420,
                     font(FONT_BOLD, 110), WHITE)

    # サブテキスト
    multiline_center(d, "野菜ソムリエが教える\n食べてみたくなる工夫", 680,
                     font(FONT_REGULAR, 38), WHITE)

    # 下部テキスト（グリーン）
    multiline_center(d, "野菜嫌い克服", 900,
                     font(FONT_BOLD, 40), GREEN)

    paste_logo(img, logo, margin=50)
    save(img, "farm", "farm_01.jpg")


def make_farm_02(logo):
    """季節の食育 02"""
    img = Image.new("RGB", (SIZE, SIZE), CREAM)
    d = ImageDraw.Draw(img)

    # 葉っぱ風の楕円（大・装飾）
    for x, y, a, b in [(150, 300, 260, 360), (900, 200, 200, 280),
                        (800, 750, 240, 200), (180, 780, 200, 160)]:
        d.ellipse([x-a//2, y-b//2, x+a//2, y+b//2], fill=GREEN_LIGHT)

    # 白い中央カード
    draw_rounded_rect(d, [120, 140, 960, 820], 60, WHITE)

    # グリーン上帯（カード内）
    draw_rounded_rect(d, [120, 140, 960, 280], 60, GREEN)
    d.rectangle([120, 210, 960, 280], fill=GREEN)

    # タイトル
    d.text((540, 210), "旬の食材で食育", font=font(FONT_BOLD, 60),
           fill=WHITE, anchor="mm")

    # メインテキスト
    multiline_center(d, "季節を食べると\n子どもの感性が\n育ちます", 530,
                     font(FONT_BOLD, 72), GREEN)

    # サブ
    multiline_center(d, "野菜ソムリエ監修", 760,
                     font(FONT_REGULAR, 36), GRAY)

    # 下部オレンジ帯
    d.rectangle([0, SIZE-100, SIZE, SIZE], fill=ORANGE)
    d.text((540, SIZE-50), "季節の食育", font=font(FONT_BOLD, 44),
           fill=WHITE, anchor="mm")

    paste_logo(img, logo)
    save(img, "farm", "farm_02.jpg")


def make_product_01(logo):
    """米粉クッキー紹介 01"""
    img = Image.new("RGB", (SIZE, SIZE), BEIGE)
    d = ImageDraw.Draw(img)

    # 大きな装飾円（オレンジ薄）
    d.ellipse([140, 100, 940, 900], fill=ORANGE_LIGHT)

    # 白い内円
    d.ellipse([220, 180, 860, 820], fill=WHITE)

    # メインテキスト
    multiline_center(d, "もぐもぐ\nスティック", 430,
                     font(FONT_BOLD, 96), ORANGE)

    # サブテキスト
    multiline_center(d, "米粉クッキー", 640,
                     font(FONT_BOLD, 52), GREEN)

    # タグ風テキスト
    for i, tag in enumerate(["グルテンフリー", "噛む力を育てる", "食育につながる"]):
        y = 740 + i * 60
        bb = d.textbbox((0, 0), tag, font=font(FONT_REGULAR, 32))
        w = bb[2] - bb[0] + 40
        x = (SIZE - w) // 2
        draw_rounded_rect(d, [x, y-18, x+w, y+34], 20,
                          GREEN if i % 2 == 0 else ORANGE)
        d.text((SIZE//2, y+8), tag, font=font(FONT_REGULAR, 32),
               fill=WHITE, anchor="mm")

    paste_logo(img, logo)
    save(img, "product", "product_01.jpg")


def make_product_02(logo):
    """米粉クッキー紹介 02"""
    img = Image.new("RGB", (SIZE, SIZE), WHITE)
    d = ImageDraw.Draw(img)

    # 上部 グリーン帯
    d.rectangle([0, 0, SIZE, 200], fill=GREEN)
    d.ellipse([800, -60, 1140, 280], fill=(130, 200, 60))

    # タイトル
    d.text((120, 100), "米粉でつくった\nおやつ", font=font(FONT_BOLD, 68),
           fill=WHITE, anchor="lm")

    # メイン 大テキスト（オレンジ装飾）
    d.text((540, 480), "もぐもぐ", font=font(FONT_BOLD, 140),
           fill=ORANGE_LIGHT, anchor="mm")

    # 重ねテキスト
    multiline_center(d, "子どもの\n「噛む力」を\n楽しく育てる", 480,
                     font(FONT_BOLD, 74), ORANGE)

    # 下部ライン＋テキスト
    d.rectangle([0, SIZE-100, SIZE, SIZE], fill=BEIGE)
    multiline_center(d, "専門家監修 ｜ 野菜ソムリエ開発", SIZE-50,
                     font(FONT_REGULAR, 30), GRAY)

    paste_logo(img, logo)
    save(img, "product", "product_02.jpg")


def make_kids_01(logo):
    """育児応援メッセージ 01 - 温かみのあるデザイン"""
    img = Image.new("RGB", (SIZE, SIZE), ORANGE_LIGHT)
    d = ImageDraw.Draw(img)

    # 装飾円
    d.ellipse([-80, -80, 320, 320], fill=(255, 220, 180))
    d.ellipse([780, 760, 1180, 1160], fill=(255, 220, 180))

    # 白いカード
    draw_rounded_rect(d, [80, 120, 1000, 880], 60, WHITE)

    # オレンジ上部帯（カード内）
    draw_rounded_rect(d, [80, 120, 1000, 280], 60, ORANGE)
    d.rectangle([80, 200, 1000, 280], fill=ORANGE)
    d.text((540, 200), "パパ・ママへ", font=font(FONT_BOLD, 54),
           fill=WHITE, anchor="mm")

    # メインメッセージ
    multiline_center(d, "完璧じゃ\nなくていい", 490,
                     font(FONT_BOLD, 104), ORANGE)

    # サブメッセージ
    multiline_center(d, "一緒に食卓を囲む時間が\n一番の食育です", 720,
                     font(FONT_REGULAR, 40), GRAY)

    paste_logo(img, logo)
    save(img, "kids", "kids_01.jpg")


def make_kids_02(logo):
    """育児応援メッセージ 02"""
    img = Image.new("RGB", (SIZE, SIZE), CREAM)
    d = ImageDraw.Draw(img)

    # グリーン上部帯
    d.rectangle([0, 0, SIZE, 220], fill=GREEN)
    d.ellipse([-60, -60, 260, 260], fill=(130, 200, 60))

    # タイトル
    d.text((540, 110), "今日もよくがんばってる", font=font(FONT_BOLD, 52),
           fill=WHITE, anchor="mm")

    # 大きな引用符（装飾）
    d.text((100, 280), "\"", font=font(FONT_BOLD, 260), fill=GREEN_LIGHT,
           anchor="lt")

    # メインメッセージ
    multiline_center(d, "子どもと一緒に\n食事を楽しめた日は\n最高の食育の日", 560,
                     font(FONT_BOLD, 64), GREEN)

    # 下部引用符
    d.text((SIZE-100, 820), "\"", font=font(FONT_BOLD, 260), fill=GREEN_LIGHT,
           anchor="rt")

    # 下部テキスト
    multiline_center(d, "もぐもぐキッズプロジェクト", 940,
                     font(FONT_REGULAR, 34), GRAY)

    paste_logo(img, logo)
    save(img, "kids", "kids_02.jpg")


# ======================================================
# メイン実行
# ======================================================

if __name__ == "__main__":
    print("ブランド画像生成開始...")
    logo = load_logo(width=200)

    makers = [
        make_food_01, make_food_02,
        make_dental_01, make_dental_02,
        make_farm_01, make_farm_02,
        make_product_01, make_product_02,
        make_kids_01, make_kids_02,
    ]
    for fn in makers:
        fn(logo)

    print(f"\n完了！ 合計 {len(makers)} 枚生成しました。")
    print("images/ 配下の各フォルダを確認してください。")
