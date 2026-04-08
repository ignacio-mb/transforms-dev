-- Discourse Topic Activity
--
-- Aggregated topic-level metrics from the Metabase community forum.
-- Tracks engagement, resolution, and response times.

WITH topics AS (
  SELECT
    id,
    title,
    category_id,
    user_id AS author_id,
    created_at,
    last_posted_at,
    posts_count,
    reply_count,
    views,
    like_count,
    closed,
    archived
  FROM staging.discourse_topics
),

posts AS (
  SELECT
    topic_id,
    min(created_at) FILTER (WHERE post_number = 2) AS first_reply_at,
    count(*) FILTER (WHERE user_id IN (
      SELECT id FROM staging.discourse_users WHERE is_staff
    )) AS staff_replies
  FROM staging.discourse_posts
  GROUP BY 1
),

final AS (
  SELECT
    t.id,
    t.title,
    t.category_id,
    t.author_id,
    t.created_at,
    t.last_posted_at,
    t.posts_count,
    t.reply_count,
    t.views,
    t.like_count,
    t.closed,
    t.archived,
    p.first_reply_at,
    p.staff_replies,
    EXTRACT(EPOCH FROM (p.first_reply_at - t.created_at)) / 3600 AS hours_to_first_reply,
    date_trunc('week', t.created_at) AS created_week
  FROM topics t
  LEFT JOIN posts p ON t.id = p.topic_id
)

SELECT * FROM final
