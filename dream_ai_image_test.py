import openai
import requests
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv

# .envファイルからAPIキーを読み込む
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI APIの設定
openai.api_key = OPENAI_API_KEY

def extract_keywords(dream_text):
    """ChatGPTを使って夢のキーワードを抽出する"""
    prompt = f"""
    以下の夢の内容から、重要なキーワードを3つ抽出してください。
    夢: "{dream_text}"
    キーワード:
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたは優秀な言語解析AIです。"},
            {"role": "user", "content": prompt}
        ]
    )
    return response["choices"][0]["message"]["content"].strip()

def generate_detailed_prompt(keywords):
    """キーワードから詳細な画像生成プロンプトを作成"""
    prompt_template = f"""
    あなたは優秀な画像生成アシスタントです。
    以下のキーワードを元に、DALL·E 3 に最適な詳細なプロンプトを作成してください。
    
    キーワード: {keywords}
    
    期待するプロンプト:
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたは画像生成のプロンプト作成に特化したAIです。"},
            {"role": "user", "content": prompt_template}
        ]
    )
    return response["choices"][0]["message"]["content"].strip()

def generate_dream_image(keywords):
    """DALL·E 3 を使って夢の画像を生成する"""
    detailed_prompt = generate_detailed_prompt(keywords)
    response = openai.Image.create(
        model="dall-e-3",
        prompt=detailed_prompt,
        n=1,
        size="1024x1024"
    )
    image_url = response["data"][0]["url"]
    return image_url

def download_and_show_image(image_url):
    """生成された画像をダウンロードして表示"""
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    img.show()

def main():
    """テスト実行用のメイン関数"""
    dream_text = input("あなたの夢の内容を入力してください: ")
    keywords = extract_keywords(dream_text)
    print(f"抽出されたキーワード: {keywords}")
    
    image_url = generate_dream_image(keywords)
    print(f"生成された画像URL: {image_url}")
    
    download_and_show_image(image_url)

if __name__ == "__main__":
    main()
