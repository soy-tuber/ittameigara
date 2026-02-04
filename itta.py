import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO
import re

# 1. ページ設定
st.set_page_config(page_title="JP-Stock Scanner", layout="wide")

# カスタムCSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stDataFrame { border: 1px solid #e6e9ef; }
    h1 { color: #2c3e50; border-left: 8px solid #3498db; padding-left: 15px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧊 ittameigara")

# 2. サイドバー
with st.sidebar:
    st.header("🔍 Filter")
    # 市場の表記揺れ（東P, 東Gなど）に対応
    market_map = {"プライム": "東Ｐ", "スタンダード": "東Ｓ", "グロース": "東Ｇ"}
    selected_display = st.multiselect("表示する市場", list(market_map.keys()), default=list(market_map.keys()))
    selected_markets = [market_map[m] for m in selected_display]

# 3. メイン：データ入力
st.subheader("📥 データ入力")
raw_data = st.text_area("証券ツールのリストをコピペしてください", height=150, placeholder=' "No" "コード" "銘柄名" ... ')

if raw_data:
    try:
        # 文字列のクレンジング：引用符を処理し、タブかカンマを自動判定
        # 一旦StringIOで読み込み
        df = pd.read_csv(StringIO(raw_data), sep=None, engine='python', quotechar='"')

        # 【数値クレンジング関数】
        def clean_stock_value(x):
            if pd.isna(x): return 0.0
            s = str(x)
            # 記号の置換：▲や▼をマイナスとして扱う
            s = s.replace('▲', '-').replace('▼', '-').replace('%', '').replace(',', '')
            # 余計な文字を排除して数値へ
            try:
                # 連続するマイナスなどはre.subで整理
                s = re.sub(r'[^\d\.\-]', '', s)
                return float(s)
            except:
                return 0.0

        # カラムの自動特定
        name_col = next((c for c in df.columns if "銘柄名" in c), df.columns[3])
        ratio_col = next((c for c in df.columns if "比率" in c), None)
        market_col = next((c for c in df.columns if "市場" in c), None)

        if ratio_col:
            # 騰落率の数値化
            df['clean_ratio'] = df[ratio_col].apply(clean_stock_value)
            
            # 市場フィルタリング
            if market_col and selected_markets:
                df = df[df[market_col].isin(selected_markets)]

            # 下落銘柄のみ抽出
            dead_df = df[df['clean_ratio'] < 0].sort_values('clean_ratio')

            if not dead_df.empty:
                # 4. 可視化
                st.subheader(f"📊 絶望の可視化（下落 {len(dead_df)} 銘柄）")
                
                # ツリーマップ
                fig = px.treemap(
                    dead_df,
                    path=[market_col, name_col] if market_col else [name_col],
                    values=dead_df['clean_ratio'].abs(), # 大きさは下落率の絶対値
                    color='clean_ratio',
                    color_continuous_scale='Blues_r', # 深い青
                    range_color=[dead_df['clean_ratio'].min(), 0],
                    hover_data={ratio_col: True, 'clean_ratio': False}
                )
                fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
                st.plotly_chart(fig, use_container_width=True)

                # 5. リスト表示
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.subheader("📉 逝った順ランキング")
                    # 表示用に整形
                    display_df = dead_df.drop(columns=['clean_ratio'])
                    st.dataframe(display_df, use_container_width=True, hide_index=True)

                with col2:
                    st.subheader("🤳 SNSあおり用生成器")
                    worst = dead_df.iloc[0]
                    avg_loss = dead_df['clean_ratio'].mean()
                    
                    st.code(
                        f"今日もお疲れ様です。\n"
                        f"本日の地獄絵図：\n"
                        f"・ワースト：{worst[name_col]} ({worst[ratio_col]})\n"
                        f"・下落銘柄平均：{avg_loss:.2f}%\n\n"
                        f"爽やかな青が目に染みますね...。 #日本株 #含み損 #お通夜",
                        language="text"
                    )
            else:
                st.success("✨ 下落銘柄はありません。全銘柄プラスです！")
        else:
            st.warning("「前日比率」カラムが見つかりませんでした。ヘッダーを含めてコピーしてください。")

    except Exception as e:
        st.error(f"データ解析に失敗しました。形式を確認してください。\nError: {e}")
else:
    st.info("証券サイトのデータをここに貼り付けてください（例：TIS, イビデン...）")