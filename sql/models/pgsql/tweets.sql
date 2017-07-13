create table tweets (
	id serial primary key,
	created_at character(250) null,
	favorite_count bigint null,
	favorited boolean null,
	filter_level character(250) null,
	id_tweet bigint unique,
	id_str character(30) null,
	id_user bigint null,
	in_reply_to_screen_name character(30) null,
	in_reply_to_status_id bigint null,
	in_reply_to_status_id_str character(30) null,
	in_reply_to_user_id bigint null,
	lang character(10) null,
	possibly_sensitive boolean null,
	quoted_status_id bigint null,
	quoted_status_id_str character(30) null,
	scopes text[][],
	retweet_count bigint null,
	retweeted boolean null,
	source character(250) null,
	text text,
	truncated boolean null,
	withheld_copyright boolean null,
	withheld_in_countries character(250) null,
	withheld_scope character(250) null
);

create index on tweets (created_at);
create index on tweets (id_user);
