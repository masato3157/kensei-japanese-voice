"""
Ollama API プロンプト最適化テスト

目的：
    LFM 2.5-1.2B-JP モデルで漢字変換の精度を高めるため、
    複数のプロンプトを比較検証する。

使用方法：
    python test_ollama_lfm.py
"""

import ollama


# 使用するモデル名
MODEL_NAME = "hf.co/LiquidAI/LFM2.5-1.2B-JP-GGUF"

# 検証するプロンプト一覧
PROMPTS = [
    {
        "id": 1,
        "name": "書記官パターン",
        "content": (
            "あなたは優秀な書記官です。"
            "以下のひらがな混じりの文章を、文脈に沿って適切な漢字に変換し、"
            "句読点を補って読みやすい日本語に直してください。"
            "出力は整形後の文章のみとしてください。"
        )
    },
    {
        "id": 2,
        "name": "同音異義語パターン",
        "content": (
            "以下の音声認識結果を修正してください。"
            "特に、同音異義語の誤字を文脈から判断して正しい漢字に変換することに注力してください。"
            "余計な解説は一切不要です。"
        )
    },
    {
        "id": 3,
        "name": "シンプル変換パターン",
        "content": (
            "入力された日本語の、漢字変換と句読点の挿入のみを行ってください。"
            "文章の意味は変えず、表記のみを整えてください。"
        )
    }
]

# テスト入力文
TEST_INPUTS = [
    "きょうはいいてんきですねこしつにいきます",
    "きのうはよつがひどくてしごとをやすみました"
]


def call_llm(prompt: str, user_input: str) -> str:
    """
    LFM に問い合わせを行い、整形結果を返す。
    
    Args:
        prompt: システムプロンプト
        user_input: ユーザー入力（整形対象の文章）
    
    Returns:
        LFM からの応答テキスト
    """
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input}
            ]
        )
        return response["message"]["content"].strip()
    except Exception as e:
        return "[エラー] " + str(e)


def run_comparison_test():
    """
    3種類のプロンプトと2つの入力文でテストを実行し、結果を比較する。
    """
    lines = []
    lines.append("=" * 60)
    lines.append("LFM 2.5 JP プロンプト最適化テスト")
    lines.append("=" * 60)
    lines.append("モデル: " + MODEL_NAME)
    lines.append("")
    
    # 結果を保存する辞書
    results = {}
    
    for prompt_info in PROMPTS:
        prompt_id = prompt_info["id"]
        prompt_name = prompt_info["name"]
        prompt_content = prompt_info["content"]
        
        lines.append("-" * 60)
        lines.append("プロンプト " + str(prompt_id) + ": " + prompt_name)
        lines.append("-" * 60)
        
        results[prompt_id] = []
        
        for test_input in TEST_INPUTS:
            lines.append("")
            lines.append("  [入力] " + test_input)
            
            # LFM に問い合わせ
            output = call_llm(prompt_content, test_input)
            results[prompt_id].append(output)
            
            lines.append("  [出力] " + output)
    
    # 結果サマリー
    lines.append("")
    lines.append("=" * 60)
    lines.append("結果サマリー")
    lines.append("=" * 60)
    
    # 期待される変換例を表示
    lines.append("")
    lines.append("[期待される変換例]")
    lines.append("  入力1: きょうはいいてんきですねこしつにいきます")
    lines.append("    期待: 今日はいい天気ですね。個室に行きます。")
    lines.append("  入力2: きのうはよつがひどくてしごとをやすみました")
    lines.append("    期待: 昨日は夜通しがひどくて仕事を休みました。")
    lines.append("")
    
    # 各プロンプトの結果を表形式で表示
    lines.append("[各プロンプトの結果]")
    for prompt_info in PROMPTS:
        prompt_id = prompt_info["id"]
        prompt_name = prompt_info["name"]
        lines.append("")
        lines.append("  プロンプト " + str(prompt_id) + " (" + prompt_name + "):")
        for i, output in enumerate(results[prompt_id]):
            lines.append("    入力" + str(i + 1) + " -> " + output)
    
    lines.append("")
    lines.append("=" * 60)
    lines.append("テスト完了")
    lines.append("=" * 60)
    
    # 結果をファイルに保存
    result_text = "\n".join(lines)
    with open("test_result.txt", "w", encoding="utf-8") as f:
        f.write(result_text)
    
    print("結果を test_result.txt に保存しました。")


if __name__ == "__main__":
    run_comparison_test()
