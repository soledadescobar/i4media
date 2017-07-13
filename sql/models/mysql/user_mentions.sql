create table user_mentions (
	id integer auto_increment primary key,
	id_tweet bigint,
	id_user_mentions bigint,
	id_str varchar(30),
	indices varchar(250),
	name varchar(250),
	screen_name varchar(250)
);
