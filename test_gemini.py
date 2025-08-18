import os
from dotenv import load_dotenv
import google.generativeai as genai

# 환경 변수 로드
load_dotenv()

def test_gemini_api():
    """Gemini API 테스트"""
    try:
        # API 키 설정
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("GOOGLE_API_KEY가 설정되지 않았습니다.")
            return False
        
        print(f"API 키 확인: {api_key[:10]}...")
        
        # Gemini 설정
        genai.configure(api_key=api_key)
        
        # 모델 초기화 (무료 버전용)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 테스트 요청
        test_text = "스타트업 창업을 위한 투자자를 만나고 싶어요"
        
        system_prompt = """
        당신은 '건너건너'라는 인맥 연결 서비스의 요청 분석 AI입니다.
        사용자의 요청 텍스트를 분석하여 아래 6가지 카테고리 중 가장 적합한 것 하나만 골라 소문자로 답해주세요.
        다른 설명은 절대 추가하지 마세요.
        카테고리: business, networking, career, academic, hobby, personal
        """
        
        response = model.generate_content(f"{system_prompt}\n\n사용자 요청: {test_text}")
        
        print(f"테스트 요청: {test_text}")
        print(f"AI 응답: {response.text.strip()}")
        
        return True
        
    except Exception as e:
        print(f"API 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("Gemini API 연결 테스트를 시작합니다...")
    success = test_gemini_api()
    
    if success:
        print("\nGemini API가 성공적으로 연결되었습니다!")
        print("이제 Django 서버를 실행하여 AI 추천 기능을 사용할 수 있습니다.")
    else:
        print("\nAPI 연결에 실패했습니다. 설정을 확인해주세요.")