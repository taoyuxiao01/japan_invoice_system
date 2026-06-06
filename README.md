# 日本のレシートAI抽出システム

## サマリー
### **プロジェクト概要**

- 日本のレシート AI 抽出システムは、完全にローカル環境で動作する自動財務データ抽出ツールです。

### **デモ画面 (Demo)**

- 以下はシステムの実際の動作と抽出プロセスのデモです：

![Japan Invoice Extraction System Demo](./assets/choose_pic.gif)

![Japan Invoice Extraction System Demo](./assets/recognization.gif)

### **開発の背景**

- 本プロジェクトは、友人の実際の副業における課題から生まれました。彼女は毎日、フォーマットが異なる数十から数百枚に及ぶ日本のレシートを処理する必要がありました。この膨大な作業量を軽減しつつ、機密性の高い財務データの漏洩リスクを完全に排除するために本システムは開発されました。

### **技術の進化とパフォーマンス**

- 日本のレシート特有の複雑なレイアウト、テキストのズレ、印鑑による文字の隠れなどの問題に対し、初期段階では PaddleOCR などの従来の OCR 技術を試みましたが、十分な精度が得られませんでした。そこで、コアアーキテクチャを当時最新のマルチモーダル・ビジョンモデル（VLM）である Qwen3.5シリーズ に切り替えました。
- テストの結果、RTX 5060Ti 16GB の GPU 環境にて 9B モデルを使用した場合、元画像の解析処理はわずか 約5秒 で完了します。さらに、プロンプト（Prompt）エンジニアリングによる出力の制約により、期待通りの JSON 形式でデータを安定的かつ高速に出力することが可能になりました。

### **主な機能と特徴**

- **100% ローカル処理**：Ollama を活用し、データの抽出・処理プロセスをすべてローカルで実行します。機密性の高い財務データがクラウドに送信されるリスクは一切ありません。

- **ヒューマン・イン・ザ・ループ**：Excel にデータを保存する前に、画面上での手動確認と修正を必須とすることで、100%の正確性を確保します。

- **モダンな分離アーキテクチャ**：軽量なバックエンド（FastAPI）が画像の圧縮とモデルの推論を効率的に処理し、インタラクティブなフロントエンド（Streamlit）が直感的な表編集体験を提供します。



[English Version](#english-version) | [日本語版](#日本語版)

---

<h2 id="english-version">English Version</h2>

This is a local, automated invoice and receipt data extraction system. It uses a Vision-Language Model (VLM) instead of traditional OCR to handle complex Japanese receipt layouts, misaligned text, and stamp occlusions. It also includes a Human-in-the-Loop (HITL) verification step before saving data to an Excel database.

### Features
- **Vision-Based Extraction**: Uses edge VLMs to understand document layouts directly from images, bypassing the need for complex OCR pipeline tuning.
- **Human-in-the-Loop (HITL)**: Flags uncertain extractions (e.g., blurry images or math discrepancies) and forces a manual review in the UI before the data can be saved.
- **Local Processing**: Powered by Ollama. The entire pipeline runs locally, ensuring that sensitive financial data is never sent to the cloud.
- **Decoupled Architecture**: A lightweight FastAPI backend handles image compression and model inference, while a Streamlit frontend provides an interactive, editable dataframe.

### Tech Stack
- **Frontend**: Streamlit
- **Backend**: FastAPI, Uvicorn
- **AI Engine**: Ollama
- **Core Model**: qwen3.5:35b-a3b-q4_K_M
- **Data Storage**: Pandas, Openpyxl

### Quick Start
**1. Prerequisites**
- Python 3.12
- Ollama installed and running.
- Pull the local vision model:
```bash
ollama run qwen3.5:35b-a3b-q4_K_M
```
**2. Installation**

It is recommended to use a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**3. Run the system**

Execute the main script in the project root:
    
```bash
python run.py
```

The system will start the backend and frontend automatically.

Access the UI at http://localhost:8501.



<h2 id="japanese-version">日本語版</h2>

これは、ローカルで動作する請求書および領収書データの自動抽出システムです。従来のOCRとは異なり、本プロジェクトでは視覚言語モデル（VLM）を使用して画像内容を直接理解します。これにより、日本の請求書によく見られる複雑なレイアウト、テキストのズレ、印鑑による文字の隠れなどの問題に適切に対処できます。また、データをExcelに書き込む前に、システムはヒューマン・イン・ザ・ループ（HITL）による手動検証プロセスを提供し、データの正確性を確保します。

### 主な機能
- **ビジョンベースの抽出**：VLMを使用して画像から直接ドキュメントの構造を理解するため、複雑なOCRのパラメータ調整は不要です。
- **手動検証（HITL）**：不確実な抽出結果（不鮮明な画像や金額の不一致など）をフラグ付けし、保存する前に手動での確認を必須とします。
- **ローカル処理**：Ollamaを活用し、すべての処理をローカルで実行します。機密性の高い財務データがクラウドに送信されることはありません。
- **分離アーキテクチャ**：軽量なFastAPIバックエンドが画像の圧縮とモデルの推論を担当し、Streamlitフロントエンドがインタラクティブで編集可能なデータインターフェースを提供します。

### 技術スタック
- **フロントエンド**：Streamlit
- **バックエンド**：FastAPI, Uvicorn
- **AI エンジン**：Ollama
- **コアモデル**：qwen3.5:35b-a3b-q4_K_M
- **データストレージ**：Pandas, Openpyxl

### クイックスタート
**1. 前提条件**
- Python 3.12
- Ollamaがインストールされ、実行されていること。
- ローカルのビジョンモデルをプルします：
```bash
ollama run qwen3.5:35b-a3b-q4_K_M
```
**2. インストール**

- 仮想環境の使用を推奨します：
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**3. システムの起動**

プロジェクトのルートディレクトリでメインスクリプトを実行します：
    
```bash
python run.py
```

システムは自動的にバックエンドとフロントエンドを起動します。ブラウザから http://localhost:8501 にアクセスしてください。