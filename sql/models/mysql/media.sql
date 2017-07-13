create table media (
	id integer auto_increment primary key,
	id_tweet bigint null,
	display_url varchar(250) null,
	expanded_url varchar(250) null,
	id_media bigint,
	id_str varchar(30) null,
	indices varchar(250) null,
	media_url varchar(250) null,
	media_url_https varchar(250) null,
	source_status_id bigint null,
	source_status_id_str varchar(30) null,
	type varchar(30) null,
	url varchar(250) null
);