import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.similarity import TextSimilarity

def test_auto_detection():
    print("=== Phase 3: 自動判定ロジックのテスト ===")

    # シナリオ1: 全く違う話をした場合（新規入力）
    clip_text_1 = "昨日の晩御飯はカレーでした。"
    voice_text_1 = "明日の会議の資料を作成してください。"
    
    sim_1 = TextSimilarity.calculate(clip_text_1, voice_text_1)
    is_fix_1 = TextSimilarity.is_correction(clip_text_1, voice_text_1)
    
    print(f"\n[Case 1] 全く違う内容")
    print(f"  Clipboard: {clip_text_1}")
    print(f"  Voice:     {voice_text_1}")
    print(f"  Similarity: {sim_1:.2f}")
    print(f"  判定: {'【修正指示】' if is_fix_1 else '【新規入力】'} -> 正解は【新規入力】")

    # シナリオ2: 直前の内容を修正した場合（学習対象）
    clip_text_2 = "彼は、早く走る。"
    voice_text_2 = "彼は速く走る。"
    
    sim_2 = TextSimilarity.calculate(clip_text_2, voice_text_2)
    is_fix_2 = TextSimilarity.is_correction(clip_text_2, voice_text_2)
    
    print(f"\n[Case 2] 微修正（学習チャンス！）")
    print(f"  Clipboard: {clip_text_2}")
    print(f"  Voice:     {voice_text_2}")
    print(f"  Similarity: {sim_2:.2f}")
    print(f"  判定: {'【修正指示】' if is_fix_2 else '【新規入力】'} -> 正解は【修正指示】")

if __name__ == "__main__":
    test_auto_detection()