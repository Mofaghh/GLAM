create table if not exists orders (
    id bigint generated always as identity primary key,
    user_id bigint not null,
    username text,
    description text,
    topic_id bigint unique not null,
    status text default 'active',
    created_at timestamptz default now()
);

create index if not exists idx_orders_user_active
    on orders (user_id, status);
