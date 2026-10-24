# Taxi Dispatch Mini — Такси тапсырыс жүйесі (Нұсқа 25)

Университет студенттеріне арналған Flask веб-қосымшасы.  
Клиенттер такси тапсырыс береді, админ жүргізуші тағайындайды, статустар бақыланады.

## Технологиялар

- Python 3.x
- Flask 3 + Flask-SQLAlchemy + Flask-Login + Flask-WTF
- Jinja2 шаблондар
- SQLite (оңай PostgreSQL-ге ауыстыруға болады)
- Bootstrap 5 (UI)

## Функционал

| Талап | Орындалуы |
|-------|-----------|
| Тіркелу / кіру / шығу | ✅ Flask-Login + session |
| 2 рөл (admin / user) | ✅ Role-based access |
| 3+ модель + relationship | ✅ User, Customer, Driver, Ride |
| CRUD толық | ✅ Тапсырыстар, жүргізушілер, клиенттер |
| Іздеу + сүзгі + сорттау | ✅ Тапсырыстар бетінде (статус, күн, мәтін) |
| Пагинация | ✅ Барлық тізім беттерінде |
| Форма валидациясы | ✅ WTForms (email, телефон, ұзындық, диапазон) |
| Файл жүктеу | ✅ Жүргізуші фотосы (қауіпсіз атау + кеңейтім тексеру) |
| Custom 404 / 500 | ✅ |
| API (3+ endpoint) | ✅ `/api/rides`, `/api/drivers`, `/api/customers` |
| README + скриншоттар | ✅ |

### Ерекшеліктер (Нұсқа 25)

- Ride статустары: `requested` → `assigned` → `in_progress` → `done` / `cancelled`
- Күні мен статус бойынша сүзгі
- Жүргізуші бос/бос емес статусы автоматты жаңартылады

## Құрылым

```
taxi_dispatch/
├── app/
│   ├── blueprints/      # auth, main, rides, drivers, customers, api
│   ├── templates/       # Jinja2
│   ├── static/
│   │   ├── css/
│   │   └── uploads/     # жүктелген фотолар
│   ├── models.py
│   ├── forms.py
│   ├── utils.py
│   ├── errors.py
│   └── __init__.py
├── config.py
├── run.py
├── init_db.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Орнату және іске қосу

### 1. Клондау / көшіру

```bash
cd taxi_dispatch
```

### 2. Виртуалды орта

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate
```

### 3. Тәуелділіктер

```bash
pip install -r requirements.txt
```

### 4. Дерекқорды инициализациялау (демо деректермен)

```bash
python init_db.py
```

`init_db.py` creates missing tables and adds demo records only when they are absent. It does not drop or overwrite an existing database. To start with a clean demo database, stop the app and remove `taxi_dispatch.db` yourself before running the command.

### 5. Іске қосу

```bash
python run.py
```

Браузерде: **http://127.0.0.1:5000**. Debug mode өшірулі; әзірлеу кезінде қосу үшін `FLASK_DEBUG=1` орнатыңыз.

## VS Code арқылы іске қосу

