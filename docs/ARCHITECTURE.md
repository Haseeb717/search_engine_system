# SCALABLE SEARCH ENGINE SYSTEM - SIMPLE ARCHITECTURE

## VISUAL DIAGRAM

```
                            ┌─────────────────┐
                            │   API USERS     │
                            │ (100B queries/  │
                            │    month)       │
                            └────────┬────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │      FASTAPI APPLICATION       │
                    │  (Search & Re-crawl Endpoints) │
                    └────┬───────────────────────┬───┘
                         │                       │
              ┌──────────▼──────────┐   ┌────────▼─────────┐
              │   SEARCH REQUEST    │   │  CRAWL REQUEST   │
              └──────────┬──────────┘   └────────┬─────────┘
                         │                       │
                    ┌────▼────┐                  │
                    │  REDIS  │                  │
                    │  CACHE  │                  │
                    └────┬────┘                  │
                         │ (miss)                │
                    ┌────▼──────────┐            │
                    │ ELASTICSEARCH │            │
                    │ (Inverted     │            │
                    │  Index)       │            │
                    │ 4B documents  │            │
                    └───────────────┘            │
                                                 │
                         ┌───────────────────────▼──────┐
                         │   RABBITMQ QUEUE             │
                         │   (Crawl Jobs)               │
                         └───────────┬──────────────────┘
                                     │
                         ┌───────────▼──────────────────┐
                         │   CRAWLER WORKERS            │
                         │   (Download web pages)       │
                         │   1,500 pages/second         │
                         └───┬─────────────┬────────────┘
                             │             │
                    ┌────────▼───────┐    │
                    │   S3 STORAGE   │    │
                    │   (Raw HTML)   │    │
                    └────────────────┘    │
                                          │
                              ┌───────────▼──────────────┐
                              │  TEXT PROCESSOR          │
                              │  (Extract & Tokenize)    │
                              └───────────┬──────────────┘
                                          │
                              ┌───────────▼──────────────┐
                              │  INDEXER                 │
                              │  (Build Reverse Index)   │
                              └───────────┬──────────────┘
                                          │
                              ┌───────────▼──────────────┐
                              │  ELASTICSEARCH           │
                              │  (Update Index)          │
                              └──────────────────────────┘
                                          │
                              ┌───────────▼──────────────┐
                              │  POSTGRESQL              │
                              │  (Metadata & Job Status) │
                              └──────────────────────────┘
```

═══════════════════════════════════════════════════════════════

## SIMPLE EXPLANATION

### The 6 Core Components:

1. **FastAPI Application** 
   - Your REST API that users talk to
   - Handles search queries and re-crawl requests

2. **Redis Cache**
   - Stores popular search results
   - Makes searches super fast (no database lookup)

