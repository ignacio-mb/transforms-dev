-- Snippet: normalize_email
-- Extracts and lowercases the domain from an email address.
-- Usage in transforms: {{ snippet: normalize_email }}
--
-- Expects a column called `email` in scope.

lower(split_part(email, '@', 2))
