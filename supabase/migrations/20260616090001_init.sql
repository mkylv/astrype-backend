-- Astrype — başlangıç şeması (Bölüm 5)
-- pgvector + tüm tablolar. RLS politikaları 0002'de.

create extension if not exists vector;

-- profiles: temel kullanıcı + doğum bilgisi
create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  birth_date date,
  birth_time time,                 -- nullable: "bilmiyorum" seçeneği
  birth_time_known boolean default true,
  birth_lat double precision,
  birth_lng double precision,
  birth_place text,
  birth_tz text,
  language text default 'en',       -- en, tr, az, ru, es
  interests text[] default '{}',
  created_at timestamptz default now()
);

-- charts: hesaplanan natal chart (provider'dan, bir kez)
create table if not exists charts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  raw_json jsonb not null,          -- provider ham çıktısı
  svg_url text,                     -- storage'daki dark tema SVG
  provider text not null,           -- 'numerology_api' | 'swisseph' | 'skyfield'
  created_at timestamptz default now()
);
create index if not exists charts_user_idx on charts(user_id);

-- daily_insight_cache: gün boyu aynı sonuç
create table if not exists daily_insight_cache (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  insight_date date not null,
  content jsonb not null,           -- {love, career, mood, decision, summary}
  created_at timestamptz default now(),
  unique(user_id, insight_date)
);

-- readings: tarot, kahve falı, el falı arşivi (FOTO YOK)
create table if not exists readings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  type text not null,               -- 'tarot' | 'coffee' | 'palm'
  input_meta jsonb,                 -- kartlar / sembol listesi
  result jsonb not null,            -- AI yorumu
  created_at timestamptz default now()
);
create index if not exists readings_user_idx on readings(user_id, created_at desc);

-- relationships: ilişki uyumu
create table if not exists relationships (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  partner_name text,
  partner_birth jsonb not null,
  synastry_raw jsonb,
  result jsonb,
  created_at timestamptz default now()
);
create index if not exists relationships_user_idx on relationships(user_id);

-- chat_messages: AI sohbet geçmişi
create table if not exists chat_messages (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  role text not null,               -- 'user' | 'assistant'
  content text not null,
  created_at timestamptz default now()
);
create index if not exists chat_user_idx on chat_messages(user_id, created_at);

-- memory_chunks: Cosmic Memory RAG (pgvector)
create table if not exists memory_chunks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  source text not null,             -- 'reading' | 'chat' | 'chart' | 'relationship'
  summary text not null,
  embedding vector(1536),           -- OpenAI text-embedding-3-small
  created_at timestamptz default now()
);
create index if not exists memory_chunks_embedding_idx
  on memory_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);
create index if not exists memory_chunks_user_idx on memory_chunks(user_id);

-- subscriptions: RevenueCat webhook senkronu
create table if not exists subscriptions (
  user_id uuid primary key references profiles(id) on delete cascade,
  rc_app_user_id text,
  tier text default 'free',         -- 'free' | 'premium' | 'elite'
  is_active boolean default false,
  expires_at timestamptz,
  updated_at timestamptz default now()
);
