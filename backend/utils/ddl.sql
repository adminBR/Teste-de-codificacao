create table users (
   usr_id         serial primary key,
   usr_name       text not null,
   usr_email      text not null unique,
   usr_password   text not null,
   usr_isadmin    boolean default false,
   usr_created_at timestamp default current_timestamp,
   usr_updated_at timestamp default current_timestamp,
);

create table clients (
   cli_id         serial primary key,
   cli_name       text not null,
   cli_email      text not null unique,
   cli_cpf        text not null unique,
   cli_created_at timestamp default current_timestamp,
   cli_updated_at timestamp default current_timestamp,
   cli_created_by integer not null
            REFERENCES users ( usr_id )
            on delete cascade,
);

create table products (
   prd_id            serial primary key,
   prd_desc          text not null,
   prd_category      text,
   prd_section       text,
   prd_price         numeric(10,2) not null,
   prd_barcode       text unique,
   prd_initial_stock integer not null,
   prd_current_stock integer not null,
   prd_expiring_date date,
   prd_created_at    timestamp default current_timestamp,
   prd_updated_at    timestamp default current_timestamp
);

create table product_images (
   img_id         serial primary key,
   prd_id         integer not null
      references products ( prd_id )
         on delete cascade,
   img_url        text not null,
   img_created_at timestamp default current_timestamp
);

create table orders (
   ord_id         serial primary key,
   ord_status     text not null,
      references clients ( cli_id )
         on delete cascade,
   ord_usr_id     integer
      references users ( usr_id ),
   ord_created_at timestamp default current_timestamp,
   ord_updated_at timestamp default current_timestamp
);

create table orders_items (
   ord_it_id      serial primary key,
   ord_id         integer not null
      references orders ( ord_id )
         on delete cascade,
   ord_prd_id     integer not null
      references products ( prd_id ),
   ord_it_quant   integer not null,
   ord_it_price   numeric(10,2) not null,
   ord_created_at timestamp default current_timestamp,
   ord_updated_at timestamp default current_timestamp
);

create table product_images (
   img_id         serial primary key,
   prd_id         integer not null
      references products ( prd_id )
         on delete cascade,
   img_url        text not null,
   img_created_at timestamp default current_timestamp
);