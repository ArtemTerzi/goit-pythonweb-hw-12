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

Before running the application, create a **`.env`** file in the root directory of the project (next to `.env.example`) and fill it with configuration data.

#### `.env` File Example:

```env
# Parameters for PostgreSQL Docker container
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password
POSTGRES_DB=contacts_db

# Connection string for FastAPI (use host "db" for Docker, or "localhost" for local run)
DB_URL=postgresql+asyncpg://postgres:postgres_password@db:5432/contacts_db

# Security and JWT token configuration
JWT_SECRET=your_secret_string_for_jwt_signatures
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_MINUTES=10080

# Mail server (SMTP) configuration
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=your_email@gmail.com
MAIL_PORT=465
MAIL_SERVER=smtp.gmail.com

# Cloudinary integration for avatar storage
CLOUDINARY_NAME=your_cloudinary_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret

# Redis configuration for caching the current user
# (use host "redis" for Docker, or "localhost" for a local run)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_CACHE_TTL=900

# Lifetime (in minutes) of the password reset token
JWT_RESET_TOKEN_EXPIRE_MINUTES=60
```

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

If you want to run the database in Docker but execute the application locally:

#### 1. Start only the database in Docker
Run the PostgreSQL container (it will expose port `5434` to your computer):
```bash
docker compose up -d db
```

#### 2. Update `.env` for local execution
Since the app will run on the host machine, change `DB_URL` in your `.env` to point to `localhost` and use the external port `5434`:
```env
DB_URL=postgresql+asyncpg://postgres:postgres_password@localhost:5434/contacts_db
```

#### 3. Install dependencies and activate the virtual environment
```bash
poetry install
poetry shell
```

#### 4. Run database migrations
```bash
poetry run alembic upgrade head
```

#### 5. Start the development server
```bash
poetry run python main.py
# or
poetry run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
The application will be available at `http://127.0.0.1:8000/docs`.

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
* **Password reset.** `POST /api/auth/reset_password` emails a short-lived, single-purpose JWT (`token_type = "reset"`); `POST /api/auth/reset_password/{token}` validates it and stores the new password hash (clearing the refresh token to invalidate old sessions). To avoid account enumeration, the request endpoint always returns the same generic message regardless of whether the email exists.
* **User roles and access control.** Each user has a `role` of either `user` or `admin`. A reusable `RoleAccess` dependency enforces role requirements; the avatar update endpoint is restricted to administrators via `get_admin_user`.

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

Перед запуском застосунку обов'язково створіть файл **`.env`** у кореневій директорії проєкту (поруч із `.env.example`) та заповніть його конфігураційними даними.

#### Приклад файлу `.env`:

```env
# Параметри для Docker контейнера PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password
POSTGRES_DB=contacts_db

# Змінна підключення до БД (використовуйте хост "db" для Docker, або "localhost" для локального запуску)
DB_URL=postgresql+asyncpg://postgres:postgres_password@db:5432/contacts_db

# Налаштування безпеки та JWT-токенів
JWT_SECRET=ваша_секретна_строка_для_підпису_токенів_jwt
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_MINUTES=10080

# Налаштування поштового сервера (SMTP)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=your_email@gmail.com
MAIL_PORT=465
MAIL_SERVER=smtp.gmail.com

# Інтеграція з Cloudinary для збереження аватарів
CLOUDINARY_NAME=your_cloudinary_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret

# Налаштування Redis для кешування поточного користувача
# (використовуйте хост "redis" для Docker, або "localhost" для локального запуску)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_CACHE_TTL=900

# Час життя (у хвилинах) токена для скидання пароля
JWT_RESET_TOKEN_EXPIRE_MINUTES=60
```

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

Якщо ви бажаєте запустити базу даних у Docker, а сам додаток виконувати на локальній машині:

#### 1. Запуск лише бази даних у Docker
Запустіть контейнер PostgreSQL (він прокине порт `5434` на ваш комп'ютер):
```bash
docker compose up -d db
```

#### 2. Оновлення `.env` для локального запуску
Оскільки додаток працюватиме на хості, змініть адресу підключення `DB_URL` у вашому `.env` на локальну та вкажіть зовнішній порт `5434`:
```env
DB_URL=postgresql+asyncpg://postgres:postgres_password@localhost:5434/contacts_db
```

#### 3. Встановлення залежностей та активація середовища
```bash
poetry install
poetry shell
```

#### 4. Виконання міграцій бази даних
```bash
poetry run alembic upgrade head
```

#### 5. Запуск сервера розробки
```bash
poetry run python main.py
# або
poetry run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
Додаток буде доступний за адресою `http://127.0.0.1:8000/docs`.

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
* **Скидання пароля.** `POST /api/auth/reset_password` надсилає короткоживучий одноразовий JWT (`token_type = "reset"`); `POST /api/auth/reset_password/{token}` перевіряє його та зберігає новий хеш пароля (очищаючи refresh-токен, щоб завершити старі сесії). Щоб уникнути розкриття зареєстрованих адрес, ендпоінт запиту завжди повертає однакове повідомлення незалежно від наявності користувача.
* **Ролі користувачів і доступ.** Кожен користувач має роль `user` або `admin`. Універсальна залежність `RoleAccess` перевіряє роль; оновлення аватара дозволено лише адміністраторам через залежність `get_admin_user`.
