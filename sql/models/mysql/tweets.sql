create table tweets (
	id integer auto_increment primary key,
	created_at varchar(250) null,
	favorite_count bigint null,
	favorited boolean null,
	filter_level varchar(250) null,
	id_tweet bigint,
	id_str varchar(30) null,
	in_reply_to_screen_name varchar(30) null,
	in_reply_to_status_id bigint null,
	in_reply_to_status_id_str varchar(30) null,
	in_reply_to_user_id bigint null,
	lang varchar(3) null,
	possibly_sensitive boolean null,
	quoted_status_id bigint null,
	quoted_status_id_str varchar(30) null,
	scopes varchar(250),
	retweet_count bigint null,
	retweeted boolean null,
	source varchar(250) null,
	text text,
	truncated boolean null,
	withheld_copyright boolean null,
	withheld_in_countries varchar(250) null,
	withheld_scope varchar(250) null,
    date_inserted datetime default now()
);


