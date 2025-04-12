-- SQL Migration: Fix django_admin_log user_id ForeignKey for Custom User Model

-- Use CTE to drop the existing constraint without relying on its name
DO $$
DECLARE
    constraint_name text;
BEGIN
    WITH constraints AS (
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'django_admin_log'::regclass
          AND contype = 'f'
          AND conkey @> ARRAY[(
              SELECT attnum FROM pg_attribute
              WHERE attrelid = 'django_admin_log'::regclass
                AND attname = 'user_id'
          )]
    )
    SELECT conname INTO constraint_name FROM constraints LIMIT 1;

    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE django_admin_log DROP CONSTRAINT %I;', constraint_name);
    END IF;
END $$;

-- Step 2: Add the new constraint referencing custom user model in auth_app
ALTER TABLE django_admin_log
ADD CONSTRAINT fk_user_id FOREIGN KEY (user_id)
REFERENCES auth_app_user (id) ON DELETE CASCADE;
