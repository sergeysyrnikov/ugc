---
name: django-models
description: Guides Django model design and implementation: field choice, relations, Meta options, migrations, and conventions. Use when creating or refactoring Django models, designing schemas, or discussing data modeling in Django.
---

# Django Models Skill

## Purpose

This skill defines how to design and create Django models in this project:
- consistent field and relation usage;
- clean and explicit schema design;
- safe migration workflow;
- reusable patterns (base models, choices, managers).

The goal is to keep models **explicit, predictable, and easy to query**.

## General principles

- Treat models as the **single source of truth** for the database schema.
- Prefer **small, focused models** with clear responsibility.
- Avoid storing derived or easily computed data unless there is a clear performance reason.
- Always think about **query patterns** when designing fields and relations (what will be filtered/ordered/aggregated).
- Keep naming consistent and descriptive.
- Always define `verbose_name` and `verbose_name_plural` for each model in `class Meta` so that admin and auto-generated UIs use clear human-readable names.
- Always define `verbose_name` for every field to control how field labels appear in the admin and in forms.

## Naming conventions

- Model names: **PascalCase**, singular (`Article`, `UserProfile`).
- Field names: **snake_case**, descriptive (`created_at`, `is_active`, `full_name`).
- Use `_at` for datetimes (`created_at`, `updated_at`) and `_on` for dates (`published_on`).
- Use `is_` / `has_` prefixes for booleans (`is_active`, `has_access`).

## Base model pattern

For most domain models, prefer a timestamped base model:

```python
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps."""

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

Usage:

```python
class Article(TimeStampedModel):
    """Represents a published article."""

    title: models.CharField = models.CharField(max_length=255, db_index=True)
    body: models.TextField = models.TextField()
    is_published: models.BooleanField = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
```

## Field selection guidelines

### Strings

- Use `CharField` for short text (titles, names, slugs). Always set `max_length`.
- Use `TextField` for long text (descriptions, bodies).
- Use `SlugField` for URL slugs; combine with `unique=True` or unique constraints where necessary.

### Numbers and money

- Use `IntegerField` / `BigIntegerField` for counts and IDs.
- Use `DecimalField` for money and precise numeric values (set `max_digits` and `decimal_places`).

### Booleans

- Use `BooleanField` with `default` (`default=False` or `default=True` as appropriate).
- If tri-state logic is needed, explicitly use `NullBooleanField` pattern via `BooleanField(null=True)` and handle it carefully.

### Dates and times

- Use `DateTimeField` with `auto_now_add` / `auto_now` for created/updated tracking.
- Use `DateField` for date-only concepts (birthdays, calendar days).

### Relations

- `ForeignKey` for many-to-one relationships (most common).
- `OneToOneField` when there is exactly one related row (e.g., `User` ↔ `Profile`).
- `ManyToManyField` for many-to-many relations; consider through models when you need extra fields on the relation.

Always set the `related_name` explicitly to avoid ambiguity in reverse relations.

```python
class Author(TimeStampedModel):
    full_name: models.CharField = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.full_name


class Article(TimeStampedModel):
    author: models.ForeignKey = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="articles",
    )
    # other fields...
```

## Choices and enums

For a fixed set of values, use `TextChoices` or `IntegerChoices`:

```python
from django.db import models


class ArticleStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class Article(TimeStampedModel):
    status: models.CharField = models.CharField(
        max_length=16,
        choices=ArticleStatus.choices,
        default=ArticleStatus.DRAFT,
        db_index=True,
    )
```

Benefits:
- validation at the model level;
- consistent values across the codebase;
- easier to filter and aggregate by status.

## Meta options and indexes

Use `Meta` to codify common behaviors:

- `ordering` for default queryset ordering.
- `unique_together` or `UniqueConstraint` for composite uniqueness.
- `indexes` for frequent filters/sorts.

Example:

```python
from django.db import models


class Subscription(TimeStampedModel):
    user: models.ForeignKey = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    plan_code: models.CharField = models.CharField(max_length=64)
    is_active: models.BooleanField = models.BooleanField(default=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "plan_code"],
                name="subscription_user_plan_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["is_active", "created_at"]),
        ]
