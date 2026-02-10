import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.memory import UserProfile, ContextManager

def test_memory():
    print("=== 1. 長期記憶 (UserProfile) テスト ===")
    profile = UserProfile()
    # デフォルト設定でのプロンプト生成を確認
    instruction = profile.get_instruction()
    print(f"[生成された指示文]\n{instruction}")
    print("-" * 30)

    print("\n=== 2. 短期記憶 (ContextManager) テスト ===")
    ctx = ContextManager()
    # 擬似的な会話を追加
    ctx.add_entry("京都の天気はどう？", "あいにくの雨です。")
    ctx.add_entry("明日は晴れるかな？", "予報では晴れですね。")
    
    # プロンプト生成を確認
    context_prompt = ctx.get_context_prompt()
    print(f"[生成された文脈プロンプト]\n{context_prompt}")
    print("-" * 30)

if __name__ == "__main__":
    test_memory()