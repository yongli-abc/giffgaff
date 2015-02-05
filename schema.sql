drop table if exists entries;
create table entries (
    id integer primary key autoincrement,
    email string not null unique,
    name string not null,
    phone string not null,
    nano_qty integer,
    micro_qty integer,
    created_time DATETIME default CURRENT_TIMESTAMP
)
