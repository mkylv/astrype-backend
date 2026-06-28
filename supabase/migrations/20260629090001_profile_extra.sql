-- Onboarding'de toplanan ek profil alanları (cinsiyet / ilişki / iş durumu).
alter table profiles add column if not exists gender text;
alter table profiles add column if not exists relationship_status text;
alter table profiles add column if not exists work_status text;
