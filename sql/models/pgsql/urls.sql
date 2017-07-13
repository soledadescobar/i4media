create table urls(
	id serial primary key,
	id_tweet bigint null,
	id_user bigint null,
	display_url character(250),
	expanded_url character(250),
	indices character(250),
	url character(250)
);

create index on urls (id_tweet);
create index on urls (id_user);
