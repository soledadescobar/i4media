create table media (
	id serial primary key,
	id_tweet bigint null,
	display_url character(250) null,
	expanded_url character(250) null,
	id_media bigint,
	id_str character(30) null,
	indices character(250) null,
	media_url character(250) null,
	media_url_https character(250) null,
	source_status_id bigint null,
	source_status_id_str character(30) null,
	type character(30) null,
	url character(250) null
);

create index on media (id_tweet);
create index on media (id_media);
