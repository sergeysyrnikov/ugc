---
name: django-env-dev
description: Uses env.dev in the ugc project when running Django manage.py commands. Apply when the user asks to run Django management commands or Django-related scripts in this repository and does not explicitly specify another environment file.
---

# Django env.dev management commands

## Instructions

- This skill is **project-specific** for the `ugc` Django project.
- The project root is the directory that contains `manage.py` and `env.dev`.
- The `env.dev` file stores environment variables for local development, including PostgreSQL connection settings and Django settings flags.

When the user asks to run Django management commands in this project (for example: `python manage.py migrate`, `runserver`, `createsuperuser`), assume **development** by default unless they clearly mention production, `env.prod`, Docker, or another environment.

### Preferred patterns

**If the user is running commands manually in a shell:**

- Recommend loading `env.dev` once per terminal session, then using plain `python manage.py ...`:

```bash
cd /home/sergey/ProjectsWithOpenAI/ugc
set -a
source ./env.dev
set +a

python manage.py migrate
python manage.py runserver
```

- If the user insists on a **single-shot command** without modifying shell config, suggest:

```bash
cd /home/sergey/ProjectsWithOpenAI/ugc
env $(grep -v '^#' env.dev | xargs) python manage.py migrate
```

### When generating commands in responses

- For **short examples** in answers, prefer the simple pattern:

```bash
set -a
source ./env.dev
set +a
python manage.py migrate
```

- If the user wants the **shortest possible one-liner**, use:

```bash
env $(grep -v '^#' env.dev | xargs) python manage.py migrate
```

- If the user mentions `uv` explicitly, adapt commands to:

```bash
set -a
source ./env.dev
set +a
uv run python manage.py migrate
```

### Do not assume env.prod

- Never use `env.prod` automatically.
- Only reference `env.prod` or production settings when the user clearly requests production, deployment, Docker, or similar context.

## Examples

- **User**: "python manage.py migrate как запустить с env.dev переменными окружения?"
- **Assistant (with this skill)**:

```bash
cd /home/sergey/ProjectsWithOpenAI/ugc
set -a
source ./env.dev
set +a
python manage.py migrate
```

- **User**: "Запусти сервер разработки Django с dev env"
- **Assistant**:

```bash
cd /home/sergey/ProjectsWithOpenAI/ugc
set -a
source ./env.dev
set +a
python manage.py runserver
```

