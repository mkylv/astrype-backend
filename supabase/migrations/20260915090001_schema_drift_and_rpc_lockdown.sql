-- Canlı veritabanında elle yapılmış ama migration'larda olmayan değişikliklerin kaydı
-- (2026-09-15, canlı şema service-role OpenAPI ile karşılaştırılarak çıkarıldı).
-- Tümü idempotent: canlıya tekrar uygulanması güvenli, mevcut veriyi/fonksiyonu EZMEZ.

-- 1) Kodun kullandığı ama migration'da tanımsız kolonlar
alter table charts        add column if not exists display    jsonb;  -- routes_chart: çark geometrisi/önizleme
alter table subscriptions add column if not exists product_id text;   -- revenuecat webhook + wallet (Lyra günlük limiti)
alter table subscriptions add column if not exists period     text;   -- weekly / monthly / yearly

-- 2) incr_chat_usage: canlıda elle oluşturulmuş; gövdesi SQL erişimi olmadan okunamadı.
--    Backend sözleşmesi (app/services/wallet.py charge_lyra_message):
--      rpc("incr_chat_usage", {p_user, p_date}) -> o günün GÜNCEL mesaj sayısı (integer).
--    Canlıdaki gerçek fonksiyonu EZMEMEK için yalnızca YOKSA oluşturulur (yeni ortam kurulumu için).
--    TODO: Supabase erişimiyle `pg_get_functiondef('incr_chat_usage'::regproc)` alınıp birebir buraya yazılmalı.
do $$
begin
  if not exists (
    select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'public' and p.proname = 'incr_chat_usage'
  ) then
    execute $f$
      create function public.incr_chat_usage(p_user uuid, p_date date)
      returns integer
      language plpgsql
      security definer
      set search_path = public
      as $body$
      declare v_count integer;
      begin
        insert into chat_usage(user_id, usage_date, message_count)
          values (p_user, p_date, 1)
        on conflict (user_id, usage_date)
          do update set message_count = chat_usage.message_count + 1
        returning message_count into v_count;
        return v_count;
      end;
      $body$
    $f$;
  end if;
end $$;

-- 3) RPC kilidi (2026-09-15'te canlıda SQL Editor ile uygulandı; burada kayıt altına alınıyor).
--    SECURITY DEFINER fonksiyonlar Postgres varsayılanında PUBLIC'e açıktır; uygulamadaki public key
--    ile çağrılıp coin basılabiliyordu. Yalnızca backend (service_role) çağırabilir.
--    YENİ BİR RPC EKLENİRSE AYNI KİLİT ONA DA UYGULANMALI.
do $$
declare r record;
begin
  for r in
    select p.oid::regprocedure as sig
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'public'
      and p.proname in ('grant_coins', 'spend_coins', 'incr_chat_usage')
  loop
    execute format('revoke execute on function %s from public, anon, authenticated', r.sig);
    execute format('grant execute on function %s to service_role', r.sig);
  end loop;
end $$;

-- NOT: match_memory SECURITY INVOKER (sql stable) — RLS geçerli; 2026-09-15 testinde public key
-- başka kullanıcının hafızası için 0 satır döndü. Backend onu da service_role ile çağırıyor.
