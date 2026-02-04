import os
from src.ai.corrector import TextCorrector

def test_integration():
    print("=== 統合テスト: 文脈理解の確認 ===")
    
    # 1. 初期化
    corrector = TextCorrector()
    print("[System] TextCorrector Initialized.")

    # 2. 最初の会話（情報を与える）
    input1 = "私の名前は「賢声（けんせい）」です。覚えておいてね。"
    print(f"\n[User 1] {input1}")
    result1 = corrector.correct(input1)
    print(f"[AI 1] {result1}")

    # 3. 次の会話（文脈を問う）
    input2 = "さて、私の名前は何でしたか？"
    print(f"\n[User 2] {input2}")
    result2 = corrector.correct(input2)
    print(f"[AI 2] {result2}")

    # 判定
    if "賢声" in result2 or "けんせい" in result2:
        print("\nSUCCESS: AIは文脈を理解しています！ ✅")
    else:
        print("\nFAILED: AIは名前を忘れてしまいました... ❌")

if __name__ == "__main__":
    test_integration()