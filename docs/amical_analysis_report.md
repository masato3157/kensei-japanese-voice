# Amical 技術分析レポート

Amicalの音声入力ノウハウを分析し、「賢声」への適用方針をまとめました。

---

## 1. 文脈の扱い (Context Management)

### Amicalの実装
Amicalでは`PipelineContext`というデータ構造に以下の情報を集約しています。

```python
# 賢声での実装イメージ (Pythonへの翻訳)
class PipelineContext:
    vocabulary: list[str]           # カスタム語彙（専門用語など）
    replacements: dict[str, str]   # テキスト置換ルール
    user_preferences: dict         # 言語、フォーマットスタイル
    accessibility_context: dict    # アクティブアプリ情報
```

### 賢声への適用案
- **アプリ検出**: Windowsでは`pywin32`の`GetForegroundWindow()`でアクティブなアプリ名を取得
- **プロファイル**: メール(Outlook)、チャット(Slack/Teams)、エディタ(VSCode)など用途別にプロンプトを切替
- **カスタム語彙**: ユーザーが登録した専門用語をプロンプトに注入し、誤認識を修正

---

## 2. 確定ロジック (VAD - Voice Activity Detection)

### Amicalの実装
Silero VAD v6 (ONNXモデル) を使用した音声区間検出。

| パラメータ | 値 | 意味 |
|------------|-----|------|
| `WINDOW_SIZE_SAMPLES` | 512 | 32msのフレームサイズ (16kHz) |
| `SPEECH_THRESHOLD` | 0.1 | 音声判定の閾値 (10%) |
| `REDEMPTION_FRAMES` | 8 | 無音が8フレーム続いたら発話終了 |

### 確定フロー
```
1. 音声確率 > 0.1 → speechFrameCount++
2. speechFrameCount >= 3 → 発話開始と判定
3. 音声確率 <= 0.1 → silenceFrameCount++
4. silenceFrameCount >= 8 → 発話終了と判定 → 確定処理へ
```

### 賢声への適用案 (Python版)
```python
import numpy as np
# Silero VADはPyTorchでも利用可能
# https://github.com/snakers4/silero-vad

class VADService:
    SPEECH_THRESHOLD = 0.1   # 音声判定閾値
    REDEMPTION_FRAMES = 8    # 確定までの無音フレーム数
    
    def __init__(self):
        self.speech_count = 0
        self.silence_count = 0
        self.is_speaking = False
    
    def process_frame(self, probability: float) -> bool:
        if probability > self.SPEECH_THRESHOLD:
            self.speech_count += 1
            self.silence_count = 0
        else:
            self.silence_count += 1
            if self.silence_count > self.REDEMPTION_FRAMES:
                self.speech_count = 0
        
        # 発話開始判定
        if not self.is_speaking and self.speech_count >= 3:
            self.is_speaking = True
        
        # 発話終了判定
        if self.is_speaking and self.silence_count >= self.REDEMPTION_FRAMES:
            self.is_speaking = False
        
        return self.is_speaking
```

---

## 3. プロンプト設計 (Formatter Prompt)

### Amicalのシステムプロンプト構造
```
You are a professional text formatter...

Custom vocabulary to use for corrections: {語彙リスト}

Instructions:
1. Fix any transcription errors based on context and custom vocabulary
2. Add proper punctuation and capitalization
3. Remove unnecessary filler words (um, uh, etc.)
4. [アプリタイプ別ルール]
5. Return ONLY the formatted text enclosed in <formatted_text></formatted_text> tags
```

### アプリタイプ別ルール
| タイプ | 適用ルール |
|--------|-----------|
| **email** | 挨拶・本文・結びの構造、署名保持 |
| **chat** | カジュアルなトーン維持、絵文字保持 |
| **notes** | 見出し・箇条書きで構造化 |
| **default** | 標準的な整形 |

### 賢声への適用案 (日本語版)
```python
SYSTEM_PROMPT_JA = """
あなたはプロのテキスト整形者です。音声認識されたテキストを、明確で読みやすく整えてください。

カスタム語彙（これらの用語は正確に使用してください）:
{vocabulary}

指示:
1. 文脈とカスタム語彙に基づいて認識ミスを修正する
2. 適切な句読点と改行を追加する
3. 「えーと」「あの」などのフィラー語を削除する
4. {app_type_rules}
5. 整形後のテキストのみを <formatted_text></formatted_text> タグで囲んで返す
6. 説明やコメントは一切含めない
"""
```

---

## 4. 賢声への統合ロードマップ

### Phase 1: 基本実装
- [ ] Silero VAD導入 (`pip install silero-vad torch`)
- [ ] 確定ロジックの実装 (REDEMPTION_FRAMES方式)

### Phase 2: 文脈対応
- [ ] アクティブウィンドウ検出 (`pywin32`)
- [ ] アプリタイプ別プロンプト切替

### Phase 3: カスタマイズ
- [ ] カスタム語彙登録UI
- [ ] 語彙のプロンプト注入

---

## 参考リンク
- [Silero VAD (GitHub)](https://github.com/snakers4/silero-vad)
- [Amical (GitHub)](https://github.com/amicalhq/amical)