1. **Folder-ді ашыңыз:** `File → Open Folder…` → `taxi_dispatch` қалтасын таңдаңыз.
2. VS Code ұсынылған кеңейтімдерді орнатуды сұрайды (Python, Pylance, Jinja) — **Install** басыңыз.
3. Терминалда (`` Ctrl+` ``):
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python init_db.py
   ```
4. **Іске қосу / Debug:**
   - `F5` немесе `Run and Debug` панелі
   - **Python: run.py** немесе **Flask: Taxi Dispatch** конфигурациясын таңдаңыз
5. Немесе **Tasks:** `Ctrl+Shift+P` → `Tasks: Run Task` → `Run Flask server`

`.vscode/` ішінде дайын:
- `launch.json` — debug конфигурациялары
- `tasks.json` — venv, init_db, run тапсырмалары
- `settings.json` — Python interpreter + Jinja
- `extensions.json` — ұсынылған кеңейтімдер

## Netlify-ге жариялау

Flask серверін Netlify Functions ішінде тікелей іске қосу мүмкін емес: Netlify Functions JavaScript/TypeScript және Go кодын іске қосады. Бұл конфигурация Flask серверін Render-де, ал браузерге көрінетін доменді Netlify-де орналастырып, барлық сұрауды Netlify проксиі арқылы өткізеді.

1. Репозиторийді GitHub-қа жүктеңіз.
2. Render-де **New → Blueprint** арқылы осы репозиторийді қосыңыз. `render.yaml` Flask сервері мен PostgreSQL базасын жасайды.
3. Render сервисі іске қосылған соң оның URL-ін тексеріңіз. Ол `https://taxi-dispatch-flask.onrender.com` болмаса, `netlify.toml` ішіндегі прокси URL-ін Render берген адреске ауыстырыңыз.
4. Netlify-де **Add new site → Import an existing project** арқылы сол GitHub репозиторийін таңдаңыз. Build command бос, publish directory — `app/static`.
5. Жарияланған сайттың `https://<сайт-аты>.netlify.app` адресін ашыңыз.

Тегін Render сервисі біраз уақыт қолданылмаса ұйқыға кетуі мүмкін, сондықтан алғашқы сұрау баяу жауап беруі ықтимал. Render-дің тегін PostgreSQL дерекқоры 30 күннен кейін аяқталады. Тегін сервистің файл жүйесі тұрақты сақтау орны емес: жүктелген жүргізуші фотолары қайта жариялаудан кейін сақталмауы мүмкін. Ұзақ уақыт жұмыс істейтін нұсқаға тұрақты дерекқор және файл сақтау орны қосыңыз.

## Тест аккаунттар

| Рөл   | Username | Password  |
|-------|----------|-----------|
| Admin | `admin`  | `admin123` |
| User  | `user1`  | `user123`  |

- **Admin** — барлық CRUD, жүргізуші тағайындау, клиенттерді басқару
- **User** — өз тапсырыстарын көру / жаңа тапсырыс беру

## API endpoint-тер

Барлық API үшін алдымен браузерде кіру керек (session cookie) немесе Postman-да cookie жіберу.

| Метод | URL | Сипаттама |
|-------|-----|-----------|
| GET | `/api/rides` | Тапсырыстар тізімі (`?status=requested&page=1`) |
| POST | `/api/rides` | Жаңа тапсырыс (`pickup_address`, `dropoff_address`) |
| GET | `/api/rides/<id>` | Бір тапсырыс |
| PUT/PATCH | `/api/rides/<id>` | Статус / жүргізуші жаңарту (admin) |
| DELETE | `/api/rides/<id>` | Жою (admin) |
| GET | `/api/drivers` | Жүргізушілер (`?status=available`) |
| GET | `/api/drivers/<id>` | Бір жүргізуші |
| GET | `/api/customers` | Клиенттер (admin only) |

### Мысал (curl, cookie қажет)

```bash
# Кіруден кейін cookie алыңыз, содан кейін:
curl -b cookies.txt http://127.0.0.1:5000/api/rides
curl -b cookies.txt -X POST http://127.0.0.1:5000/api/rides \
  -H "Content-Type: application/json" \
  -d '{"pickup_address":"Абай 1","dropoff_address":"Достық 2"}'
```

## Демо сценарий

1. `admin` / `admin123` арқылы кіріңіз → Админ панелі
2. **Жүргізушілер** → жаңа жүргізуші қосыңыз (фото жүктеңіз)
3. **Тапсырыстар** → күтудегі тапсырысқа жүргізуші тағайындаңыз (өңдеу)
4. Шығып, `user1` / `user123` арқылы кіріңіз → жаңа тапсырыс беріңіз
5. Қайта admin болып, сүзгілерді (статус, күн) қолданып көріңіз
6. API: `/api/rides?status=requested`

## Скриншоттар

Скриншоттарды `screenshots/` қалтасына салыңыз (6–10 дана):

1. Басты бет
2. Кіру / тіркелу
3. Тапсырыстар тізімі (сүзгі + пагинация)
4. Жаңа тапсырыс формасы
5. Тапсырыс деталі
6. Жүргізушілер тізімі / форма (фото)
7. Админ панелі
8. API жауабы (Postman немесе браузер)

## PostgreSQL-ге ауыстыру (қаласаңыз)

`.env` ішінде:

```
DATABASE_URL=postgresql://user:password@localhost:5432/taxi_dispatch
```

және `psycopg2-binary` орнатыңыз.

## Автор

Нұсқа 25 — Taxi Dispatch Mini  
Студенттік өзіндік жұмыс
