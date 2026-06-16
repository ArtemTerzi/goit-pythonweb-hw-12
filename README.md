# REST API for Contacts Management (Contacts API)

[English](#english) | [Українська](#українська)

---

<a name="english"></a>
## English Version

An asynchronous web application based on **FastAPI** and **SQLAlchemy 2.0**, designed to store, search, and manage contacts. The project supports user registration, JWT authorization, avatar uploads via the Cloudinary cloud service, sending emails (SMTP), rate limiting via `slowapi`, and containerization using Docker Compose.

### 🛠 Tech Stack

* **Python 3.12+**
* **FastAPI** (ASGI web framework)
* **SQLAlchemy 2.0** (ORM in async mode)
* **PostgreSQL + asyncpg** (DBMS and async driver)
* **Alembic** (database migration management)
* **Pydantic v2** (data validation and serialization)
* **Poetry** (virtual environment and dependency management)
* **Docker & Docker Compose** (containerization)
* **Cloudinary** (user avatar storage and transformation)
* **Redis** (caching the authenticated user to offload the database)
* **Slowapi** (rate limiting for spam protection)
* **Bcrypt / Jose (python-jose)** (password hashing and JWT token operations)

---

### ⚙️ Environment Variables Configuration

The project ships with a ready-to-use **`.env.example`** filled with safe placeholder values (no real credentials). For a quick start you can simply copy it — the application boots as-is:

```bash
cp .env.example .env
```

A few things worth knowing:

* **`POSTGRES_*`** are the single source of truth for the database connection — `DB_URL` is assembled from them automatically, so you never edit it by hand. `POSTGRES_PORT=5434` matches the bundled docker `db` container's external port; set it to `5432` if you connect to your own local PostgreSQL.
* **`JWT_SECRET`** — change it to your own long random string for anything beyond local development.
* **`MAIL_*`** and **`CLOUDINARY_*`** are optional: the app starts without them (email sending and avatar upload simply stay disabled until you provide real values).
* **`REDIS_*`** are optional too: if Redis is unavailable, the user cache degrades gracefully to direct database access.

---

### 🚀 Quick Start via Docker Compose (Recommended)

The easiest way to run the entire project (FastAPI web server and PostgreSQL database) with automatic migration application:

1. Make sure **Docker** / **Docker Desktop** is running on your computer.
2. Navigate to the project folder and run:
   ```bash
   docker compose up --build
   ```
3. The server will automatically run `alembic upgrade head` to create tables and start at:
   * **Application:** `http://localhost:8001` (according to the `8001:8000` port mapping in your compose file).
   * **Documentation (Swagger UI):** `http://localhost:8001/docs`.

---

### 💻 Local Run (without Docker Compose)

If you want to run the database in Docker but execute the application on the host:

#### 1. Start the database (and optionally Redis) in Docker
```bash
docker compose up -d db
# optionally, to enable the cache layer locally:
docker compose up -d db redis
```
> Redis is optional — if it is not running, the cache degrades gracefully to direct DB access.

#### 2. Prepare `.env`
Copy the template; its defaults (`POSTGRES_HOST=localhost`, `POSTGRES_PORT=5434`) already match the bundled `db` container:
```bash
cp .env.example .env
```
> If you use your own local PostgreSQL instead of the `db` container, set `POSTGRES_PORT=5432` (and the matching user/password) in `.env`.

#### 3. Install dependencies
```bash
poetry install
```

#### 4. Run database migrations
This creates the database automatically if it doesn't exist yet, then applies all migrations:
```bash
poetry run alembic upgrade head
```

#### 5. (Optional) Seed pre-confirmed users
Creates ready-to-use accounts so you can log in without registering:
```bash
poetry run python seed.py
```

#### 6. Start the development server
```bash
poetry run python main.py
# or
poetry run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
The application will be available at `http://127.0.0.1:8000/docs`.

---

### 👥 Seed Users

Running `seed.py` inserts the following **already-confirmed** accounts, so you can log in immediately via `POST /api/auth/login` without registration or email confirmation. The script is idempotent (existing users are skipped by email), so it is safe to run repeatedly.

| Role | Email | Password |
| :--- | :--- | :--- |
| `admin` | `admin@example.com` | `admin12345` |
| `user` | `user@example.com` | `user12345` |

> These are local-development credentials — change the `SEED_USERS` list in `seed.py` for anything else.

---

### 🧪 Running Tests

The test suite is **fully self-contained** — it runs against an in-memory SQLite database and an in-memory Redis fake (`fakeredis`). You need **no `.env` file, no PostgreSQL, and no Redis** to run it: the required settings are provided automatically by `tests/conftest.py`, so a fresh clone can run the tests immediately.

#### 1. Install dependencies (includes the dev tools)
```bash
poetry install
```

#### 2. Run the whole suite
```bash
poetry run pytest
```

#### 3. Useful variations
```bash
poetry run pytest -v                                                  # one line per test
poetry run pytest tests/test_integration_auth.py                      # a single file
poetry run pytest tests/test_integration_auth.py::test_login_success  # a single test
poetry run pytest -x                                                  # stop at the first failure
```

#### 4. Coverage report
Coverage is pre-configured in `pyproject.toml` (it measures the `src` package and omits the e-mail helper). For a terminal report listing the uncovered lines:
```bash
poetry run pytest --cov=src --cov-report=term-missing
```
For a browsable HTML report (then open `htmlcov/index.html`):
```bash
poetry run pytest --cov=src --cov-report=html
```
> Current total coverage is ~94%.

#### What the tests cover
| File | Type | Scope |
| :--- | :--- | :--- |
| `tests/test_user_repository_unit.py` | Unit | User repository methods (mocked DB session) |
| `tests/test_contact_repository_unit.py` | Unit | Contact repository methods (mocked DB session) |
| `tests/test_cache_unit.py` | Unit | Redis user-cache serialization and invalidation |
| `tests/test_integration_auth.py` | Integration | Signup, login, token refresh, email confirmation, password reset |
| `tests/test_integration_users.py` | Integration | Profile (`/me`) and role-restricted avatar update |
| `tests/test_intrgration_contacts.py` | Integration | Contacts CRUD, search, upcoming birthdays |
| `tests/test_integration_utils.py` | Integration | Health-check endpoint |

---

### 📖 Main API Endpoints

All requests to contacts and user profiles require authorization via the `Authorization: Bearer <token>` header.

#### 🔐 Authentication (`/api/auth`)
| Method | Route | Description |
| :--- | :--- | :--- |
| **POST** | `/api/auth/signup` | Register a new user (sends verification email) |
| **POST** | `/api/auth/login` | User login (returns Access and Refresh tokens) |
| **POST** | `/api/auth/refresh-token` | Refresh Access token using Refresh token |
| **GET** | `/api/auth/secret` | Protected route for testing access |
| **POST** | `/api/auth/reset_password` | Request a password reset link by email |
| **GET** | `/api/auth/reset_password/{token}` | Render the HTML page with the new-password form (the link from the email) |
| **POST** | `/api/auth/reset_password/{token}` | Set a new password using the emailed reset token |

#### 👤 Users (`/api/users`)
| Method | Route | Description |
| :--- | :--- | :--- |
| **GET** | `/api/users/me` | Retrieve the current authorized user's profile |
| **PATCH** | `/api/users/avatar` | Update user avatar (upload to Cloudinary). **Admins only** (`role = admin`); regular users receive `403 Forbidden` |

#### 📞 Contacts (`/api/contacts`)
| Method | Route | Description |
| :--- | :--- | :--- |
| **GET** | `/api/contacts/` | Retrieve contact list for the current user (with pagination and search by name, last_name, email) |
| **GET** | `/api/contacts/birthdays` | Retrieve contacts with birthdays in the next 7 days |
| **GET** | `/api/contacts/{contact_id}` | Retrieve detailed information about a specific contact |
| **POST** | `/api/contacts/` | Create a new contact for the authorized user |
| **PATCH** | `/api/contacts/{contact_id}` | Partially update information of an existing contact |
| **DELETE** | `/api/contacts/{contact_id}` | Delete a contact from the database |

---

### 🛑 Rate Limiting

To prevent overload or abuse of resources, **`slowapi`** is integrated.
* Endpoints for creating and updating users/contacts have rate limits per minute from a single IP address.
* Exceeding the limit will result in a `429 Too Many Requests` error.

---

### ✨ Key Features

* **Redis caching of the current user.** On every authorized request, `get_current_user` first looks the user up in Redis (key `user:{username}`). The database is queried only on a cache miss, after which the user is cached with a configurable TTL (`REDIS_CACHE_TTL`). The cache is invalidated on login, token refresh, password reset, and avatar change. If Redis is unavailable, the application degrades gracefully and falls back to direct database access.
* **Password reset.** `POST /api/auth/reset_password` emails a short-lived, single-purpose JWT (`token_type = "reset"`). The link in the email opens `GET /api/auth/reset_password/{token}`, which renders an HTML page with a new-password form; that page submits a `POST` to the same URL, which validates the token and stores the new password hash (clearing the refresh token to invalidate old sessions). To avoid account enumeration, the request endpoint always returns the same generic message regardless of whether the email exists.
* **User roles and access control.** Each user has a `role` of either `user` or `admin`. A reusable `RoleAccess` dependency enforces role requirements; the avatar update endpoint is restricted to administrators via `get_admin_user`.
* **Self-healing startup.** Before migrations run, the target database is created automatically if it doesn't exist (see `src/database/create_db.py`), so a fresh server never fails with "database does not exist".
* **Seedable users.** `seed.py` inserts pre-confirmed accounts for instant login (run locally, or automatically on every Render deploy).
* **Boot without secrets.** `MAIL_*` and `CLOUDINARY_*` have safe defaults, so the app starts even when those credentials are not configured (those features simply stay disabled).

---

<a name="українська"></a>
## Українська версія

Асинхронний вебзастосунок на базі **FastAPI** та **SQLAlchemy 2.0**, призначений для збереження, пошуку та керування контактами. Проєкт підтримує реєстрацію користувачів, JWT-авторизацію, завантаження аватарів через хмарний сервіс Cloudinary, надсилання листів (SMTP), обмеження швидкості запитів (Rate Limiting) за допомогою `slowapi` та запуск усього середовища через Docker Compose.

### 🛠 Технологічний стек

* **Python 3.12+**
* **FastAPI** (ASGI вебфреймворк)
* **SQLAlchemy 2.0** (ORM з асинхронним режимом)
* **PostgreSQL + asyncpg** (СУБД та асинхронний драйвер)
* **Alembic** (керування міграціями бази даних)
* **Pydantic v2** (валідація та серіалізація даних)
* **Poetry** (керування віртуальним середовищем та залежностями)
* **Docker & Docker Compose** (контейнеризація бази даних та додатку)
* **Cloudinary** (збереження та трансформація аватарів користувачів)
* **Redis** (кешування авторизованого користувача для розвантаження бази даних)
* **Slowapi** (обмеження кількості запитів для захисту від спаму)
* **Bcrypt / Jose (python-jose)** (хешування паролів та робота з JWT-токенами)

---

### ⚙️ Налаштування змінних оточення

У проєкті є готовий **`.env.example`**, заповнений безпечними значеннями-заглушками (без реальних креденшелів). Для швидкого старту його достатньо скопіювати — застосунок запуститься як є:

```bash
cp .env.example .env
```

Що варто знати:

* **`POSTGRES_*`** — єдине джерело правди для підключення до БД; `DB_URL` збирається з них автоматично, тож вручну його не редагують. `POSTGRES_PORT=5434` відповідає зовнішньому порту контейнера `db` із docker-compose; якщо ви підключаєтесь до власного локального PostgreSQL — поставте `5432`.
* **`JWT_SECRET`** — для будь-чого, окрім локальної розробки, замініть на власний довгий випадковий рядок.
* **`MAIL_*`** і **`CLOUDINARY_*`** — необов'язкові: застосунок стартує й без них (надсилання пошти та завантаження аватара просто лишаються вимкненими, доки не задасте реальні значення).
* **`REDIS_*`** — теж необов'язкові: якщо Redis недоступний, кеш «м'яко» деградує до прямого доступу до БД.

---

### 🚀 Швидкий запуск через Docker Compose (Рекомендовано)

Найпростіший спосіб запустити весь проєкт (вебсервер FastAPI та базу даних PostgreSQL) з автоматичним виконанням міграцій:

1. Переконайтеся, що на вашому комп'ютері запущено **Docker** / **Docker Desktop**.
2. Перейдіть до папки проєкту та виконайте команду:
   ```bash
   docker compose up --build
   ```
3. Сервер автоматично виконає команду `alembic upgrade head` для створення таблиць і запуститься за адресою:
   * **Додаток:** `http://localhost:8001` (відповідно до конфігурації портів `8001:8000` у вашому compose-файлі).
   * **Документація (Swagger UI):** `http://localhost:8001/docs`.

---

### 💻 Локальний запуск (без Docker Compose)

Якщо ви бажаєте запустити базу даних у Docker, а сам додаток виконувати на хості:

#### 1. Запуск бази даних (і за бажанням Redis) у Docker
```bash
docker compose up -d db
# за бажанням, щоб увімкнути шар кешування локально:
docker compose up -d db redis
```
> Redis необов'язковий — якщо він не запущений, кеш «м'яко» деградує до прямого доступу до БД.

#### 2. Підготовка `.env`
Скопіюйте шаблон; його дефолти (`POSTGRES_HOST=localhost`, `POSTGRES_PORT=5434`) уже відповідають контейнеру `db`:
```bash
cp .env.example .env
```
> Якщо замість контейнера `db` ви користуєтесь власним локальним PostgreSQL — вкажіть у `.env` `POSTGRES_PORT=5432` (та відповідні user/password).

#### 3. Встановлення залежностей
```bash
poetry install
```

#### 4. Виконання міграцій бази даних
Тут же автоматично створюється база, якщо її ще немає, після чого накатуються всі міграції:
```bash
poetry run alembic upgrade head
```

#### 5. (Необов'язково) Створення заздалегідь підтверджених користувачів
Створює готові акаунти, щоб одразу залогінитись без реєстрації:
```bash
poetry run python seed.py
```

#### 6. Запуск сервера розробки
```bash
poetry run python main.py
# або
poetry run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
Додаток буде доступний за адресою `http://127.0.0.1:8000/docs`.

---

### 👥 Початкові користувачі (Seed)

Запуск `seed.py` додає такі **вже підтверджені** акаунти, тож можна одразу логінитись через `POST /api/auth/login` без реєстрації та підтвердження пошти. Скрипт ідемпотентний (наявні користувачі пропускаються за email), тож його безпечно запускати повторно.

| Роль | Email | Пароль |
| :--- | :--- | :--- |
| `admin` | `admin@example.com` | `admin12345` |
| `user` | `user@example.com` | `user12345` |

> Це креденшели для локальної розробки — для іншого змініть список `SEED_USERS` у `seed.py`.

---

### 🧪 Запуск тестів

Набір тестів **повністю самодостатній** — він працює з базою SQLite в пам'яті та in-memory підробкою Redis (`fakeredis`). Для запуску **не потрібні ані `.env`, ані PostgreSQL, ані Redis**: потрібні налаштування автоматично задаються у `tests/conftest.py`, тож свіжий клон можна тестувати одразу.

#### 1. Встановлення залежностей (разом із dev-інструментами)
```bash
poetry install
```

#### 2. Запуск усіх тестів
```bash
poetry run pytest
```

#### 3. Корисні варіанти запуску
```bash
poetry run pytest -v                                                  # по рядку на кожен тест
poetry run pytest tests/test_integration_auth.py                      # один файл
poetry run pytest tests/test_integration_auth.py::test_login_success  # один тест
poetry run pytest -x                                                  # зупинитися на першій помилці
```

#### 4. Звіт про покриття (coverage)
Покриття попередньо налаштоване в `pyproject.toml` (вимірюється пакет `src`, поштовий помічник виключено). Звіт у терміналі з переліком непокритих рядків:
```bash
poetry run pytest --cov=src --cov-report=term-missing
```
HTML-звіт для перегляду в браузері (потім відкрийте `htmlcov/index.html`):
```bash
poetry run pytest --cov=src --cov-report=html
```
> Поточне загальне покриття — ~94%.

#### Що покривають тести
| Файл | Тип | Область |
| :--- | :--- | :--- |
| `tests/test_user_repository_unit.py` | Модульні | Методи репозиторію користувачів (з моком сесії БД) |
| `tests/test_contact_repository_unit.py` | Модульні | Методи репозиторію контактів (з моком сесії БД) |
| `tests/test_cache_unit.py` | Модульні | Серіалізація та скидання кешу користувачів у Redis |
| `tests/test_integration_auth.py` | Інтеграційні | Реєстрація, вхід, оновлення токенів, підтвердження пошти, скидання пароля |
| `tests/test_integration_users.py` | Інтеграційні | Профіль (`/me`) та оновлення аватара з обмеженням за роллю |
| `tests/test_intrgration_contacts.py` | Інтеграційні | CRUD контактів, пошук, найближчі дні народження |
| `tests/test_integration_utils.py` | Інтеграційні | Ендпоінт перевірки стану (health-check) |

---

### 📖 Основні маршрути API (Endpoints)

Усі запити до контактів та профілю користувача вимагають авторизації за допомогою заголовка `Authorization: Bearer <token>`.

#### 🔐 Автентифікація (`/api/auth`)
| Метод | Маршрут | Опис |
| :--- | :--- | :--- |
| **POST** | `/api/auth/signup` | Реєстрація нового користувача (надсилає лист верифікації) |
| **POST** | `/api/auth/login` | Вхід користувача (повертає Access та Refresh токени) |
| **POST** | `/api/auth/refresh-token` | Оновлення Access токена за допомогою Refresh токена |
| **GET** | `/api/auth/secret` | Тестовий захищений маршрут для перевірки доступу |
| **POST** | `/api/auth/reset_password` | Запит на надсилання листа для скидання пароля |
| **GET** | `/api/auth/reset_password/{token}` | HTML-сторінка з формою для введення нового пароля (посилання з листа) |
| **POST** | `/api/auth/reset_password/{token}` | Встановлення нового пароля за токеном із листа |

#### 👤 Користувачі (`/api/users`)
| Метод | Маршрут | Опис |
| :--- | :--- | :--- |
| **GET** | `/api/users/me` | Отримання профілю поточного авторизованого користувача |
| **PATCH** | `/api/users/avatar` | Оновлення аватара (завантаження на Cloudinary). **Лише для адміністраторів** (`role = admin`); звичайні користувачі отримують `403 Forbidden` |

#### 📞 Контакти (`/api/contacts`)
| Метод | Маршрут | Опис |
| :--- | :--- | :--- |
| **GET** | `/api/contacts/` | Отримання списку контактів поточного користувача (з пагінацією та пошуком за name, last_name, email) |
| **GET** | `/api/contacts/birthdays` | Отримання контактів, у яких день народження буде в найближчі 7 днів |
| **GET** | `/api/contacts/{contact_id}` | Отримання детальної інформації про конкретний контакт |
| **POST** | `/api/contacts/` | Створення нового контакту для авторизованого користувача |
| **PATCH** | `/api/contacts/{contact_id}` | Часткове оновлення інформації про наявний контакт |
| **DELETE** | `/api/contacts/{contact_id}` | Видалення контакту з бази даних |

---

### 🛑 Обмеження швидкості запитів (Rate Limiting)

Для запобігання перевантаженню або зловживанню ресурсами (наприклад, DDoS-атакам) інтегровано бібліотеку **`slowapi`**. 
* Ендпоінти створення та оновлення користувачів / контактів мають ліміти на кількість запитів за хвилину з однієї IP-адреси.
* У разі перевищення ліміту сервер поверне помилку `429 Too Many Requests`.

---

### ✨ Ключові можливості

* **Кешування поточного користувача в Redis.** На кожен авторизований запит функція `get_current_user` спершу шукає користувача в Redis (ключ `user:{username}`). До бази даних застосунок звертається лише за відсутності запису в кеші, після чого користувач кешується із заданим часом життя (`REDIS_CACHE_TTL`). Кеш скидається під час входу, оновлення токенів, скидання пароля та зміни аватара. Якщо Redis недоступний, застосунок продовжує працювати, звертаючись напряму до бази даних.
* **Скидання пароля.** `POST /api/auth/reset_password` надсилає короткоживучий одноразовий JWT (`token_type = "reset"`). Посилання з листа відкриває `GET /api/auth/reset_password/{token}` — HTML-сторінку з формою для нового пароля; ця сторінка надсилає `POST` на ту саму адресу, який перевіряє токен і зберігає новий хеш пароля (очищаючи refresh-токен, щоб завершити старі сесії). Щоб уникнути розкриття зареєстрованих адрес, ендпоінт запиту завжди повертає однакове повідомлення незалежно від наявності користувача.
* **Ролі користувачів і доступ.** Кожен користувач має роль `user` або `admin`. Універсальна залежність `RoleAccess` перевіряє роль; оновлення аватара дозволено лише адміністраторам через залежність `get_admin_user`.
* **Самовідновлюваний старт.** Перед міграціями цільова база створюється автоматично, якщо її немає (`src/database/create_db.py`), тож на свіжому сервері не буде помилки «database does not exist».
* **Початкові користувачі (seed).** `seed.py` додає заздалегідь підтверджені акаунти для миттєвого входу (локально або автоматично під час кожного розгортання на Render).
* **Старт без секретів.** `MAIL_*` і `CLOUDINARY_*` мають безпечні дефолти, тож застосунок стартує, навіть коли ці креденшели не налаштовані (відповідні функції просто лишаються вимкненими).

---