# -*- coding: utf-8 -*-
"""
学習エンジン - ユーザーの修正から文体と単語を学習

このモジュールは、ユーザーが修正したテキストを分析し、
文体パラメータ（UserProfile）を自動調整し、
単語の誤りを辞書に登録する機能を提供します。
"""

import json
from typing import Optional, Dict, Any
from groq import Groq

from src.utils.config_loader import get_settings, is_api_key_configured
from src.utils.memory import UserProfile
from src.utils.dictionary import Dictionary


class LearningEngine:
    """
    ユーザーの修正から文体と単語を学習するエンジン
    
    責務:
    - AIの出力とユーザーの修正を比較
    - 文体パラメータの変動値を算出
    - UserProfileを自動更新
    - 単語の誤りを辞書に登録
    
    使用例:
        engine = LearningEngine()
        report = engine.learn(
            original_text="これは賢声のテストです",
            corrected_text="これは賢声のテストだよ",
            profile=user_profile,
            dictionary=dictionary
        )
        print(report)  # "学習完了: 硬さ -0.3, 辞書登録: よつう -> 腰痛"
    """
    
    # 学習プロンプトのテンプレート（単語誤り対応版）
    LEARNING_PROMPT = """あなたは文体分析と音声認識エラー検出の専門家です。

ユーザーは以下のテキストAをテキストBに修正しました。
この変更を2つの観点で分析してください。

【テキストA（修正前）】
{original_text}

【テキストB（修正後）】
{corrected_text}

【分析1: 文体パラメータの変動】
以下の5つのパラメータについて、変動値（-0.5〜+0.5）を算出してください。
- formality: 文体の硬さ（低い=口語的、高い=論文調）
- emotionality: 情緒レベル（低い=冷静、高い=感情的）
- assertiveness: 断定の強さ（低い=曖昧、高い=断定的）
- density: 情報密度（低い=簡潔、高い=詳細）
- vocabulary: 語彙レベル（低い=平易、高い=専門的）

【分析2: 音声認識の聞き間違い検出】
修正内容に「音は似ているが漢字や表記が違う」という明らかな聞き間違いがあれば、
それを `term_correction` として報告してください。
聞き間違いがなければ `null` としてください。

【回答形式】
以下のJSON形式で回答してください。JSONのみを出力し、他の説明は不要です。

{{
  "formality": 0.0,
  "emotionality": 0.0,
  "assertiveness": 0.0,
  "density": 0.0,
  "vocabulary": 0.0,
  "term_correction": null
}}

または、聞き間違いがある場合:

{{
  "formality": 0.0,
  "emotionality": 0.0,
  "assertiveness": 0.0,
  "density": 0.0,
  "vocabulary": 0.0,
  "term_correction": {{
    "wrong_word": "間違った単語",
    "correct_word": "正しい単語"
  }}
}}"""

    def __init__(self, api_key: Optional[str] = None):
        """
        LearningEngineを初期化する
        
        Args:
            api_key: Groq APIキー（省略時はsettings.pyから読み込み）
        """
        self._settings = get_settings()
        self._api_key = api_key or self._settings.get("GROQ_API_KEY")
        self._client: Optional[Groq] = None
        
        self._init_client()
        
    def _init_client(self) -> None:
        """Groqクライアントを初期化する"""
        if not is_api_key_configured(self._settings):
            raise ValueError("Groq APIキーが設定されていません。")
            
        self._client = Groq(api_key=self._api_key)
        print(f"[LearningEngine] 初期化完了")
        
    def learn(
        self,
        original_text: str,
        corrected_text: str,
        profile: UserProfile,
        dictionary: Optional[Dictionary] = None
    ) -> str:
        """
        ユーザーの修正から学習し、プロファイルと辞書を更新する
        
        Args:
            original_text: AIが出力したテキスト（修正前）
            corrected_text: ユーザーが修正したテキスト（修正後）
            profile: 更新対象のUserProfile
            dictionary: 更新対象のDictionary（省略可）
            
        Returns:
            学習結果のレポートメッセージ
        """
        if self._client is None:
            return "[学習エラー] クライアントが初期化されていません"
            
        # テキストが同じ場合は学習不要
        if original_text.strip() == corrected_text.strip():
            return "[学習スキップ] 修正がありませんでした"
            
        try:
            # プロンプトを構築
            prompt = self.LEARNING_PROMPT.format(
                original_text=original_text,
                corrected_text=corrected_text
            )
            
            # Groq APIで分析
            response = self._client.chat.completions.create(
                model=self._settings.get("MODEL_NAME", "llama-3.3-70b-versatile"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=512,
            )
            
            # レスポンスを解析
            result_text = response.choices[0].message.content.strip()
            parsed = self._parse_response(result_text)
            
            if not parsed:
                return "[学習エラー] レスポンスの解析に失敗しました"
                
            reports = []
            
            # 文体パラメータを更新
            style_report = self._apply_style_deltas(profile, parsed)
            if style_report:
                reports.append(style_report)
                
            # 単語辞書を更新
            if dictionary is not None:
                term_report = self._apply_term_correction(dictionary, parsed)
                if term_report:
                    reports.append(term_report)
            
            if reports:
                return "[学習完了] " + ", ".join(reports)
            else:
                return "[学習完了] 有意な変動なし"
            
        except Exception as e:
            print(f"[LearningEngine] 学習エラー: {e}")
            return f"[学習エラー] {str(e)}"
            
    def _parse_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Groqのレスポンスを解析してJSON辞書に変換する
        
        Args:
            response_text: Groqからのレスポンステキスト
            
        Returns:
            パース結果の辞書、または解析失敗時はNone
        """
        try:
            # JSONを抽出（余分なテキストがある場合に対応）
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            
            if start == -1 or end == 0:
                print(f"[LearningEngine] JSON形式が見つかりません: {response_text}")
                return None
                
            json_text = response_text[start:end]
            data = json.loads(json_text)
            
            # 期待されるキーを確認
            expected_keys = ["formality", "emotionality", "assertiveness", "density", "vocabulary"]
            for key in expected_keys:
                if key not in data:
                    data[key] = 0.0
                else:
                    # 値を -0.5 〜 +0.5 の範囲に制限
                    data[key] = max(-0.5, min(0.5, float(data[key])))
                    
            return data
            
        except json.JSONDecodeError as e:
            print(f"[LearningEngine] JSON解析エラー: {e}")
            print(f"[LearningEngine] レスポンス: {response_text}")
            return None
            
    def _apply_style_deltas(self, profile: UserProfile, data: Dict[str, Any]) -> Optional[str]:
        """
        文体パラメータの変動値をプロファイルに適用する
        
        Args:
            profile: 更新対象のUserProfile
            data: パース結果の辞書
            
        Returns:
            変更レポート、または変更なしの場合None
        """
        changes = []
        current = profile.data
        new_values = {}
        
        style_keys = ["formality", "emotionality", "assertiveness", "density", "vocabulary"]
        
        for key in style_keys:
            delta = data.get(key, 0.0)
            if abs(delta) > 0.01:  # 微小な変動は無視
                old_value = getattr(current, key)
                new_value = max(1.0, min(5.0, old_value + delta))
                new_values[key] = new_value
                
                sign = "+" if delta > 0 else ""
                changes.append(f"{key} {sign}{delta:.1f}")
                
        if new_values:
            profile.update(**new_values)
            
        if changes:
            return ", ".join(changes)
        return None
            
    def _apply_term_correction(self, dictionary: Any, data: Dict[str, Any]) -> Optional[str]:
        """
        単語の誤りを辞書に登録する
        
        Args:
            dictionary: 更新対象のDictionary
            data: パース結果の辞書
            
        Returns:
            登録レポート、または登録なしの場合None
        """
        term_correction = data.get("term_correction")
        
        if term_correction is None:
            return None
            
        if not isinstance(term_correction, dict):
            return None
            
        wrong_word = term_correction.get("wrong_word", "")
        correct_word = term_correction.get("correct_word", "")
        
        if not wrong_word or not correct_word:
            return None
            
        # 辞書に登録
        if dictionary.add_word(wrong_word, correct_word):
            return f"辞書登録: {wrong_word} -> {correct_word}"
        else:
            return None
            
    def dispose(self) -> None:
        """リソースを解放する"""
        self._client = None
        print("[LearningEngine] リソース解放完了")


# ============================================
# モジュールテスト
# ============================================

if __name__ == "__main__":
    print("=== LearningEngine テスト ===")
    print()
    
    # APIキーチェック
    if not is_api_key_configured():
        print("エラー: Groq APIキーが設定されていません")
        exit(1)
        
    # 初期化
    engine = LearningEngine()
    profile = UserProfile()
    
    print(f"学習前のプロファイル: {profile.data}")
    print()
    
    # テストケース: 口語から敬語への修正
    original = "これすごいね！マジでやばいよ"
    corrected = "これは素晴らしいですね。非常に良いと思います。"
    
    print(f"修正前: {original}")
    print(f"修正後: {corrected}")
    print()
    
    report = engine.learn(original, corrected, profile)
    print(report)
    print()
    
    print(f"学習後のプロファイル: {profile.data}")
    
    engine.dispose()
    print("\nテスト終了")
