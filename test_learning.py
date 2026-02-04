from src.ai.corrector import TextCorrector
from src.utils.memory import UserProfile

def test_learning():
    print("=== Phase 2: 学習機能テスト ===")
    
    # 1. 初期状態の確認
    corrector = TextCorrector()
    profile = UserProfile()
    print(f"[Before] 現在の硬さ(Formality): {profile.data.formality}")

    # 2. 学習シナリオ
    # AIは「思うよ」と軽く言ったが、ユーザーは「考えられる」と硬く修正した想定
    original_text = "すごい結果が出たと思うよ。"
    corrected_text = "著しい成果が得られたと考えられる。"
    
    print(f"\n[Action] 修正を実行中...")
    print(f"  A (AI): {original_text}")
    print(f"  B (User): {corrected_text}")

    # 学習実行
    report = corrector.learn_from_correction(original_text, corrected_text)
    print(f"\n[Result] レポート: {report}")

    # 3. 結果確認
    # ファイルから再読み込みして、値が変わったか確認
    new_profile = UserProfile()
    print(f"[After]  学習後の硬さ(Formality): {new_profile.data.formality}")
    
    if new_profile.data.formality > profile.data.formality:
        print("\nSUCCESS: AIは「硬い文章」を好む傾向を学習しました！ 📈")
    else:
        print("\nFAILED: パラメータが変化していません... 📉")

if __name__ == "__main__":
    test_learning()