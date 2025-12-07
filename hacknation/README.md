# Work Accident Reporter - PoC

A proof-of-concept application for reporting work accidents via scan, form, or voice assistant.

## Quick Start with Docker

```bash
docker-compose up --build
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Deploy with Public URL (No Account Required!)

Make your app accessible from the internet using Cloudflare Tunnel - **no signup or authentication needed!**

### 1. Set up your environment

```bash
# Copy the example env file (for OpenAI API key)
cp env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Start with public tunnels

```bash
./tunnel-start.sh
```

This script will:
1. Start the backend and create a Cloudflare tunnel
2. Get the backend's public URL (like `https://random-words.trycloudflare.com`)
3. Start the frontend configured with that backend URL
4. Create a tunnel for the frontend

### 3. Access your app

After the script completes, you'll see:
- **Frontend URL**: Your public app URL (share this!)
- **Backend API URL**: The API endpoint URL

Both URLs will look like: `https://some-random-words.trycloudflare.com`

### Check tunnel URLs anytime

```bash
./tunnel-urls.sh
```

### Stop all services

```bash
docker compose down
```

## Project Structure

```
hacknation/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.js        # Main React app with routing
│   │   ├── styles.css    # Global styles
│   │   └── i18n/         # Translation files
│   │       ├── pl.json   # Polish translations
│   │       └── en.json   # English translations
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/skan`  | POST   | Upload scanned document |
| `/form`  | POST   | Submit accident report form |
| `/voice` | GET    | Voice assistant (placeholder) |

## Development

### Backend only
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend only
```bash
cd frontend
npm install
npm start
```

## Roadmap

- [ ] OCR processing for scanned documents
- [ ] Form data validation
- [ ] PDF generation
- [ ] Voice-to-text AI assistant
- [ ] Multi-language support switching

