"""
RAG 검색 엔진 모듈
"""
from typing import List, Dict, Any, Optional, Tuple, Union
import re

from ..config import config
from ..utils.logger import get_logger
from ..services.openai_service import OpenAIService
from ..services.vector_db import VectorDBService
from ..processors.language.language_processor import LanguageProcessor

logger = get_logger(__name__)

class RAGEngine:
    """RAG 검색 엔진 클래스"""
    
    def __init__(self, 
                openai_service: Optional[OpenAIService] = None,
                vector_db_service: Optional[VectorDBService] = None,
                language_processor: Optional[LanguageProcessor] = None,
                top_k: int = None):
        """RAG 엔진 초기화
        
        Args:
            openai_service (Optional[OpenAIService], optional): OpenAI 서비스 객체
            vector_db_service (Optional[VectorDBService], optional): 벡터 DB 서비스 객체
            language_processor (Optional[LanguageProcessor], optional): 언어 처리 객체
            top_k (int, optional): 검색 결과 수. 기본값은 config에서 로드
        """
        self.openai_service = openai_service or OpenAIService()
        self.vector_db_service = vector_db_service or VectorDBService()
        self.language_processor = language_processor or LanguageProcessor()
        self.top_k = top_k or config.TOP_K_RESULTS
        
        logger.info(f"RAG 엔진 초기화 완료 (TOP-K: {self.top_k})")
    
    def retrieve(self, 
                query: str, 
                collection_name: str, 
                n_results: int = None,
                filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """쿼리에 관련된 문서 검색
        
        Args:
            query (str): 검색 쿼리
            collection_name (str): 검색할 컬렉션 이름
            n_results (int, optional): 결과 수
            filter_metadata (Optional[Dict[str, Any]], optional): 메타데이터 필터링 조건
        
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        n_results = n_results or self.top_k
        
        if not query or not query.strip():
            logger.warning("빈 쿼리로 검색이 무시되었습니다")
            return []
        
        # 언어 감지
        query_language = self.language_processor.detect_language(query)
        logger.info(f"쿼리 언어 감지: {query_language}")
        
        # 벡터 검색 수행
        results = self.vector_db_service.search(
            collection_name=collection_name,
            query=query,
            n_results=n_results,
            where=filter_metadata
        )
        
        logger.info(f"쿼리 '{query}'에 대해 {len(results)}개 결과 검색 완료")
        return results
    
    def generate_with_context(self, 
                            query: str, 
                            contexts: List[Dict[str, Any]],
                            system_message: Optional[str] = None,
                            temperature: float = 0.7) -> str:
        """컨텍스트를 포함한 텍스트 생성
        
        Args:
            query (str): 사용자 쿼리
            contexts (List[Dict[str, Any]]): 컨텍스트 목록
            system_message (Optional[str], optional): 시스템 메시지
            temperature (float, optional): 온도 매개변수
        
        Returns:
            str: 생성된 텍스트
        """
        if not contexts:
            logger.warning("컨텍스트 없이 생성 요청이 처리되었습니다")
            return self.openai_service.generate_text(query, system_message, temperature)
        
        # 기본 시스템 메시지
        if system_message is None:
            system_message = (
                "주어진 컨텍스트를 바탕으로 질문에 답변하세요. "
                "컨텍스트에 없는 정보는 '제공된 정보에 없습니다'라고 답변하세요. "
                "답변은 명확하고 간결하게 작성하세요."
            )
        
        # 컨텍스트 결합
        context_texts = [context["document"] for context in contexts if "document" in context]
        combined_context = "\n\n---\n\n".join(context_texts)
        
        # 프롬프트 생성
        prompt = f"컨텍스트:\n{combined_context}\n\n질문: {query}\n\n답변:"
        
        # 텍스트 생성
        response = self.openai_service.generate_text(
            prompt=prompt,
            system_message=system_message,
            temperature=temperature
        )
        
        logger.info(f"컨텍스트 {len(contexts)}개를 포함한 답변 생성 완료")
        return response
    
    def rag_query(self, 
                query: str, 
                collection_name: str,
                system_message: Optional[str] = None,
                temperature: float = 0.7,
                n_results: int = None,
                filter_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """RAG 검색 및 응답 생성
        
        Args:
            query (str): 사용자 쿼리
            collection_name (str): 검색할 컬렉션 이름
            system_message (Optional[str], optional): 시스템 메시지
            temperature (float, optional): 온도 매개변수
            n_results (int, optional): 결과 수
            filter_metadata (Optional[Dict[str, Any]], optional): 메타데이터 필터링 조건
        
        Returns:
            Dict[str, Any]: 응답 및 검색 결과
        """
        # 문서 검색
        retrieved_docs = self.retrieve(
            query=query,
            collection_name=collection_name,
            n_results=n_results or self.top_k,
            filter_metadata=filter_metadata
        )
        
        # 응답 생성
        response = self.generate_with_context(
            query=query,
            contexts=retrieved_docs,
            system_message=system_message,
            temperature=temperature
        )
        
        return {
            "query": query,
            "response": response,
            "sources": retrieved_docs
        }
    
    def enhanced_rag_query(self, 
                        query: str, 
                        collection_name: str,
                        reranking: bool = True,
                        query_expansion: bool = True,
                        context_compression: bool = True,
                        system_message: Optional[str] = None,
                        temperature: float = 0.7,
                        n_results: int = None,
                        filter_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """향상된 RAG 검색 및 응답 생성
        
        Args:
            query (str): 사용자 쿼리
            collection_name (str): 검색할 컬렉션 이름
            reranking (bool, optional): 재순위화 사용 여부
            query_expansion (bool, optional): 쿼리 확장 사용 여부
            context_compression (bool, optional): 컨텍스트 압축 사용 여부
            system_message (Optional[str], optional): 시스템 메시지
            temperature (float, optional): 온도 매개변수
            n_results (int, optional): 결과 수
            filter_metadata (Optional[Dict[str, Any]], optional): 메타데이터 필터링 조건
        
        Returns:
            Dict[str, Any]: 응답 및 검색 결과
        """
        expanded_query = query
        
        # 쿼리 확장
        if query_expansion:
            expanded_query = self._expand_query(query)
            logger.info(f"쿼리 확장: '{query}' -> '{expanded_query}'")
        
        # 초기 검색 (더 많은 결과 검색)
        initial_n_results = (n_results or self.top_k) * 2 if reranking else (n_results or self.top_k)
        retrieved_docs = self.retrieve(
            query=expanded_query,
            collection_name=collection_name,
            n_results=initial_n_results,
            filter_metadata=filter_metadata
        )
        
        # 재순위화
        if reranking and retrieved_docs:
            retrieved_docs = self._rerank_results(query, retrieved_docs, n_results or self.top_k)
            logger.info(f"검색 결과 재순위화 완료 ({len(retrieved_docs)}개 결과)")
        
        # 컨텍스트 압축
        if context_compression and retrieved_docs:
            contexts = self._compress_context(query, retrieved_docs)
            logger.info(f"컨텍스트 압축 완료")
        else:
            contexts = retrieved_docs
        
        # 응답 생성
        response = self.generate_with_context(
            query=query,
            contexts=contexts,
            system_message=system_message,
            temperature=temperature
        )
        
        return {
            "query": query,
            "expanded_query": expanded_query if query_expansion else None,
            "response": response,
            "sources": retrieved_docs
        }
    
    def _expand_query(self, query: str) -> str:
        """쿼리 확장
        
        Args:
            query (str): 원본 쿼리
        
        Returns:
            str: 확장된 쿼리
        """
        try:
            # 간단한 프롬프트로 쿼리 확장 요청
            system_message = (
                "당신은 검색 쿼리 확장 전문가입니다. "
                "주어진 쿼리를 더 효과적인 검색을 위해 확장하세요. "
                "원래 의도를 유지하되, 관련된 단어나 개념을 추가하여 검색 범위를 넓히세요."
            )
            
            prompt = f"다음 검색 쿼리를 확장하세요: {query}\n\n확장된 쿼리:"
            
            expanded = self.openai_service.generate_text(
                prompt=prompt,
                system_message=system_message,
                temperature=0.3
            )
            
            # 결과 정리
            expanded = expanded.strip()
            
            # 결과가 너무 길면 원본 쿼리 반환
            if len(expanded) > len(query) * 3:
                logger.warning(f"확장된 쿼리가 너무 깁니다. 원본 쿼리를 사용합니다.")
                return query
                
            return expanded
        except Exception as e:
            logger.error(f"쿼리 확장 중 오류 발생: {e}")
            return query
    
    def _rerank_results(self, 
                        query: str, 
                        results: List[Dict[str, Any]], 
                        n_results: int) -> List[Dict[str, Any]]:
        """검색 결과 재순위화
        
        Args:
            query (str): 사용자 쿼리
            results (List[Dict[str, Any]]): 검색 결과 목록
            n_results (int): 반환할 결과 수
        
        Returns:
            List[Dict[str, Any]]: 재순위화된 결과 목록
        """
        try:
            # 각 문서에 대한 관련성 점수 계산
            scored_results = []
            
            for result in results:
                document = result.get("document", "")
                
                # 간단한 휴리스틱 점수 계산
                # 1. 쿼리 단어가 문서에 등장하는 빈도
                query_words = set(re.findall(r'\w+', query.lower()))
                doc_words = re.findall(r'\w+', document.lower())
                word_count = sum(doc_words.count(word) for word in query_words)
                
                # 2. 거리 점수 (이미 거리 정보가 있으면 사용)
                distance_score = result.get("distance", 0)
                
                # 최종 점수 계산 (낮을수록 좋음)
                final_score = distance_score - (word_count * 0.1)
                
                scored_results.append({
                    "result": result,
                    "score": final_score
                })
            
            # 점수로 정렬 (낮은 점수가 더 관련성 높음)
            sorted_results = sorted(scored_results, key=lambda x: x["score"])
            
            # 상위 n개 결과 반환
            reranked = [item["result"] for item in sorted_results[:n_results]]
            
            return reranked
        except Exception as e:
            logger.error(f"결과 재순위화 중 오류 발생: {e}")
            return results[:n_results]
    
    def _compress_context(self, 
                        query: str, 
                        contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """컨텍스트 압축
        
        Args:
            query (str): 사용자 쿼리
            contexts (List[Dict[str, Any]]): 컨텍스트 목록
        
        Returns:
            List[Dict[str, Any]]: 압축된 컨텍스트 목록
        """
        try:
            compressed_contexts = []
            
            for context in contexts:
                document = context.get("document", "")
                
                # 컨텍스트가 짧으면 압축하지 않음
                if len(document) < 500:
                    compressed_contexts.append(context)
                    continue
                
                # 쿼리와 관련된 부분 추출
                system_message = (
                    "당신은 문서 요약 전문가입니다. "
                    "주어진 쿼리에 답변하는 데 필요한 정보만 추출하세요. "
                    "중요하지 않은 내용은 제거하고, 핵심 정보만 유지하세요."
                )
                
                prompt = f"다음 문서에서 이 쿼리에 답변하는 데 필요한 정보만 추출하세요: '{query}'\n\n문서:\n{document}\n\n추출된 정보:"
                
                compressed = self.openai_service.generate_text(
                    prompt=prompt,
                    system_message=system_message,
                    temperature=0.3
                )
                
                # 압축 결과가 너무 짧으면 원본 사용
                if len(compressed) < len(document) * 0.2:
                    logger.warning(f"압축된 컨텍스트가 너무 짧습니다. 원본을 사용합니다.")
                    compressed_contexts.append(context)
                    continue
                
                # 압축된 컨텍스트로 대체
                compressed_context = context.copy()
                compressed_context["document"] = compressed
                compressed_context["compressed"] = True
                compressed_context["original_length"] = len(document)
                compressed_context["compressed_length"] = len(compressed)
                
                compressed_contexts.append(compressed_context)
            
            return compressed_contexts
        except Exception as e:
            logger.error(f"컨텍스트 압축 중 오류 발생: {e}")
            return contexts
    
    def rag_query_with_language(self, 
                            query: str, 
                            collection_name: str,
                            target_language: Optional[str] = None,
                            system_message: Optional[str] = None,
                            temperature: float = 0.7,
                            n_results: int = None,
                            filter_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """다국어 지원 RAG 검색 및 응답 생성
        
        Args:
            query (str): 사용자 쿼리
            collection_name (str): 검색할 컬렉션 이름
            target_language (Optional[str], optional): 대상 언어 코드
            system_message (Optional[str], optional): 시스템 메시지
            temperature (float, optional): 온도 매개변수
            n_results (int, optional): 결과 수
            filter_metadata (Optional[Dict[str, Any]], optional): 메타데이터 필터링 조건
        
        Returns:
            Dict[str, Any]: 응답 및 검색 결과
        """
        # 쿼리 언어 감지
        query_language = self.language_processor.detect_language(query)
        
        # 대상 언어 설정
        if target_language is None:
            target_language = query_language
        
        # 언어별 필터링 조건 추가
        if filter_metadata is None:
            filter_metadata = {}
        
        # 쿼리 번역 (영어로 검색하기 위해)
        english_query = query
        if query_language != "en":
            english_query = self.language_processor.translate_text(query, "en", query_language)
            logger.info(f"쿼리 번역: '{query}' ({query_language}) -> '{english_query}' (en)")
        
        # 문서 검색
        retrieved_docs = self.retrieve(
            query=english_query,
            collection_name=collection_name,
            n_results=n_results or self.top_k,
            filter_metadata=filter_metadata
        )
        
        # 검색 결과 번역 (필요한 경우)
        translated_contexts = []
        
        for doc in retrieved_docs:
            document = doc.get("document", "")
            doc_language = self.language_processor.detect_language(document)
            
            # 대상 언어와 다른 경우 번역
            if doc_language != target_language:
                translated_text = self.language_processor.translate_text(
                    document, target_language, doc_language
                )
                
                translated_doc = doc.copy()
                translated_doc["document"] = translated_text
                translated_doc["original_language"] = doc_language
                translated_doc["translated"] = True
                
                translated_contexts.append(translated_doc)
            else:
                translated_contexts.append(doc)
        
        # 시스템 메시지 설정
        if system_message is None:
            system_message = (
                f"주어진 컨텍스트를 바탕으로 질문에 답변하세요. "
                f"컨텍스트에 없는 정보는 '제공된 정보에 없습니다'라고 답변하세요. "
                f"답변은 {self.language_processor.get_language_name(target_language)} 언어로 작성하세요."
            )
        
        # 응답 생성
        response = self.generate_with_context(
            query=query,
            contexts=translated_contexts,
            system_message=system_message,
            temperature=temperature
        )
        
        return {
            "query": query,
            "response": response,
            "sources": retrieved_docs,
            "query_language": query_language,
            "target_language": target_language
        }
