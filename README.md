# SpinTar - Slot Machine с OAuth2 интеграцией

Веб-игра слот-машина с интеграцией авторизации через Orbitar.space. Игроки могут играть как гости (по IP) или авторизоваться через Orbitar для персонального рейтинга.

## Особенности

- 🎰 Классический слот-машина с emoji символами
- 🏆 Система рейтингов с топ-игроков
- 🔐 OAuth2 авторизация через Orbitar.space
- 🌙 Темная/светлая тема
- 🔄 Реалтайм синхронизация через Firebase
- 🎁 Система бонусов
- 📱 Адаптивный дизайн

## Архитектура

- **Frontend**: Vanilla JS + HTML/CSS (статичные файлы)
- **Backend**: Vercel Serverless Functions для OAuth2
- **База данных**: Firebase Firestore для рейтингов
- **Деплой**: GitHub + Vercel
- **Авторизация**: OAuth2 с Orbitar.space

## Настройка проекта

### 1. Регистрация OAuth2 приложения в Orbitar

1. Перейди на [orbitar.space](https://orbitar.space)
2. Авторизуйся в своем аккаунте
3. Зайди в настройки профиля → Developer Settings → OAuth Applications
4. Создай новое приложение со следующими параметрами:
   - **Application Name**: `SpinTar Game`
   - **Homepage URL**: `https://your-app-name.vercel.app`
   - **Authorization callback URL**: `https://your-app-name.vercel.app/api/auth/callback`
   - **Description**: `Slot machine game with OAuth2 integration`

5. Сохрани **Client ID** и **Client Secret** - они понадобятся для настройки Vercel

### 2. Настройка Firebase

1. Перейди в [Firebase Console](https://console.firebase.google.com)
2. Создай новый проект или используй существующий
3. Включи Firestore Database
4. Настрой правила безопасности для публичного доступа на запись/чтение:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

5. Скопируй конфигурацию Firebase и вставь в `index.html` (уже настроено)

### 3. Деплой на Vercel

1. Форкни или склонируй репозиторий
2. Подключи репозиторий к [Vercel](https://vercel.com)
3. В настройках проекта на Vercel добавь Environment Variables:

```
CLIENT_ID=your_orbitar_client_id
CLIENT_SECRET=your_orbitar_client_secret
REDIRECT_URI=https://your-app-name.vercel.app/api/auth/callback
```

4. Задеплой проект - Vercel автоматически создаст production URL

### 4. Обновление URL в Orbitar

После деплоя обнови настройки OAuth2 приложения в Orbitar:
- **Homepage URL**: `https://your-actual-vercel-url.vercel.app`
- **Authorization callback URL**: `https://your-actual-vercel-url.vercel.app/api/auth/callback`

## API Endpoints

### Авторизация
- `GET /api/auth/login` - Инициация OAuth2 авторизации
- `GET /api/auth/callback` - Обработка callback от Orbitar
- `POST /api/auth/refresh` - Обновление access token
- `POST /api/auth/logout` - Выход из системы

### Пользователь
- `GET /api/user/profile` - Получение профиля авторизованного пользователя

## Структура проекта

```
spintar/
├── api/                    # Vercel Functions
│   ├── auth/
│   │   ├── login.js       # OAuth2 авторизация
│   │   ├── callback.js    # Обработка callback
│   │   ├── refresh.js     # Обновление токенов
│   │   └── logout.js      # Выход
│   └── user/
│       └── profile.js     # Профиль пользователя
├── index.html             # Основная игра
├── package.json          # Зависимости и скрипты
├── vercel.json           # Конфигурация Vercel
├── .gitignore           # Git исключения
└── README.md            # Документация
```

## Безопасность

- ✅ Client Secret хранится только в Environment Variables на сервере
- ✅ Access/Refresh токены в HttpOnly cookies
- ✅ State parameter для защиты от CSRF
- ✅ Secure и SameSite настройки для cookies
- ✅ Валидация всех входящих параметров

## Разработка

### Локальная разработка

1. Установи Vercel CLI: `npm i -g vercel`
2. Склонируй репозиторий
3. Создай `.env` файл с переменными окружения:

```env
CLIENT_ID=your_orbitar_client_id
CLIENT_SECRET=your_orbitar_client_secret
REDIRECT_URI=http://localhost:3000/api/auth/callback
```

4. Запусти dev сервер: `vercel dev`
5. Открой `http://localhost:3000`

### Тестирование OAuth2

Для тестирования локально:
1. Создай отдельное OAuth2 приложение в Orbitar с localhost URL
2. Используй `http://localhost:3000/api/auth/callback` как callback URL
3. Обнови `.env` с локальными настройками

## Игровая механика

### Очки и ставки
- Стоимость спина: **100 очков**
- Стартовые очки: **100 очков** (при первом бонусе)
- Бонус: **100 очков** каждые 15-120 секунд (рандомно)

### Выигрышные комбинации
- **2 одинаковых символа**: цена символа × 2
- **3 одинаковых символа**: цена символа × 3
- Проверяются линии: горизонтальные, вертикальные, диагональные

### Символы и цены
- 🎮🎲🎯🎱🎳 (Gaming): **25 очков**
- 🎼🎵🎸🎺🎷🎹🎻 (Music): **50 очков**
- 🎬🎪🎨🎭 (Entertainment): **75 очков**
- 🌟💫⭐🌙☀️🌈 (Nature): **125 очков**
- 🍀🎋🎍 (Luck): **250 очков**
- 🎰 (Jackpot): **500 очков**

## Поддержка

Если возникли проблемы:
1. Проверь логи в Vercel Dashboard
2. Убедись, что все Environment Variables настроены
3. Проверь правильность URL в настройках Orbitar OAuth2
4. Убедись, что Firebase правила позволяют запись/чтение

## Лицензия

MIT License - используй свободно для своих проектов.
