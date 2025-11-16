## Introduction

API that grabs Bryant Park Bring Your Own Skates free ice skating sessions along with the number of slots per time window.

## Deployment Configuration

User sets up a Siri Shortcut which invokes this API. See API.md for usage.

The most common usage would be making a GET request to `https://bp-skate.vercel.app/availability/text` for today's date as default. Another usage could be `https://bp-skate.vercel.app/availability/text?date=2025-12-01`; the user provides the desired date. Slots are released 5 days out, please take that into consideration when using the API.

## Dev

```
python -m venv venv
```

```
source venv/bin/activate
```

```
pip install -r requirements.txt
```

```
pip install uvicorn
```

```
cd api
```

```
fastapi dev index.py
```

At this point, the server should be available on 0.0.0.0:8000 and hot reload on changes.
