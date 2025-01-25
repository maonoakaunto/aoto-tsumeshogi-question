import subprocess

# USIエンジンのパス
engine_path = "C:\\shogi\\engine\\YaneuraOu.exe"

# エンジンを起動
engine = subprocess.Popen(engine_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

def send_command(cmd):
    """エンジンにコマンドを送る"""
    engine.stdin.write(cmd + "\n")
    engine.stdin.flush()

def read_output():
    """エンジンの出力を読み取る"""
    while True:
        line = engine.stdout.readline().strip()
        print(line)
        if "bestmove" in line or "checkmate" in line:
            return line

# USIエンジンを起動
send_command("usi")
send_command("isready")
read_output()

# 詰将棋の局面をセット（ここは適宜変更）
tsume_position = "position sfen 7k/9/9/9/9/9/9/9/4K4 b R2G2N2S3L4P 1"
send_command(tsume_position)

# 詰み手順を探索
send_command("go mate 10")  # 10手以内で詰み探索
result1 = read_output()

send_command("go mate 10")  # もう一度別の手順を探索
result2 = read_output()

# 異なる詰み筋があるか判定
if result1 != result2:
    print("余詰めの可能性あり")
else:
    print("唯一の詰み手順")
    
# エンジンを終了
send_command("quit")
engine.terminate()