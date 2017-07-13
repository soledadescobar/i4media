create table friendfollower (
	id serial primary key,
	user_id bigint,
	followers bigint[],
	followers_count int,
	friends bigint[],
	friends_count int,
	created timestamp
);

create index on friendfollower (created);
create index on friendfollower (user_id);
