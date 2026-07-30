-- Astrype — Coin ekonomisi ("Yıldız Tozu" / Stardust) altyapısı.
-- Hibrit model: abonelik (devamlı içerik sınırsız) + coin (tek seferlik okumalar).
-- Coin bakiyesi SUNUCU tarafında tutulur; harcama/kazandırma atomik + idempotent.
-- Kaynak: design-refs/revisions/coinekonomisivefiyatlandirma.md

-- 1) wallets: kullanıcı coin bakiyesi (tek satır/kullanıcı)
create table if not exists wallets (
  user_id uuid primary key references profiles(id) on delete cascade,
  balance integer not null default 0 check (balance >= 0),
  first_purchase_done boolean not null default false,  -- ilk alım +%50 bonusu için
  updated_at timestamptz default now()
);

-- 2) coin_transactions: değişmez defter (audit + idempotency)
create table if not exists coin_transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  amount integer not null,              -- + kazanç, - harcama
  balance_after integer not null,
  reason text not null,                 -- 'signup_bonus'|'spend'|'purchase'|'subscription_grant'|'streak'|'ad_reward'|'welcome_bonus'
  module text,                          -- harcamaysa modül anahtarı
  idempotency_key text unique,          -- retry/timeout çift işlem koruması
  metadata jsonb not null default '{}',
  created_at timestamptz default now()
);
create index if not exists coin_tx_user_idx on coin_transactions(user_id, created_at desc);

-- 3) feature_prices: modül fiyatı + kategori (uzaktan konfigüre edilebilir)
--    category: 'free' | 'continuous' (abonelikte sınırsız) | 'one_time' (her zaman coin) | 'chat'
create table if not exists feature_prices (
  feature text primary key,
  coin_price integer not null default 0 check (coin_price >= 0),
  category text not null,
  label text,
  updated_at timestamptz default now()
);

-- 4) chat_usage: Lyra günlük mesaj hakkı sayacı (abonelik limiti için)
create table if not exists chat_usage (
  user_id uuid references profiles(id) on delete cascade,
  usage_date date not null,
  message_count integer not null default 0,
  primary key (user_id, usage_date)
);

-- ---- Seed: modül fiyatları (coinekonomisi §4) ----
insert into feature_prices (feature, coin_price, category, label) values
  ('horoscope_daily',    0,  'free',       'Günlük Burç'),
  ('horoscope_monthly', 30,  'continuous', 'Aylık Burç'),
  ('daily_map',         10,  'continuous', 'Günlük Harita'),
  ('tarot',             40,  'continuous', 'Tarot (3 kart)'),
  ('dream',             40,  'continuous', 'Rüya Yorumu'),
  ('coffee',            50,  'continuous', 'Kahve Falı'),
  ('compatibility',     60,  'continuous', 'Kozmik Uyum'),
  ('natal',            250,  'one_time',   'Doğum Haritası'),
  ('yildizname',       300,  'one_time',   'Yıldızname'),
  ('human_design',     100,  'one_time',   'İnsan Tasarımı'),
  ('palm',              75,  'one_time',   'El Falı'),
  ('face',              75,  'one_time',   'Yüz Falı'),
  ('subconscious',      75,  'one_time',   'Bilinçaltı'),
  ('numerology',        60,  'one_time',   'Numeroloji'),
  ('ebced',             50,  'one_time',   'Ebced'),
  ('lyra_chat',          3,  'chat',       'Lyra AI (mesaj)')
on conflict (feature) do update
  set coin_price = excluded.coin_price,
      category   = excluded.category,
      label      = excluded.label,
      updated_at = now();

-- ---- Atomik RPC: coin harca ----
-- Dönüş: (balance, charged). idempotency_key varsa ve daha önce işlendiyse tekrar düşmez.
-- p_amount = 0 ise (ücretsiz/abonelik kapsamı) sadece bakiye döner.
create or replace function spend_coins(
  p_user uuid,
  p_amount integer,
  p_reason text,
  p_module text,
  p_idempotency_key text
) returns table(balance integer, charged boolean)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_existing coin_transactions%rowtype;
  v_balance integer;
