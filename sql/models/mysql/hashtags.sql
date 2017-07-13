create table hashtags(
	id integer auto_increment primary key,
	id_tweet bigint,
	indices varchar(250),
	text varchar(250)
);