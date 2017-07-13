create table sizes (
	id serial primary key,
	id_media bigint,
	thumb text[][],
	large text[][],
	medium text[][],
	small text[][]
);