begin
  if p_amount < 0 then
    raise exception 'AMOUNT_NEGATIVE';
  end if;

  -- idempotency: aynı işlem tekrar gelirse çift düşme yok
  if p_idempotency_key is not null then
    select * into v_existing from coin_transactions
      where idempotency_key = p_idempotency_key limit 1;
    if found then
      balance := v_existing.balance_after; charged := false; return next; return;
    end if;
  end if;

  -- wallet garanti + satır kilidi
  insert into wallets(user_id, balance) values (p_user, 0)
    on conflict (user_id) do nothing;
  select w.balance into v_balance from wallets w where w.user_id = p_user for update;

  -- ücretsiz / abonelik kapsamı: kayıt tutma, sadece bakiye dön
  if p_amount = 0 then
    balance := v_balance; charged := false; return next; return;
  end if;

  if v_balance < p_amount then
    raise exception 'INSUFFICIENT_COINS' using errcode = 'P0001';
  end if;

  -- NOT: kolon adı OUT değişkeni 'balance' ile çakışmasın diye wallets.* nitele.
  update wallets set balance = wallets.balance - p_amount, updated_at = now()
    where wallets.user_id = p_user returning wallets.balance into v_balance;

  insert into coin_transactions(user_id, amount, balance_after, reason, module, idempotency_key)
    values (p_user, -p_amount, v_balance, p_reason, p_module, p_idempotency_key);

  balance := v_balance; charged := true; return next; return;
end;
$$;

-- ---- Atomik RPC: coin kazandır (satın alma / abonelik / bonus) ----
create or replace function grant_coins(
  p_user uuid,
  p_amount integer,
  p_reason text,
  p_idempotency_key text,
  p_metadata jsonb default '{}'
) returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  v_balance integer;
begin
  insert into wallets(user_id, balance) values (p_user, 0)
    on conflict (user_id) do nothing;

  if p_amount <= 0 then
    select balance into v_balance from wallets where user_id = p_user;
    return coalesce(v_balance, 0);
  end if;

  -- idempotency: aynı grant tekrar gelirse yeniden ekleme
  if p_idempotency_key is not null
     and exists(select 1 from coin_transactions where idempotency_key = p_idempotency_key) then
    select balance into v_balance from wallets where user_id = p_user;
    return coalesce(v_balance, 0);
  end if;

  update wallets set balance = balance + p_amount, updated_at = now()
    where user_id = p_user returning balance into v_balance;

  insert into coin_transactions(user_id, amount, balance_after, reason, idempotency_key, metadata)
    values (p_user, p_amount, v_balance, p_reason, p_idempotency_key, coalesce(p_metadata, '{}'));

  return v_balance;
end;
$$;

-- ---- RLS: kullanıcı yalnızca kendi verisini OKUR; yazma backend (service-role) + RPC ile ----
alter table wallets            enable row level security;
alter table coin_transactions  enable row level security;
alter table feature_prices     enable row level security;
alter table chat_usage         enable row level security;

drop policy if exists "read_own_wallet" on wallets;
create policy "read_own_wallet" on wallets
  for select using (auth.uid() = user_id);

drop policy if exists "read_own_coin_tx" on coin_transactions;
create policy "read_own_coin_tx" on coin_transactions
  for select using (auth.uid() = user_id);

drop policy if exists "read_own_chat_usage" on chat_usage;
create policy "read_own_chat_usage" on chat_usage
  for select using (auth.uid() = user_id);

-- feature_prices: herkes okuyabilir (fiyat kataloğu), yazma yalnız service-role.
drop policy if exists "read_prices" on feature_prices;
create policy "read_prices" on feature_prices
  for select using (true);
