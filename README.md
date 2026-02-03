# 賢声 (Kensei)

Windows用の常駐型・高速日本語音声入力アプリです。

## 特徴

- **音声認識**: faster-whisper による高速な文字起こし
- **AI整形**: llama.cpp によるローカルLLMでの文章修正
- **操作**: 左Ctrlキーで入力、右Ctrlキーで修正指示
- **出力**: クリップボード経由で任意のアプリに貼り付け

## インストール

```bash
pip install -r requirements.txt
```

## 起動

```bash
python main.py
```
