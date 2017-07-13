create table urls(
	id serial primary key,
	id_tweet bigint null,
	id_user bigint null,
	display_url varchar(250),
	expanded_url varchar(250),
	indices varchar(250),
	url varchar(250)
);
