### Environmental Variables
```
API_TOKEN=
SQL_HOST=
SQL_USER=
SQL_PORT=
SQL_DATABASE=
SQL_PASSWORD=
```
### Database is PostgreSQL
```
create table dict_users
(
    user_id        bigint not null,
    username       text,
    user_name      text,
    user_surname   text,
    dict           text,
    shuffle        boolean default false,
    separator      text    default ' - '::text,
    order_of_words boolean default true,
    admin          boolean default false
);
```
