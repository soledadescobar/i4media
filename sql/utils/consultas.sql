--Conteo de hashtags:
select lower(text) as ht, count(text) as Tweets from hashtags group by ht order by tweets desc;

select lower(text) as ht from hashtags limit 100 offset 1400;

--Conteo de tweets por dia:
select to_date(created_at, 'Dy mon DD HH24:MI:SS "+0000" YYYY') as dia, count(*) as "tweets" from tweets group by dia;

--Conteo de tweets por hora:
select extract(day from to_timestamp(created_at, $$Dy mon DD HH24:MI:SS "+0000" YYYY$$)) as dia, extract(hour from to_timestamp(created_at, $$Dy mon DD HH24:MI:SS "+0000" YYYY$$)) as hora, count(id) as "tweets" from tweets group by 1,2 order by 1,2 asc;

--Conteo de tweets por hora ultimos 7 dias:
select extract(day from to_timestamp(created_at, $$Dy mon DD HH24:MI:SS "+0000" YYYY$$)) as dia, extract(hour from to_timestamp(created_at, $$Dy mon DD HH24:MI:SS "+0000" YYYY$$)) as hora, count(id) as tweets from tweets where to_timestamp(created_at, $$Dy mon DD HH24:MI:SS "+0000" YYYY$$) > current_date - interval $$14$$ and to_timestamp(created_at, $$Dy mon DD HH24:MI:SS "+0000" YYYY$$) < current_date - interval $$7$$ day group by 1,2 order by 1,2 asc;

--Tweet con Hashtag
select tw.text,
lower(ht.text) as hashtag
from tweets as tw
join hashtags as ht
on tw.id_tweet = ht.id_tweet


select extract(hour from to_timestamp(created_at, 'Dy mon DD HH24:MI:SS "+0000" YYYY')) as hora from tweets limit