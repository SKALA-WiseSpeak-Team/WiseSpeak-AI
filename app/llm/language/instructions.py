# app/language/instructions.py
# 언어별 지침 - 다양한 언어별 특성 및 문화적 맥락을 반영한 지침 제공

import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_language_instructions(language: str) -> str:
    """
    언어별 지침 생성
    
    Args:
        language: 언어 코드
    
    Returns:
        언어 지침
    """
    language = language.lower()
    
    # 지원하지 않는 언어인 경우 영어로 기본 설정
    if language not in settings.SUPPORTED_LANGUAGES:
        logger.warning(f"지원하지 않는 언어: {language}, 영어로 대체합니다")
        language = "en"
    
    instructions = {
        "en": "Respond in English using clear, natural language. Employ academic terminology appropriately while maintaining accessibility. Use culturally relevant examples and analogies. Consider diverse English-speaking contexts (North American, British, Australian, etc.) and adapt accordingly. Explain specialized terms when introducing them for the first time.",
        
        "ko": "Respond in Korean (한국어). 자연스럽고 정확한 한국어 표현을 사용하세요. 한국 교육 문화에 적합한 존댓말과 격식체를 유지하되, 필요에 따라 친근한 표현도 활용하세요. 세대별 이해도를 고려하여 전문 용어는 풀어서 설명하고, 적절한 한국적 비유와 예시를 활용하세요. '먹튀', '갑분싸', '솔까말', '꿀팁' 같은 현대 한국어 표현을 맥락에 맞게 자연스럽게 사용하고, '밟이 넓다'와 같은 문화적 표현의 진정한 의미를 이해하고 적용하세요.",
        
        "ja": "Respond in Japanese (日本語). 自然で正確な日本語表現を使用してください。日本の教育環境に適した敬語、丁寧語、常体を状況に応じて適切に使い分けてください。年齢層や社会的立場を考慮した表現を選び、専門用語には必要に応じて説明を加えてください。「スマホ」「エモい」「リア充」などの現代日本語表現を文脈に合わせて自然に使用し、「空気を読む」「猫をかぶる」などの日本文化特有の表現の真の意味を理解して適用してください。",
        
        "zh": "Respond in Chinese (中文). 使用自然、准确的中文表达，注重语言的流畅性和专业性。根据教育场景使用恰当的敬语和表达方式，考虑不同地区（中国大陆、台湾、香港等）的语言习惯差异。专业术语应配以必要的解释，采用符合中华文化的例子和比喻。适当使用「666」「打卡」「内卷」等现代中文表达，理解并正确运用「打铁还需自身硬」「一眼望穿秋水」等文化特定表达的真正含义。",
        
        "es": "Respond in Spanish using natural, accurate expressions. Adapt formality levels according to educational contexts, considering regional variations across Spanish-speaking countries. Use 'tú' or 'usted' appropriately based on the situation. Incorporate culturally relevant examples that resonate with Hispanic contexts. When using specialized terms, provide brief explanations. Understand and appropriately use expressions like 'ponerse las pilas', 'dar en el clavo', or modern colloquialisms like 'molar', 'guay', or 'friki' according to regional contexts.",
        
        "fr": "Respond in French using natural, precise expressions. Balance formality appropriate for educational settings ('tu' vs 'vous'), considering the context carefully. Present concepts with clarity, explaining specialized terminology when needed. Use examples and metaphors that are culturally relevant to French-speaking contexts. Understand and appropriately incorporate expressions like 'avoir la pêche', 'être dans les choux', or contemporary terms like 'chelou', 'ouf', or 'kiffer' when contextually appropriate.",
        
        "de": "Respond in German using natural, precise expressions. Employ appropriate formality levels ('du' vs 'Sie') for educational contexts, with 'Sie' as the default for formal education. Present concepts with clarity and German precision, explaining Fachbegriffe (specialized terminology) when introduced. Integrate examples and analogies relevant to German-speaking cultures. Understand and appropriately use expressions like 'die Daumen drücken', 'Schwein haben', or modern colloquialisms like 'krass', 'geil', or 'Digga' when contextually appropriate."
    }
    
    return instructions.get(language, instructions["en"])