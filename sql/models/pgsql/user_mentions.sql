create table user_mentions (
        id serial primary key,
        id_tweet bigint,
        id_user_mentions bigint,
        id_str character(30),
        indices character(250),
        name character(250),
        screen_name character(250)
);

CREATE UNIQUE INDEX user_mentions_Bk_user_mentions ON user_mentions (
	id_tweet, id_user_mentions
);
