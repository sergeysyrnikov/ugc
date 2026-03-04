---
name: django-orm
description: Provides Django ORM best practices, query patterns, and debugging workflows. Use when working with Django models, querysets, database performance, or when the user mentions Django ORM, models, migrations, or query optimization.
---

# Django ORM Skill

## Purpose

This skill helps to work with Django ORM in this project: from basic operations to debugging and query optimization.

Focus areas:
- creating and modifying models;
- typical CRUD operations through ORM;
- filtering, querying, and aggregations;
- optimization (N+1, indexes, `select_related`, `prefetch_related`);
- debugging and profiling queries.

## General principles

- **Use Django ORM**, not raw SQL, except for narrow performance hotspots.
- **All models** must inherit from `django.db.models.Model`.
- **Migrations** are created via `makemigrations` and applied via `migrate`; do not edit migration files by hand unless absolutely necessary.
- **Business logic** related to data access should live in model methods/managers where possible, not in views.

## Working with models

### Creating a model

When adding a new model:

1. Define the model in `app/models.py`.
2. Declare fields and constraints explicitly (`unique`, `db_index`, `null`, `blank`).
3. Add `__str__` for human‑readable representation.
4. Generate and apply migrations:

```bash
uv run manage.py makemigrations
uv run manage.py migrate
```

Example:

```python
from django.db import models


class Article(models.Model):
    """Represents a published article."""

    title: models.CharField = models.CharField(max_length=255, db_index=True)
    body: models.TextField = models.TextField()
    is_published: models.BooleanField = models.BooleanField(default=False, db_index=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_published", "created_at"]),
        ]

    def __str__(self) -> str:
        return self.title
```

### Modifying a model

When changing a model:
- first update the model definition;
- then always create and apply migrations:

```bash
uv run manage.py makemigrations
uv run manage.py migrate
```

## CRUD operations via ORM

### Creating objects

```python
article: Article = Article.objects.create(
    title="Example",
    body="Body",
    is_published=True,
)
```

Or:

```python
article: Article = Article(
    title="Example",
    body="Body",
)
article.is_published = True
article.save()
```

### Reading objects

```python
qs = Article.objects.filter(is_published=True)
first_article: Article | None = qs.first()

try:
    article: Article = Article.objects.get(pk=1)
except Article.DoesNotExist:
    article = None
```

### Updating objects

```python
Article.objects.filter(is_published=False).update(is_published=True)
```

### Deleting objects

```python
Article.objects.filter(is_published=False).delete()
```

## Query optimization

### Avoiding N+1

- For `ForeignKey` and `OneToOneField` use `select_related`.
- For `ManyToMany` and reverse relations use `prefetch_related`.

```python
articles = Article.objects.select_related("author").prefetch_related("tags").all()
```

### Limiting selected fields

When you only need a few fields:

```python
titles = Article.objects.filter(is_published=True).values_list("id", "title")
```

### Indexes

- For frequently filtered/sorted fields use `db_index=True` or `indexes` in `Meta`.
- Do not add indexes without real need (balance between speed and DB size).

## Aggregations and annotations

```python
from django.db.models import Count

authors = (
    Author.objects.annotate(articles_count=Count("article"))
    .filter(articles_count__gt=0)
    .order_by("-articles_count")
)
```

## Debugging ORM queries

### Inspecting SQL in shell

```bash
uv run manage.py shell
```

```python
from django.db import connection
from app.models import Article

qs = Article.objects.filter(is_published=True)
print(qs.query)  # Shows SQL

for query in connection.queries:
    print(query["sql"], query["time"])
```

### Query logging

When needed, you can temporarily enable DEBUG logging for `django.db.backends` in `settings.py` (do not keep it enabled in production).

## Typical workflows

### When to add managers and model methods

- If query logic is reused in several places, move it into a custom manager or queryset.
- If logic belongs to a single instance, move it into a model method.

Example:

```python
from django.db import models


class PublishedArticleQuerySet(models.QuerySet):
    def published(self) -> "PublishedArticleQuerySet":
        return self.filter(is_published=True)


class Article(models.Model):
    # fields...

    objects: PublishedArticleQuerySet = PublishedArticleQuerySet.as_manager()

    def publish(self) -> None:
        """Mark article as published."""
        if self.is_published:
            return
        self.is_published = True
        self.save(update_fields=["is_published"])
```

Usage:

```python
articles = Article.objects.published()
```

## How to use this skill

- When working with Django ORM, models, migrations, or query optimization:
  - follow the patterns described above;
  - suggest `select_related` / `prefetch_related` when there is risk of N+1;
  - propose indexes for frequently used filters/orderings;
  - use the code examples in this file as templates when generating responses.

