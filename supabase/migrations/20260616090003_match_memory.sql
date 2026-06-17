-- Cosmic Memory RAG: kullanıcıya özel cosine benzerlik araması.
-- Backend recall() bunu çağırır. user_id filtresi fonksiyon içinde zorunlu.

create or replace function match_memory(
  p_user_id uuid,
  p_query vector(1536),
  p_match_count int default 6
)
returns table (
  id uuid,
  source text,
  summary text,
  similarity float
)
language sql stable
as $$
  select
    m.id,
    m.source,
    m.summary,
    1 - (m.embedding <=> p_query) as similarity
  from memory_chunks m
  where m.user_id = p_user_id
  order by m.embedding <=> p_query
  limit p_match_count;
$$;