```

## Field verbose_name style

For simple non-relational fields (e.g. `CharField`, `TextField`, `BooleanField`, numeric fields), prefer using the first positional argument as `verbose_name` and then keyword arguments for everything else:

```python
from django.db import models
class Article(TimeStampedModel):
"""Represents a published article."""
title: models.CharField = models.CharField(
"Title",
max_length=255,
)
body: models.TextField = models.TextField(
"Body",
)
is_published: models.BooleanField = models.BooleanField(
"Is published",
default=False,
db_index=True,
)
```

For relational fields such as `ForeignKey`, `OneToOneField`, and `ManyToManyField`, the first positional arguments are reserved for the related model (and sometimes `on_delete`), so `verbose_name` must always be provided as a keyword argument:

```python
class Article(TimeStampedModel):
    author: models.ForeignKey = models.ForeignKey(
        "auth.User",
        models.CASCADE,
        verbose_name="Author",
        related_name="articles",
    )
```
Every field must effectively have a verbose_name: either implicitly derived from the field name (no positional arguments at all) or explicitly provided as the first positional argument (for simple fields) or as a verbose_name= keyword argument (for relational fields).

Use sentence case labels with capitalized first letter (e.g. Title, Created at) to match Django’s default.

## Model methods and managers

### Instance methods

## Verbose names convention

For every model:

- Set `verbose_name` and `verbose_name_plural` in `class Meta`:

```python
from django.db import models


class Article(TimeStampedModel):
    """Represents a published article."""

    title: models.CharField = models.CharField(
        max_length=255,
        verbose_name="Title",
    )
    body: models.TextField = models.TextField(
        verbose_name="Body",
    )
    is_published: models.BooleanField = models.BooleanField(
        default=False,
        verbose_name="Is published",
        db_index=True,
    )

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ["-created_at"]
```

Use instance methods for behavior tied to a single row:

```python
class Subscription(TimeStampedModel):
    # fields...

    def deactivate(self) -> None:
        """Deactivate subscription if it is active."""
        if not self.is_active:
            return
        self.is_active = False
        self.save(update_fields=["is_active"])
```

### Custom queryset / manager

Use custom querysets/managers for reusable filtering logic:

```python
class SubscriptionQuerySet(models.QuerySet):
    def active(self) -> "SubscriptionQuerySet":
        return self.filter(is_active=True)


class Subscription(TimeStampedModel):
    # fields...

    objects: SubscriptionQuerySet = SubscriptionQuerySet.as_manager()
```

Usage:

```python
active_subscriptions = Subscription.objects.active()
```

## Migrations workflow

When creating or changing models:

1. Modify models in `models.py`.
2. Run:

```bash
uv run manage.py makemigrations
uv run manage.py migrate
```

3. Review generated migration files (field types, defaults, constraints).
4. Avoid manual edits to migration files unless strictly necessary; if edited, ensure they still apply cleanly on a fresh database.

Never change existing migrations that have already been applied to shared environments; create **new** migrations instead.

## Validation and constraints

- Use field-level validation (`max_length`, `blank`, `null`, `choices`) wherever possible.
- For cross-field validation, use `clean()` or `Model.clean()` when needed.
- Prefer database-level constraints (unique, check constraints) for invariants that must never be violated.

Example check constraint:

```python
from django.db import models
from django.db.models import Q


class Booking(TimeStampedModel):
    starts_at: models.DateTimeField = models.DateTimeField()
    ends_at: models.DateTimeField = models.DateTimeField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(ends_at__gt=models.F("starts_at")),
                name="booking_ends_after_start",
            ),
        ]
```

## Serialization considerations

When designing models, think about how they will be exposed through APIs (e.g., via DRF):

- Use simple field types that serialize well (avoid storing complex JSON unless needed).
- Prefer foreign keys over denormalized text references.
- Avoid circular relations when possible or handle them carefully in serializers.

## How to use this skill

When creating or refactoring Django models in this project:

- follow the naming and base model patterns defined above;
- choose fields and relations based on query patterns and invariants;
- define Meta options (ordering, constraints, indexes) explicitly for important models;
- use custom querysets/managers for reusable filtering logic;
- ensure migrations are created and applied via `uv run manage.py makemigrations` and `uv run manage.py migrate`;
- keep models small, explicit, and easy to query. 

