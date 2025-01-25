import os
import re

# (A) 入出力ファイル設定
kifu_file_path = "kifu.txt"  # 入力：和文棋譜
converted_kifu_path = "translated_kifs/converted_sfen.txt"  # 出力：USI形式

# 出力フォルダを作成
os.makedirs(os.path.dirname(converted_kifu_path), exist_ok=True)

# (B) 漢数字 → USI(行き先) 用マッピング
file_map_kanji = {
    "１":"1","２":"2","３":"3","４":"4","５":"5",
    "６":"6","７":"7","８":"8","９":"9"
}
rank_map_kanji = {
    "一":"a","二":"b","三":"c","四":"d","五":"e",
    "六":"f","七":"g","八":"h","九":"i"
}

# (C) 半角数字 → USI(移動元) 用マッピング
file_map_digit = {
    "1":"1","2":"2","3":"3","4":"4","5":"5",
    "6":"6","7":"7","8":"8","9":"9"
}
rank_map_digit = {
    "1":"a","2":"b","3":"c","4":"d","5":"e",
    "6":"f","7":"g","8":"h","9":"i"
}

# (D) 成り駒の変換
promoted_pieces = {
    "成桂":"桂","成銀":"銀","成香":"香","竜":"飛","馬":"角"
}

# (E) 打ち駒用：駒 → USI英字 (任意)
piece_map = {
    "歩":"P","香":"L","桂":"N","銀":"S","金":"G",
    "角":"B","飛":"R","玉":"K"
}

# --- 正規表現パターン ---
# 1) 通常手 (例: "52 ７六歩(77)" )
normal_pattern = re.compile(
    r"(\d+)\s+([１-９])([一二三四五六七八九])([^()]*)\((\d)(\d)\)"
)
# 2) 打ち駒 (例: "49 ４五歩打")
drop_pattern = re.compile(
    r"(\d+)\s+([１-９])([一二三四五六七八九])([^()]*)打"
)
# 3) 同 行 (例: "52 同桂(21)")
same_pattern = re.compile(
    r"(\d+)\s+同\s*([成歩香桂銀金角飛玉]+)\((\d)(\d)\)"
)

# (1) 通常手
def convert_normal_move(line_text):
    m = normal_pattern.match(line_text)
    if not m:
        return None

    dst_file_kanji = m.group(2)   # 行き先の筋(漢数字)
    dst_rank_kanji = m.group(3)   # 行き先の段(漢数字)
    piece_raw      = m.group(4)   # 駒種(成が含まれる場合も)
    src_file_digit = m.group(5)   # 元筋(数字)
    src_rank_digit = m.group(6)   # 元段(数字)

    # 成り駒を通常駒に戻す
    if piece_raw in promoted_pieces:
        piece_raw = promoted_pieces[piece_raw]
    if "成" in piece_raw:
        piece_raw = piece_raw.replace("成", "")

    try:
        sf = file_map_digit[src_file_digit]
        sr = rank_map_digit[src_rank_digit]
        df = file_map_kanji[dst_file_kanji]
        dr = rank_map_kanji[dst_rank_kanji]

        usi = f"{sf}{sr}{df}{dr}"

        # 成る手かどうか
        if "成" in line_text:
            usi += "+"

        return usi
    except KeyError:
        print(f"KeyError in normal_move: {line_text}")
        return None

# (2) 打ち駒
def convert_drop_move(line_text):
    m = drop_pattern.match(line_text)
    if not m:
        return None

    dst_file_kanji = m.group(2)
    dst_rank_kanji = m.group(3)
    piece_raw      = m.group(4)  # 駒名

    try:
        df = file_map_kanji[dst_file_kanji]
        dr = rank_map_kanji[dst_rank_kanji]

        # 駒を英字化 (例 "歩" → "P")
        piece_symbol = piece_map.get(piece_raw[0], "P")
        usi = f"{piece_symbol}*{df}{dr}"
        return usi
    except KeyError:
        print(f"KeyError in drop_move: {line_text}")
        return None

