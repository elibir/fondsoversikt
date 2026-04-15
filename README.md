# Fondsoversikt for kapitalforvaltere

Et beslutningsstøtteverktøy for rangering og sammenligning av fond.

## Kom i gang lokalt

### Forutsetninger
- Python 3.10+ 
- Node.js 18+

---

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

API kjører på: http://localhost:8000  
Swagger-docs: http://localhost:8000/docs

---

### 2. Frontend (i en ny terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend kjører på: http://localhost:5173  
Vite proxyer `/api`-kall til backenden automatisk.

---

## Rangeringsalgoritme

Scoren beregnes fra tre faktorer, alle normalisert til 0–100:

| Faktor         | Vekt | Retning          | Datakilde          |
|----------------|------|------------------|--------------------|
| Avkastning     | 40%  | Høyere = bedre   | fund_metrics.csv   |
| Volatilitet    | 35%  | Lavere = bedre   | fund_metrics.csv   |
| Forvaltningsgeb.| 25% | Lavere = bedre   | fund_metrics.csv   |

**Normalisering:** Min-max til 0–100 på tvers av alle fond i utvalget.  
**Manglende data:** Faktoren settes til 50 (nøytralt) dersom verdien mangler.  
**Avkastning:** 3-årig avkastning brukes som primærverdi; 1-årig eller 5-årig brukes som fallback.

## Datafiler brukt

- `funds.csv` – fondsmetadata (navn, kategori, kostnader osv.)
- `fund_metrics.csv` – nøkkeltall (avkastning, volatilitet osv.)

Følgende filer er ikke inkludert i MVP-en, men kan utvide scoren:
- `fund_prices_monthly.csv` – for beregning av egne avkastningstall
- `fund_sector_exposure.csv` – diversifiseringsscore
- `fund_top_holdings.csv` + `company_financials.csv` – kvalitetsscore

## Antakelser og avgrensninger

- Alle avkastningstall er historiske og justert for valuta i kildedataene
- AUM og antall beholdninger inngår ikke i scoren, men vises informativt
- Fondene rangeres relativt mot hverandre (ikke mot en absolutt benchmark)

---

## Deploy til Azure App Service

### Forutsetninger
- Azure-konto ([gratis prøveperiode](https://azure.microsoft.com/free))
- Azure CLI installert: `brew install azure-cli`

### Steg

```bash
# Logg inn
az login

# Bygg frontend
cd frontend && npm run build && cd ..

# Opprett resource group og App Service
az group create --name fondsoversikt-rg --location norwayeast
az appservice plan create --name fondsoversikt-plan --resource-group fondsoversikt-rg --sku F1 --is-linux
az webapp create --name fondsoversikt-app --resource-group fondsoversikt-rg --plan fondsoversikt-plan --runtime "PYTHON:3.13"

# Sett startup-kommando
az webapp config set --resource-group fondsoversikt-rg --name fondsoversikt-app \
  --startup-file "uvicorn main:app --host 0.0.0.0 --port 8000"

# Deploy
az webapp up --name fondsoversikt-app --resource-group fondsoversikt-rg
```

### GitHub Actions (CI/CD)
Last ned publish profile fra Azure Portal → App Service → "Get publish profile".  
Legg til som GitHub Secret: `AZURE_WEBAPP_PUBLISH_PROFILE`.  
En workflow-fil ligger i `.github/workflows/deploy.yml`.
