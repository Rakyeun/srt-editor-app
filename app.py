# app.py

import streamlit as st
import google.generativeai as genai
import re
import json

# --- Core Functions (Colab 코드와 거의 동일) ---

def generate_edit_guide(srt_text, edit_topic, api_key):
    """
    Gemini API를 사용하여 SRT 내용과 주제를 기반으로 편집 가이드를 생성합니다.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
    except Exception as e:
        st.error(f"API 키 설정에 실패했습니다. 올바른 키인지 확인해주세요. 오류: {e}")
        return None

    prompt = f"""
    당신은 전문 영상 편집 조수입니다. 당신의 임무는 주어진 SRT 자막 스크립트와 특정 '주제'를 분석하여, 주제와 가장 관련이 깊은 대사(문장 또는 구절)를 원본에서 그대로 추출하는 것입니다.
    **지시사항:**
    1. 주어진 'SRT 스크립트' 전체를 읽고 내용의 맥락을 파악하세요.
    2. 주어진 '편집 주제'에 가장 부합하는 핵심적인 문장이나 구절을 500자 내외로 추려내세요.
    3. 추가적인 단어를 생성하거나 문장을 변형하지 마세요. 반드시 원본 스크립트에 있는 표현 그대로 추출해야 합니다.
    4. 추출된 대사들은 시간 순서대로 정렬되어야 합니다. (발화자는 구분하지만 타임코드는 제외)
    5. 결과는 반드시 아래의 JSON 형식으로 반환해야 합니다. 어떠한 설명이나 추가 텍스트 없이 JSON 객체만 응답해야 합니다.
    **JSON 출력 형식:**
    {{
      "selected_texts": ["추출한 첫 번째 대사", "추출한 두 번째 대사", "..."]
    }}
    ---
    **실제 분석 요청**
    **SRT 스크립트:**
    '''
    {srt_text}
    '''
    **편집 주제:** "{edit_topic}"
    """

    try:
        response = model.generate_content(prompt)
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        result = json.loads(json_response_text)
        selected_texts = result.get("selected_texts", [])
        
        if not selected_texts:
            st.warning("Gemini가 주제에 맞는 대사를 찾지 못했습니다. 주제를 변경하거나 원본 SRT를 확인해보세요.")
            return None
            
        return selected_texts
        
    except Exception as e:
        st.error(f"Gemini API 호출 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요. 오류 상세: {e}")
        return None

def create_guide_srt(original_srt, selected_phrases):
    """
    추출된 대사를 원본 SRT에 '[ ]'로 표시하여 가이드 SRT를 생성합니다.
    """
    guide_srt = original_srt
    for phrase in selected_phrases:
        escaped_phrase = re.escape(phrase)
        guide_srt = re.sub(escaped_phrase, f"[{phrase}]", guide_srt)
    return guide_srt

# --- Streamlit Web App Interface ---

st.set_page_config(page_title="편집 가이드 SRT 생성기", page_icon="🎬")

st.title("🎬 Gemini AI 영상 편집 가이드 생성기")
st.markdown("---")
st.markdown("""
원본 영상의 SRT 자막 파일과 편집 주제를 입력하면, Gemini AI가 주제에 맞는 대사를 선별하여 **편집 대본**과 **편집 가이드 SRT 파일**을 만들어 드립니다.
""")

# API 키 입력 (사이드바에 배치)
st.sidebar.header("API 키 설정")
api_key_input = st.sidebar.text_input(
    "Gemini API 키를 입력하세요.", 
    type="password",
    help="Google AI Studio에서 발급받은 API 키를 입력해주세요. 입력된 키는 저장되지 않습니다."
)

st.markdown("---")

# 1. 파일 업로드
uploaded_file = st.file_uploader("1. 원본 SRT 자막 파일을 업로드하세요.", type=['srt'])

# 2. 주제 입력
topic = st.text_input("2. 영상 편집의 주제를 입력하세요.", placeholder="예: 경주 apec (아펙)을 준비하면서 우려하는 점들")

# 3. 생성 버튼
if st.button("✨ 편집 가이드 생성하기"):
    if not api_key_input:
        st.warning("⚠️ Gemini API 키를 입력해주세요.")
    elif uploaded_file is None:
        st.warning("⚠️ SRT 파일을 업로드해주세요.")
    elif not topic:
        st.warning("⚠️ 편집 주제를 입력해주세요.")
    else:
        # 모든 입력이 완료되었을 때 로직 실행
        with st.spinner("Gemini AI가 대본을 분석하고 있습니다... 잠시만 기다려주세요."):
            # 파일 읽기
            srt_content = uploaded_file.getvalue().decode("utf-8")
            
            # 핵심 기능 호출
            selected_phrases = generate_edit_guide(srt_content, topic, api_key_input)
            
            if selected_phrases:
                # 결과 생성
                edited_script_txt = " ".join(selected_phrases)
                edit_guide_srt = create_guide_srt(srt_content, selected_phrases)
                
                st.success("🎉 작업이 완료되었습니다! 아래 결과를 확인하고 다운로드하세요.")
                
                # 결과 출력
                st.subheader("📄 편집 대본 (TXT)")
                st.text_area("편집 대본", edited_script_txt, height=150)
                st.download_button(
                    label="📥 편집 대본 다운로드 (.txt)",
                    data=edited_script_txt.encode('utf-8'),
                    file_name="edited_script.txt",
                    mime="text/plain"
                )

                st.subheader("🎬 편집 가이드 (SRT)")
                st.text_area("편집 가이드", edit_guide_srt, height=300)
                st.download_button(
                    label="📥 편집 가이드 다운로드 (.srt)",
                    data=edit_guide_srt.encode('utf-8'),
                    file_name="edit_guide.srt",
                    mime="text/plain"
                )
