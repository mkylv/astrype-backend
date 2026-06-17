-- Astrype — Row Level Security (her tabloda ZORUNLU)
-- Kullanıcı yalnızca kendi verisine erişir. Backend service-role ile bağlanıp
-- RLS'yi bypass etse de, RLS doğrudan Flutter SDK erişimleri için son savunmadır.

alter table profiles            enable row level security;
alter table charts              enable row level security;
alter table daily_insight_cache enable row level security;
alter table readings            enable row level security;
alter table relationships       enable row level security;
alter table chat_messages       enable row level security;
alter table memory_chunks       enable row level security;
alter table subscriptions       enable row level security;

-- profiles: id == auth.uid()
create policy "own_profile" on profiles
  for all using (auth.uid() = id) with check (auth.uid() = id);

-- user_id == auth.uid() olan tablolar için ortak desen
create policy "own_charts" on charts
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own_daily" on daily_insight_cache
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own_readings" on readings
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own_relationships" on relationships
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own_chat" on chat_messages
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own_memory" on memory_chunks
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- subscriptions: kullanıcı yalnızca OKUYABİLİR; yazma webhook (service-role) ile.
create policy "read_own_subscription" on subscriptions
  for select using (auth.uid() = user_id);
