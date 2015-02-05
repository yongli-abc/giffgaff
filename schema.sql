drop table if exists records;
create table entries (
    id integer primary key autoincrement,
    email string not null,
    name string not null,
    phone string not null,
    nano_qty integer,
    micro_qty integer,
    created_time date default CURRENT_DATE
)
