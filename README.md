# Fondsoversikt for kapitalforvaltere

Et beslutningsstøtteverktøy for rangering og sammenligning av fond.

## Kom i gang lokalt

### Forutsetninger
- Python 3.10+ 
- Node.js 18+

---

### 1. Backend

```bash
pip install -r requirements.txt
cd backend
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

Totalscore er en vektet sum av fire faktorer, alle normalisert til 0–100 med min-max på tvers av fondene i utvalget.

| Faktor          | Vekt | Retning        | Råverdi                  | Datakilde                 |
|-----------------|------|----------------|--------------------------|---------------------------|
| Avkastning      | 35%  | Høyere = bedre | 3-årig ann. (fallback 1-årig) | fund_metrics.csv     |
| Risiko          | 30%  | Lavere = bedre | Volatilitet 1 år         | fund_metrics.csv          |
| Kostnad         | 20%  | Lavere = bedre | Forvaltningsgebyr        | fund_metrics.csv          |
| Diversifisering | 15%  | Lavere = bedre | HHI sektorkonsentrasjon  | fund_sector_exposure.csv  |

Vektene er satt skjønnsmessig, men kan justeres etter brukerens prioriteringer.

### Min-max normalisering

Hver råverdi skaleres til $[0, 100]$ relativt til fondsutvalget:

$$s_i = \frac{x_i - x_{\min}}{x_{\max} - x_{\min}} \times 100$$

For faktorer der lavere er bedre (risiko, kostnad, diversifisering) inverteres scoren: $s_i = 100 - s_i$. Dette sikrer at høyere score alltid er bedre for alle faktorer, og gjør vektene direkte sammenlignbare uavhengig av enhet.

### Manglende data

Manglende verdier imputeres med medianen av faktoren på tvers av alle fond.
Median foretrekkes fremfor gjennomsnitt fordi den er robust mot utliggere. Et fond med manglende verdi får en nøytral score relativt til den faktiske fordelingen.

### HHI — diversifisering

Sektorkonsentrasjon måles med Herfindahl-Hirschman-indeksen:

$$\text{HHI} = \sum_{k=1}^{n} \left(\frac{w_k}{100}\right)^2$$

der $w_k$ er fondets vekt i sektor $k$ i prosent. HHI nærmer seg 0 for et perfekt spredt fond og 1 for et enkeltsektor-fond. Scoren inverteres slik at lavere HHI gir høyere diversifiseringsscore.

## Datafiler brukt

- `funds.csv` – fondsmetadata (navn, kategori osv.)
- `fund_metrics.csv` – nøkkeltall (avkastning, volatilitet, gebyr osv.)
- `fund_sector_exposure.csv` – sektorvekter brukt til HHI-beregning

Følgende filer er ikke brukt, men kan utvide scoren:
- `fund_prices_monthly.csv` – for egne avkastningstall eller momentumfaktor
- `fund_top_holdings.csv` + `company_financials.csv` – kvalitetsscore på underliggende selskaper

## Antakelser og avgrensninger

- Diversifisering mellom ulike sektorer vektes positivt, uten å ta hensyn til korrelasjon mellom de ulike sektorene - gjort som forenkling for å slippe å bruke ekstern data.

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
Push til `main` trigger automatisk build og deploy via `.github/workflows/deploy.yml`.

Forutsetninger:
1. Last ned publish profile fra Azure Portal → App Service → **Download publish profile**
2. Legg til som GitHub Secret: `AZURE_WEBAPP_PUBLISH_PROFILE`

Workflow bygger React-frontenden, og lar Azure Oryx installere Python-avhengigheter fra `requirements.txt` i roten.
