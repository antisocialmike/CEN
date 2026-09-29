UPDATE employees e
   SET email = lower(btrim(e.email))
 WHERE e.email <> lower(btrim(e.email))
   AND NOT EXISTS (
       SELECT 1 FROM employees other
        WHERE other.id <> e.id
          AND lower(btrim(other.email)) = lower(btrim(e.email))
   );

ALTER TABLE employees
    ADD CONSTRAINT employees_email_lowercase_check
    CHECK (email = lower(btrim(email))) NOT VALID;
