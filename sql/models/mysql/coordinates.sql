create table coordinates (
	id serial primary key,
	id_tweet bigint,
	coordinates varchar(250),
	type varchar(30)
);
