# Database Engineering Guide

## 1. Purpose

This guide teaches how PostgreSQL stores durable SeisChat state and how SQLAlchemy and Alembic safely represent and evolve it.

## 2. Responsibility

The database owner defines models, constraints, indexes, migrations, transaction helpers, and test fixtures with feature owners. The database enforces durable invariants; application services enforce workflow and authorization.

## 3. Concepts first

Understand tables, rows, columns, data types, primary/foreign keys, unique/not-null/check constraints, indexes, joins, transactions, and the difference between a migration and a runtime query.

## 4. Tools

PostgreSQL, SQLAlchemy ORM, Alembic, a SQL client, migration commands, and isolated test databases/transactions.

## 5. Features

Create `users`, `sessions`, and `messages`; enforce username and session credential uniqueness; relate sessions/messages to users; index session expiry and message ordering/ownership; support cursor queries and hard deletion.

## 6. Implementation sequence

1. Model users with UUID primary key, unique username, password hash, and timestamps. Do not invent normalization until the team decides its rules.
2. Model sessions with UUID, user foreign key, hash of the session credential, expiry, creation, and revocation timestamps.
3. Model messages with UUID, author foreign key, content, and creation timestamp. Do not retain a soft-delete column for V1 hard deletion.
4. Add constraints and indexes for foreign keys, expiry, message ordering, and ownership.
5. Generate and review Alembic migrations; test upgrade from an empty database.
6. Implement transactions for message creation and deletion.
7. Implement stable cursor ordering, such as `(created_at, id)`, so equal timestamps cannot duplicate or skip rows.
8. Test rollback and isolation.

## 7. Expected files/components

The current implementation uses `backend/app/models/` for user and session models, `backend/app/database/` for the declarative base and database connection, `backend/migrations/` for Alembic, and `backend/tests/test_models.py` for isolated model tests. Message models and repositories/data-access functions belong to later feature phases. Keep schema details synchronized with `docs/database-design.md` and `docs/api-contract.md`.

## 8. Connections

Registration inserts a user; login inserts a server session; authenticated requests look up a non-revoked, unexpired session; message send inserts a message before broadcasting; history reads ordered rows by cursor; delete verifies author then removes the row and triggers a broadcast.

## 9. Testing

Test constraints, relationships, session expiry/revocation, migration creation/upgrade, cursor first/next/last pages, equal timestamps, transaction rollback, hard deletion, and database isolation. Model tests use an in-memory SQLite database; test PostgreSQL migrations with a separate local test database, never production data. Use realistic SeisChat rows rather than unrelated sample data.

## 10. Common mistakes

Do not edit applied migrations, use offset pagination for the required history, omit an index from a frequent query, rely only on frontend validation, cascade-delete unexpectedly, store plaintext secrets, or broadcast a row that was not committed.

## 11. Security

Store password and session hashes only, restrict database credentials, avoid logging query parameters containing secrets, use least-privileged application access, and never expose internal database errors to clients.

## 12. Acceptance criteria

An empty PostgreSQL database can be migrated to the current schema. Constraints prevent invalid relationships and duplicates; cursor history is stable; hard-deleted rows are absent; transactions leave no partial message/session state after failure.

## 13. Questions

What does each foreign key protect? Why is `(created_at, id)` a better cursor order than time alone? Which work belongs in a transaction? Why can a database constraint still need an application authorization check? What does a migration reproduce?
