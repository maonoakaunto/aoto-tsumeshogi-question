import os
import subprocess

# --- 将棋エンジンの絶対パス ---
ENGINE_PATH = r"C:\Users\mao10\OneDrive\Haou\YaneuraOu_NNUE-tournament-clang++-avx2.exe"

# --- 変換済みの棋譜ファイル（position startpos moves... が書かれたファイル）---
CONVERTED_FILE = "translated_kifs/converted_sfen.txt"

def send_command(engine, cmd):
    """将棋エンジンにコマンドを送る"""
    if engine.poll() is not None:
        print("❌ エンジンは既に終了しています。コマンドを送れません。")
        return
    print(f"📝 コマンド送信: {cmd}")
    engine.stdin.write(cmd + "\n")
    engine.stdin.flush()

def wait_for(engine, keyword):
    """エンジンの出力を1行ずつ読み、指定したキーワードを含む行が来るまで表示する"""
    while True:
        line = engine.stdout.readline().rstrip("\n")
        if not line:
            break
        print("🔹", line)
        if keyword in line:
            break

def main():
    # (1) 変換後の棋譜ファイルを先に読み込む
    if not os.path.exists(CONVERTED_FILE):
        print(f"❌ 変換後の棋譜ファイルが見つかりません: {CONVERTED_FILE}")
        return
    with open(CONVERTED_FILE, "r", encoding="utf-8") as f:
        position_cmd = f.readline().strip()

    if not position_cmd.startswith("position"):
        print("❌ ファイルの先頭が `position` ではありません。棋譜の形式を確認してください。")
        print("取得した行:", position_cmd)
        return

    print("✅ 変換された棋譜を読み込み:", position_cmd)

    # (2) 将棋エンジンのあるフォルダに移動する (os.chdir)
    engine_dir = os.path.dirname(ENGINE_PATH)  
    if engine_dir:
        # エンジンのあるフォルダに移動
        os.chdir(engine_dir)
        print(f"✅ カレントディレクトリをエンジンの場所に変更しました: {engine_dir}")
    else:
        print("⚠️ エンジンのパスからフォルダが取得できません。")

    # (3) 将棋エンジンを起動
    try:
        engine = subprocess.Popen(
            [ENGINE_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
    except FileNotFoundError:
        print(f"❌ エンジンが見つかりません。\n  パス: {ENGINE_PATH}")
        return

    # (4) USIで初期化
    send_command(engine, "usi")
    wait_for(engine, "usiok")

    # (5) 評価ファイルフォルダ (相対パスで指定する)
    # 例: エンジンと同じフォルダ内に "eval" フォルダがある場合
    EVAL_DIR = "eval"
    send_command(engine, f"setoption name EvalDir value {EVAL_DIR}")

    # 定跡ファイル不要なら
    send_command(engine, "setoption name USI_OwnBook value false")

    # ハッシュサイズなど任意設定
    send_command(engine, "setoption name USI_Hash value 256")

    # オプション適用の完了を待つ
    send_command(engine, "isready")
    wait_for(engine, "readyok")
    print("✅ エンジンの初期化完了")

    # (6) 変換後の棋譜を読み込ませる
    send_command(engine, position_cmd)

    # (7) 探索開始
    send_command(engine, "go")

    while True:
        line = engine.stdout.readline().rstrip("\n")
        if not line:
            break
        print("🔹", line)
        if "bestmove" in line:
            # bestmoveが返ってきたら探索終了とみなす
            break

    # (8) エンジン終了
    send_command(engine, "quit")
    engine.wait()
    print("✅ エンジンとのやり取り終了")

if __name__ == "__main__":
    main()
