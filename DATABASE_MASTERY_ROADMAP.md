# Database Mastery Roadmap

A guided track to understand databases deeply — enough to make the SQL vs NoSQL
call with confidence and sound senior doing it. Applied to two real systems:
**Biocity CRM (PostgreSQL)** and **Reltio Auth (DynamoDB)**.

## How we run it
One topic per turn: **simple explanation → small real example → one analogy →
a "how to sound senior about this" line → 2 check-questions** to lock it in
before moving on.

## Progress
`▓▓░░░░░░░░` 1 / 9 topics · **Currently on: Topic 2**

---

## 1. What a database really is (foundations) ✅
- [x] Why databases exist (what's wrong with files / Excel / plain code)
- [x] What a DB engine actually does under the hood (store, index, query) — the mental model
- [x] OLTP vs OLAP (running the business vs analysing it)

## 2. The families of databases (the "models")
- [ ] Relational (tables) · Document (JSON, Mongo) · Key-value & wide-column (DynamoDB, Redis, Cassandra) · Graph · Search & Vector
- [ ] What each is shaped for — and what it's bad at

## 3. Core building blocks every engineer must own
- [ ] Schema, keys (primary / foreign), and referential integrity (the "bouncer")
- [ ] Relationships: one-to-one, one-to-many, many-to-many — and how each DB family handles them
- [ ] Normalization vs denormalization (store once & join, vs duplicate & embed)
- [ ] Indexes — how reads get fast, and what they cost you on writes

## 4. Consistency & reliability (the senior core)
- [ ] ACID & transactions (all-or-nothing) — why money / health data needs it
- [ ] CAP theorem in plain words (consistency vs availability when the network breaks)
- [ ] Strong vs eventual consistency (bank balance vs a "like count")

## 5. Access patterns & data modeling (the real decision skill)
- [ ] "Model by your queries" — designing data around how you'll read it
- [ ] Known patterns (NoSQL / Dynamo single-table thinking) vs flexible / ad-hoc queries (SQL)
- [ ] Read-heavy vs write-heavy workloads

## 6. Scale & performance
- [ ] Vertical vs horizontal scaling
- [ ] Replication (copies for safety + speed) · Sharding / partitioning (splitting data)
- [ ] Caching (Redis) · latency vs throughput

## 7. Choosing a database (bring it all together)
- [ ] The decision framework: access patterns → consistency → scale → team → cost
- [ ] SQL vs NoSQL — and polyglot persistence (several DBs, each where it's best)
- [ ] Managed vs self-hosted (RDS, Atlas, Dynamo) and how cost models differ

## 8. Operating databases in the real world
- [ ] Backups & disaster recovery · schema migrations (changing without downtime)
- [ ] Security: encryption, least privilege, data residency (matters for patient data)
- [ ] Common anti-patterns that bite people

## 9. Apply it to your projects (capstone)
- [ ] Design the Biocity CRM model in PostgreSQL
- [ ] Reverse-engineer the Reltio DynamoDB auth model and see why it's shaped that way
- [ ] How Postgres + DynamoDB + S3 coexist in one system

---

### Notes / "aha" moments
_(jot takeaways here as we go)_
-
