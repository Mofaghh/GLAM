create table if not exists orders (
    id bigint generated always as identity primary key,
    user_id bigint not null,
    username text,
    service_type text,
    description text,
    topic_id bigint unique not null,
    status text default 'active',
    created_at timestamptz default now()
);

create index if not exists idx_orders_user_active
    on orders (user_id, status);

-- Для уже созданной таблицы (без пересоздания):
-- alter table orders rename column skin_type to service_type;
-- либо, если колонки ещё нет:
-- alter table orders add column if not exists service_type text;

