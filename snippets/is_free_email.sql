-- Snippet: is_free_email
-- Returns TRUE if the email domain is a known free provider.
-- Usage: WHERE NOT ({{ snippet: is_free_email }})
--
-- Expects a column called `email` in scope.

lower(split_part(email, '@', 2)) IN (
  'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
  'aol.com', 'icloud.com', 'mail.com', 'protonmail.com',
  'zoho.com', 'yandex.com', 'gmx.com', 'live.com',
  'me.com', 'msn.com', 'qq.com', '163.com', '126.com'
)
