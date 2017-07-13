create table hashtags(
        id serial primary key,
        id_tweet bigint,
        indices character(250),
        text character(250)
);

CREATE UNIQUE INDEX Bk_hashtags ON hashtags (
        id_tweet, text
);

CREATE INDEX id_tweet on hashtags (
        id_tweet
);

CREATE INDEX text on hashtags (
        text
);