# (3) 同 行
def convert_same_move(line_text, last_dst):
    """
    例: "52 同桂(21)" → 駒=桂, 移動元=(2,1), 移動先=last_dst
    """
    m = same_pattern.match(line_text)
    if not m:
        return None

    piece_raw      = m.group(2)
    src_file_digit = m.group(3)
    src_rank_digit = m.group(4)

    # 成駒を戻す
    if piece_raw in promoted_pieces:
        piece_raw = promoted_pieces[piece_raw]
    if "成" in piece_raw:
        piece_raw = piece_raw.replace("成","")

    try:
        sf = file_map_digit[src_file_digit]
        sr = rank_map_digit[src_rank_digit]

        usi = f"{sf}{sr}{last_dst}"

        # 行中に "成" を含むなら+を付加
        if "成" in line_text:
            usi += "+"

        return usi
    except KeyError:
        print(f"KeyError in same_move: {line_text}")
        return None

# ------------------------------------------------------------------

def parse_kifu_line(line: str) -> str:
    """
    行をsplitして、(0:xx/00:xx:xx)形式の消費時間を無視。
    手数 + 指し手部分を結合して返す。
    例:
      "52 同　桂(21)        (0:02/00:01:17)"
      => 分割後 ["52","同","桂(21)","(0:02/00:01:17)"]
      => "52 同桂(21)"
    """
    parts = line.split()
    if len(parts) < 2:
        return ""

    # 先頭=手数
    move_num = parts[0]

    # 2番目以降を走査。消費時間っぽい文字列を除いてjoin
    filtered = []
    for p in parts[1:]:
        # もし "(" を含み ":" も含むなら => 消費時間とみなす
        if "(" in p and ":" in p:
            break
        filtered.append(p)

    move_text = "".join(filtered)  # 例: ["同","桂(21)"] -> "同桂(21)"

    return move_num + " " + move_text

# ------------------------------------------------------------------

def main():
    if not os.path.exists(kifu_file_path):
        print(f"❌ {kifu_file_path} が見つかりません。")
        return

    with open(kifu_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    moves_usi = []
    last_dst = None  # 前手の移動先マス (例: "7f")

    for idx, line in enumerate(lines, start=1):
        original_line = line.strip()
        if not original_line:
            continue
        # 棋譜終了キーワード
        if "まで" in original_line or "投了" in original_line:
            break

        # 1) 行をパースして "52 同桂(21)" 等を得る
        move_line = parse_kifu_line(original_line)
        if not move_line:
            print(f"⚠️ 無視された行: {original_line}")
            continue

        # 2) 正規表現で判定してUSIを生成
        # (a) 通常手
        usi = convert_normal_move(move_line)
        if usi:
            moves_usi.append(usi)
            # 移動先(末尾2文字)が "7f"など、"+"を除く
            usi_clean = usi.rstrip('+')
            dst = usi_clean[-2:]
            last_dst = dst
            continue

        # (b) 打ち駒
        usi = convert_drop_move(move_line)
        if usi:
            moves_usi.append(usi)
            # 移動先: "P*7f" → "7f"
            dst = usi.split("*")[-1]
            last_dst = dst
            continue

        # (c) 同 行
        if last_dst:
            usi = convert_same_move(move_line, last_dst)
            if usi:
                moves_usi.append(usi)
                # 移動先は 'last_dst' なので 'last_dst' を再度設定
                usi_clean = usi.rstrip('+')
                dst = usi_clean[-2:]
                last_dst = dst
                continue

        # ここまで来たらマッチしない
        print(f"⚠️ 指し手の変換エラー: {move_line}")

    # --- 出力 ---
    if moves_usi:
        with open(converted_kifu_path, "w", encoding="utf-8") as f:
            f.write("position startpos moves " + " ".join(moves_usi))

        print("✅ 棋譜を `position startpos moves` の形式に変換しました！\n")
        print("===== 変換結果 =====")
        with open(converted_kifu_path, "r", encoding="utf-8") as f2:
            print(f2.read())
    else:
        print("⚠️ 指し手が1つも変換されませんでした。")

if __name__ == "__main__":
    main()
