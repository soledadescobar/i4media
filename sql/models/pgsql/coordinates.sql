create table coordinates (
	id serial primary key,
	id_tweet bigint,
	coordinates numeric[],
	type character(30)
);
