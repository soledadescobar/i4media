create table sizes (
	id serial primary key,
	id_media bigint,
	thumb varchar(250),
	large varchar(250),
	medium varchar(250),
	small varchar(250)
);