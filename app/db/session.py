from supabase import create_client
from app.core.config import settings

# Supabase 클라이언트 설정
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
