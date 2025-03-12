from dotenv import load_dotenv  # .env を読み込むライブラリ
import os  # 環境変数を扱うための標準ライブラリ

# .env ファイルを読み込む
load_dotenv()

# APIキーを取得
api_key = os.getenv("OPENAI_API_KEY")

# 確認のためにAPIキーを表示（※セキュリティのため、実際の運用では表示しない）
print("APIキー:", api_key)