3. **Elasticsearch**
   - Special database for searching text
   - Stores the "inverted index" (like a book's index page)
   - Holds 4 billion web pages

4. **RabbitMQ Queue**
   - A waiting line for crawl jobs
   - Workers take jobs from here one by one

5. **Crawler Workers**
   - Download web pages from the internet
   - Clean and process the HTML
   - Save everything

6. **PostgreSQL**
   - Normal database for metadata
   - Tracks job status, URLs, crawl dates

═══════════════════════════════════════════════════════════════

## HOW IT SCALES TO HANDLE THE MASSIVE LOAD

### Scale Challenge: 4 Billion Pages/Month = 1,500 pages/second

**Solution: Add More Workers**

Instead of 1 worker downloading pages:
```
1 worker × 1 page/second = 1 page/second (TOO SLOW!)
```

Run many workers in parallel:
```
1,500 workers × 1 page/second = 1,500 pages/second ✓
```

Think of it like a restaurant:
- 1 chef = slow service
- 100 chefs working together = fast service

**How we run 1,500 workers:**
- Use Docker containers (each worker is a container)
- Kubernetes manages them automatically
- If queue gets long → spin up more workers
- If queue is empty → shut down workers to save money

═══════════════════════════════════════════════════════════════

### Scale Challenge: 100 Billion Queries/Month = 38,000 queries/second

**Solution 1: Caching (Most Important!)**

Most people search for the same things:
- "Python tutorial" - searched 1 million times/day
- "Weather in New York" - searched 500k times/day

Instead of hitting the database every time:
```
First search for "Python tutorial":
User → API → Redis (not found) → Elasticsearch (search) → Return result
                                   └─> Save in Redis

Next 999,999 searches for "Python tutorial":
User → API → Redis (found!) → Return result (SUPER FAST)
```

**Result:** 70-80% of searches hit cache
- Only 20-30% go to Elasticsearch
- 38,000 queries/sec → only 7,600 hit the database
- Redis can handle 100,000+ requests/second easily

**Solution 2: Multiple API Servers**

Run 100 FastAPI servers behind a load balancer:
```
User requests → Load Balancer → Picks one of 100 servers → Handles request
```

Each server handles 400 requests/second:
```
100 servers × 400 req/sec = 40,000 req/sec ✓
```

**Solution 3: Elasticsearch Cluster**

Instead of 1 big database, split data across 50 machines:
```
Machine 1: Pages 0-80 million
Machine 2: Pages 80-160 million
Machine 3: Pages 160-240 million
...
Machine 50: Pages 3.92-4 billion
```

Each machine only searches its portion → much faster!

═══════════════════════════════════════════════════════════════

## THE TWO MAIN FLOWS

### FLOW 1: User Searches for "Python tutorials"

```
Step 1: User → FastAPI: "Give me Python tutorials"
Step 2: FastAPI → Redis: "Do you have this cached?"
Step 3a: Redis: "Yes!" → Return results (DONE - 10ms)
Step 3b: Redis: "No" → Continue to Step 4
Step 4: FastAPI → Elasticsearch: "Search for Python tutorials"
Step 5: Elasticsearch searches the inverted index
Step 6: Returns top 10 results
Step 7: FastAPI saves results in Redis for next time
Step 8: FastAPI returns results to user
```

**Time:** 50-200ms per search

═══════════════════════════════════════════════════════════════

### FLOW 2: User Requests Re-crawl of "example.com"

```
Step 1: User → FastAPI: "Re-crawl example.com"
Step 2: FastAPI → PostgreSQL: Save job (ID: #12345, Status: Pending)
Step 3: FastAPI → RabbitMQ: Add job to queue
Step 4: FastAPI → User: "Job created! ID: #12345"

[Meanwhile, in the background...]

Step 5: Crawler Worker → RabbitMQ: "Give me a job"
Step 6: RabbitMQ → Worker: "Here's job #12345: crawl example.com"
Step 7: Worker → example.com: Download HTML
Step 8: Worker → S3: Save raw HTML
Step 9: Worker → Text Processor: "Process this HTML"
Step 10: Text Processor: Extract text, remove junk, tokenize
Step 11: Text Processor → Indexer: "Here are the tokens"
Step 12: Indexer → Elasticsearch: Update the inverted index
Step 13: Worker → PostgreSQL: Update job (Status: Completed)

[User can check status anytime]
User → FastAPI: "What's the status of job #12345?"
FastAPI → PostgreSQL: Check status
FastAPI → User: "Status: Completed!"
```

**Time:** Less than 1 hour (as required by SLA)

═══════════════════════════════════════════════════════════════

## WHAT IS AN INVERTED INDEX?

Think of a book's index at the back:

**Normal way (slow):**
"Let me read all 1000 pages to find mentions of 'Python'"

**Inverted index way (fast):**
```
Index:
- Python: pages 5, 67, 234, 890
- Tutorial: pages 12, 67, 234, 456
- Django: pages 234, 567, 890
```

You just look up "Python" and immediately know it's on pages 5, 67, 234, 890!

**In our search engine:**
```
Token "python" appears in:
- Document #123 (example.com/learn)
- Document #456 (tutorial.com/python)
- Document #789 (docs.python.org)
```

Instead of scanning 4 billion documents, we just look up the token!

═══════════════════════════════════════════════════════════════

## SCALING SUMMARY - SIMPLE MATH

### Crawling (4 billion pages/month):
```
4,000,000,000 pages ÷ 30 days = 133,333,333 pages/day
133,333,333 pages/day ÷ 24 hours = 5,555,555 pages/hour  
5,555,555 pages/hour ÷ 3600 seconds = 1,543 pages/second

Solution: Run 1,500-2,000 crawler workers in parallel
```

### Searching (100 billion queries/month):
```
100,000,000,000 queries ÷ 30 days = 3,333,333,333 queries/day
3,333,333,333 queries/day ÷ 24 hours = 138,888,888 queries/hour
138,888,888 queries/hour ÷ 3600 seconds = 38,580 queries/second

Solution: 
- 80% cache hit rate → 30,864 cached (Redis handles easily)
- 20% hit database → 7,716 (Elasticsearch cluster handles this)
- 100 FastAPI servers × 400 req/sec = 40,000 req/sec capacity
```

═══════════════════════════════════════════════════════════════

## WHY EACH TECHNOLOGY?

**FastAPI**: Fast Python framework, handles many requests at once
**Redis**: Super fast in-memory cache (microsecond response)
**Elasticsearch**: Built specifically for searching huge amounts of text
**RabbitMQ**: Reliable job queue, ensures no jobs are lost
**PostgreSQL**: Reliable database for structured data
**S3**: Cheap storage for billions of HTML files
**Docker + Kubernetes**: Easy to run thousands of workers

═══════════════════════════════════════════════════════════════
