-- WiseSpeak 데이터베이스 초기화 스크립트
-- Supabase SQL 편집기에서 실행

-- 강의 테이블
CREATE TABLE public.lectures (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    pdf_url TEXT NOT NULL,
    total_pages INTEGER NOT NULL,
);

-- 페이지 테이블
CREATE TABLE public.pages (
    id UUID PRIMARY KEY,
    lecture_id UUID REFERENCES public.lectures(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    content TEXT,
    audio_url TEXT,
    UNIQUE(lecture_id, page_number)
);

-- 인덱스 생성
CREATE INDEX lectures_created_at_idx ON public.lectures (created_at DESC);
CREATE INDEX pages_lecture_id_idx ON public.pages (lecture_id);
CREATE INDEX pages_lecture_page_idx ON public.pages (lecture_id, page_number);

-- RLS(Row Level Security) 정책 설정
-- MVP 단계에서는 모든 사용자에게 접근 권한 부여
ALTER TABLE public.lectures ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "모든 사용자가 강의를 볼 수 있음" ON public.lectures
    FOR SELECT USING (true);

CREATE POLICY "모든 사용자가 강의를 생성할 수 있음" ON public.lectures
    FOR INSERT WITH CHECK (true);

CREATE POLICY "모든 사용자가 페이지를 볼 수 있음" ON public.pages
    FOR SELECT USING (true);

CREATE POLICY "모든 사용자가 페이지를 생성할 수 있음" ON public.pages
    FOR INSERT WITH CHECK (true);

-- 스토리지 버킷 설정 명령어 (Supabase 대시보드에서 수동으로 생성해야 함)
-- 1. wisespeak 버킷 생성
-- 2. 아래 폴더 구조 생성:
--    - temp/ (임시 파일 저장)
--    - lectures/ (영구 PDF 저장)
--    - audio/ (생성된 오디오 파일 저장)
