# Work Accident Reporter - PoC

A proof-of-concept application for reporting work accidents via scan, form, or voice assistant.

## Quick Start with Docker

```bash
docker-compose up --build
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

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

