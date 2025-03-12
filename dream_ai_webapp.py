import streamlit as st
import openai
from PIL import Image
import requests
from io import BytesIO
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import time

# .envファイルからAPIキーを読み込む
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# セッション状態の初期化
if 'history' not in st.session_state:
    st.session_state.history = []
if "selected_image_index" not in st.session_state:
    st.session_state.selected_image_index = None
if "image_urls" not in st.session_state:
    st.session_state.image_urls = []

# サイドバーに履歴表示
st.sidebar.title("💭 夢占い履歴")
if len(st.session_state.history) > 0:
    for idx, entry in enumerate(st.session_state.history):
        with st.sidebar.expander(f"夢占い {entry['date']}"):
            st.write(f"夢の内容: {entry['dream']}")
            if 'emotions' in entry:
                st.write(f"感情: {entry['emotions']}")
            st.image(entry['image_url'], use_container_width=True)
            st.write(f"解釈: {entry['interpretation']}")

st.title("🌙 AI夢占い - あなたの夢を画像で再現")

# ユーザーが夢を入力
dream_text = st.text_area(
    "あなたの夢の内容を入力してください",
    placeholder="例：『曇り空、湖、木の橋、現実的』"
)

# 感情入力セクション
st.subheader("😊 夢の中での感情")
col1, col2 = st.columns(2)

with col1:
    # 主要な感情の選択（複数選択可能）
    primary_emotions = st.multiselect(
        "主な感情を選択してください（複数選択可能）",
        ["喜び", "悲しみ", "怒り", "恐れ", "不安", "驚き", "安心", "期待", "困惑"],
        help="夢の中で感じた主な感情を選択してください"
    )

with col2:
    # 感情の強さをスライダーで選択
    emotion_intensity = st.slider(
        "感情の強さ",
        1, 10, 5,
        help="1: とても弱い, 10: とても強い"
    )

# 追加の感情メモ
additional_emotions = st.text_area(
    "その他の感情や感情の変化について",
    placeholder="例：最初は不安でしたが、だんだん安心感が増してきました",
    help="感情の変化や、選択肢にない感情があれば記入してください"
)

# ユーザーが占いのスタイルを選択
interpretation_style = st.radio(
    "占いのスタイルを選んでください",
    ["スピリチュアル", "心理学的"]
)

def generate_diverse_prompts(dream_text):
    """写実的な視点から3つの異なるプロンプトを生成"""
    system_prompt = """
    あなたは画像生成のプロンプト作成の専門家です。
    同じ夢の内容から、3つの異なる写実的な視点でプロンプトを作成してください。
    以下の点に注意してください：

    1. すべてのプロンプトは写実的で現実的な表現を使用
    2. 各プロンプトで以下の要素を変えることで違いを出す：
       - 時間帯（朝、昼、夕方、夜など）
       - 天候（晴れ、曇り、雨上がり、霧など）
       - 視点（近景、中景、遠景）
       - 季節感（春、夏、秋、冬）
    3. 各プロンプトには必ず以下を含めてください：
       - "photorealistic"
       - "highly detailed"
       - "4k"
       - "natural lighting"
    
    結果は、同じ場面の異なる写実的な解釈となるようにしてください。
    """
    
    prompt = f"以下の夢の内容から、3つの異なる写実的なプロンプトを作成してください：\n{dream_text}"
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    
    # レスポンスから3つのプロンプトを抽出
    prompts = response.choices[0].message.content.strip().split('\n\n')
    return [p.split(': ')[-1] for p in prompts if p][:3]

