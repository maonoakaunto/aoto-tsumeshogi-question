import os
import re

kifu_file_path = "kifu.txt"
converted_kifu_path = "translated_kifs/converted_sfen.txt"
os.makedirs(os.path.dirname(converted_kifu_path), exist_ok=True)

file_map = {"１": "1", "２": "2", "３": "3", "４": "4", "５": "5",
            "６": "6", "７": "7", "８": "8", "９": "9"}
rank_map = {"一": "a", "二": "b", "三": "c", "四": "d", "五": "e",
            "六": "f", "七": "g", "八": "h", "九": "i"}

# 正規表現 (ASCIIカッコだけ対応)
move_pattern = re.compile(
    r"(\d+)\s+([１-９])([一二三四五六七八九])([歩香桂銀金角飛玉成打]*)\((\d)(\d)\)"
)

promoted_pieces = {
    "成桂": "桂", "成銀": "銀", "成香": "香", "竜": "飛", "馬": "角"
}

def convert_kifu_to_usi(move: str):
    match = move_pattern.match(move)
    if not match:
        print(f"⚠️ 指し手の変換エラー: {move}")
        return ""
    try:
        dst_file = file_map[match.group(2)]
        dst_rank = rank_map[match.group(3)]
        piece    = match.group(4)
        src_file = match.group(5)
        src_rank = match.group(6)

        # 成り駒を通常駒に戻す
        if piece in promoted_pieces:
            piece = promoted_pieces[piece]
        if "成" in piece:
            piece = piece.replace("成", "")

        # 打ち駒かどうか
        if "打" in piece:
            return f"{piece[0]}*{dst_file}{dst_rank}"

        # 通常の移動
        usi_move = f"{src_file}{src_rank}{dst_file}{dst_rank}"

        # 指し手内に「成」があったら+を付加
        if "成" in move:
            usi_move += "+"

        return usi_move
    except KeyError:
        print(f"⚠️ 指し手の変換エラー: {move}")
        return ""

if not os.path.exists(kifu_file_path):
    print("❌ `kifu.txt` が見つかりません。")
    exit()

with open(kifu_file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

moves_kifu = []
for line in lines:
    line = line.strip()
    if not line:
        continue

    # ① 全角カッコを半角カッコに置換
    line = line.replace("（", "(").replace("）", ")")

    # "まで" や "投了" があれば打ち切り
    if "まで" in line or "投了" in line:
        break

    parts = line.split()
    if len(parts) < 2:
        continue

    # 手数 + 指し手部分を取り出す ("1 ２六歩(27)" など)
    move_kifu = parts[0] + " " + parts[1]

    if move_pattern.match(move_kifu):
        moves_kifu.append(move_kifu)

moves_usi = []
for mk in moves_kifu:
    usi = convert_kifu_to_usi(mk)
    if usi:
        moves_usi.append(usi)

if moves_usi:
    with open(converted_kifu_path, "w", encoding="utf-8") as f:
        f.write("position startpos moves " + " ".join(moves_usi))
    print("✅ 棋譜を `position startpos moves` の形式に変換しました！\n")
    with open(converted_kifu_path, "r", encoding="utf-8") as f:
        print("===== 変換されたUSI形式の棋譜 =====")
        print(f.read())
else:
    print("⚠️ 指し手が抽出されませんでした。")