if st.button("夢を解析して画像を生成"):
    with st.spinner("夢を分析中..."):
        # 進捗バーの表示
        progress_bar = st.progress(0)
        progress_text = st.empty()
        
        # プロンプト生成（33%まで）
        progress_text.text("プロンプトを生成中...")
        diverse_prompts = generate_diverse_prompts(dream_text)
        progress_bar.progress(33)
        
        # DALL·E 3 で画像を生成（33%から100%まで）
        st.session_state.image_urls = []
        for i, prompt in enumerate(diverse_prompts):
            progress_text.text(f"画像を生成中... ({i+1}/3)")
            image_response = openai.Image.create(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            st.session_state.image_urls.append(image_response["data"][0]["url"])
            # 進捗バーの値を33%から100%の間で均等に配分
            progress_bar.progress(33 + ((i + 1) * 22))  # 33, 55, 77, 100
        
        progress_text.text("生成完了！")
        time.sleep(1)
        progress_text.empty()
        progress_bar.empty()

# 画像を横並びで表示して選択させる
if st.session_state.image_urls:
    st.subheader("🖼 生成された画像の中から、最も夢のイメージに合うものを選んでください")
    
    # 3列のレイアウトを作成
    cols = st.columns(3)
    
    # 各画像を表示
    for idx, (col, image_url) in enumerate(zip(cols, st.session_state.image_urls)):
        with col:
            st.image(image_url, use_container_width=True)
            
            # 画像の保存ボタン
            if st.download_button(
                f"画像を保存 #{idx + 1}",
                data=requests.get(image_url).content,
                file_name=f"dream_image_{idx+1}.png",
                mime="image/png"
            ):
                st.success(f"画像 #{idx + 1} を保存しました！")
            
            if st.button(f"この画像を選択 #{idx + 1}", key=f"select_image_{idx}"):
                st.session_state.selected_image_index = idx
                st.rerun()

# 選択された画像がある場合、夢占い結果を表示
if hasattr(st.session_state, 'selected_image_index') and st.session_state.selected_image_index is not None:
    selected_url = st.session_state.image_urls[st.session_state.selected_image_index]
    
    with st.spinner("夢占いの結果を生成中..."):
        meaning_prompt = f"""
        あなたは{interpretation_style}な夢占いの専門家です。
        以下の夢の内容と感情について、JSONフォーマットで解釈を提供してください。
        各セクションには具体的で詳細な説明を含めてください。

        夢: {dream_text}

        感情情報:
        - 主な感情: {', '.join(primary_emotions)}
        - 感情の強さ: {emotion_intensity}/10
        - 追加の感情詳細: {additional_emotions}

        必要なフォーマット:
        {{
            "symbolic_meaning": "夢の象徴的な意味の詳細な説明（感情の影響を含む）",
            "psychological_interpretation": "心理学的な解釈の詳細な説明（感情との関連を含む）",
            "key_symbols": ["重要なシンボル1とその意味", "重要なシンボル2とその意味", "重要なシンボル3とその意味"],
            "emotional_analysis": "感情が示唆する深層心理の分析",
            "future_advice": "具体的なアドバイスや提案",
            "positive_aspects": "夢から読み取れるポジティブな側面",
            "points_to_consider": "注意や意識すべきポイント"
        }}
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは夢占いの専門家です。JSONフォーマットで詳細な解釈を提供してください。"},
                {"role": "user", "content": meaning_prompt}
            ]
        )

        try:
            # JSONレスポンスをパース
            dream_meaning = json.loads(response.choices[0].message.content.strip())
            
            # 結果表示用のカードを作成
            st.subheader("✨ あなたが選んだ夢のイメージ")
            st.image(selected_url, use_container_width=True)
            
            st.subheader("🔮 夢の意味（占い結果）")
            
            # タブで結果を分類
            tab1, tab2, tab3, tab4 = st.tabs(["象徴と解釈", "感情分析", "重要なシンボル", "アドバイス"])
            
            with tab1:
                # 象徴的な意味と心理学的解釈
                with st.expander("🌟 夢の象徴的な意味", expanded=True):
                    st.write(dream_meaning["symbolic_meaning"])
                
                with st.expander("🧠 心理学的な解釈", expanded=True):
                    st.write(dream_meaning["psychological_interpretation"])
            
            with tab2:
                # 感情分析の表示
                st.markdown("### 💭 感情分析")
                st.write(dream_meaning["emotional_analysis"])
                
                # 感情情報の視覚的表示
                st.markdown("### 📊 感情データ")
                if primary_emotions:
                    emotions_str = ", ".join(primary_emotions)
                    st.info(f"主な感情: {emotions_str}")
                    st.progress(emotion_intensity/10)
                    st.caption(f"感情の強さ: {emotion_intensity}/10")
                if additional_emotions:
                    st.write("追加の感情メモ:", additional_emotions)
            
            with tab3:
                # 重要なシンボルをカードで表示
                st.write("✨ 重要なシンボルとその意味")
                cols = st.columns(len(dream_meaning["key_symbols"]))
                for idx, (col, symbol) in enumerate(zip(cols, dream_meaning["key_symbols"])):
                    with col:
                        st.markdown(f"""
                            <div style='padding: 1rem; border-radius: 0.5rem; background-color: #f0f2f6; text-align: center;'>
                                <div style='font-size: 1.2rem; font-weight: bold; margin-bottom: 0.5rem;'>シンボル {idx + 1}</div>
                                <div>{symbol}</div>
                            </div>
                        """, unsafe_allow_html=True)
            
            with tab4:
                # アドバイスと注意点
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 💫 ポジティブな側面")
                    st.write(dream_meaning["positive_aspects"])
                    
                    st.markdown("### 🎯 具体的なアドバイス")
                    st.write(dream_meaning["future_advice"])
                
                with col2:
                    st.markdown("### ⚠️ 意識すべきポイント")
                    st.write(dream_meaning["points_to_consider"])
            
            # 結果を履歴に保存
            interpretation_text = f"""
            象徴的な意味: {dream_meaning['symbolic_meaning']}
            心理学的な解釈: {dream_meaning['psychological_interpretation']}
            感情分析: {dream_meaning['emotional_analysis']}
            アドバイス: {dream_meaning['future_advice']}
            """
            
            st.session_state.history.append({
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'dream': dream_text,
                'emotions': {
                    'primary': primary_emotions,
                    'intensity': emotion_intensity,
                    'additional': additional_emotions
                },
                'image_url': selected_url,
                'interpretation': interpretation_text
            })

            # SNS共有リンク
            st.divider()
            st.subheader("🔗 結果をシェア")

            # 画像と占い結果のシェアを2列に分ける
            share_col1, share_col2 = st.columns(2)

            with share_col1:
                st.write("📸 画像をシェア")
                st.write(f"[Twitterでシェア](https://twitter.com/intent/tweet?text=私の夢をAIが画像化しました！&url={selected_url})")

            with share_col2:
                st.write("🔮 占い結果をシェア")
                # 占い結果の要約を作成
                summary = f"""私の夢を #AI占い で解析してもらいました！

🌟象徴的な意味：{dream_meaning['symbolic_meaning'][:50]}...

✨ポジティブな側面：{dream_meaning['positive_aspects'][:50]}...

#夢占い #AI"""
                
                # URLエンコードしてシェアリンク作成
                encoded_summary = requests.utils.quote(summary)
                st.write(f"[Twitterでシェア](https://twitter.com/intent/tweet?text={encoded_summary})")

            # オプション：両方をまとめてシェアするボタン
            st.write("✨ 画像と占い結果を一緒にシェア")
            combined_summary = f"""私の夢を #AI占い で解析してもらいました！

🌟象徴的な意味：{dream_meaning['symbolic_meaning'][:50]}...

✨画像：{selected_url}

#夢占い #AI"""
            encoded_combined = requests.utils.quote(combined_summary)
            st.write(f"[Twitterで全てをシェア](https://twitter.com/intent/tweet?text={encoded_combined})")

        except json.JSONDecodeError:
            st.error("結果の解析中にエラーが発生しました。もう一度お試しください。")