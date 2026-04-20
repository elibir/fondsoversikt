# Fondsoversikt for kapitalforvaltere

Et beslutningsstøtteverktøy for rangering og sammenligning av fond. Live på: https://fondsoversikt-app.azurewebsites.net/

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

Totalscore er en vektet sum av fire faktorer, alle normalisert til 0–100 med Percentile rank på tvers av fondene i utvalget.

| Faktor          | Vekt | Retning        | Råverdi                  | Datakilde                 |
|-----------------|------|----------------|--------------------------|---------------------------|
| Avkastning      | 45%  | Høyere = bedre | 3-årig ann. (fallback 1-årig) | fund_metrics.csv     |
| Risiko          | 25%  | Lavere = bedre | Volatilitet 1 år         | fund_metrics.csv          |
| Kostnad         | 10%  | Lavere = bedre | Forvaltningsgebyr        | fund_metrics.csv          |
| Diversifisering | 20%  | Lavere = bedre | HHI sektorkonsentrasjon  | fund_sector_exposure.csv  |

Vektene er satt skjønnsmessig, men kan justeres etter brukerens prioriteringer.

### Percentile rank-normalisering

Scoren til fond $i$ for en gitt faktor beregnes som:

$$s_i = \frac{r_i - 1}{N - 1} \times 100$$

der $r_i$ er rangen til fond $i$ blant de $N$ fondene med tilgjengelig data for faktoren (laveste verdi får rang 1). Ved like verdier brukes gjennomsnittlig rang — fire fond som deler plasseringene 12–15 får alle $r_i = 13.5$, og dermed samme score.

For faktorer der lavere er bedre (risiko, kostnad, diversifisering) inverteres scoren: $s_i = 100 - s_i$. Dette sikrer at høyere score alltid er bedre for alle faktorer, og gjør vektene direkte sammenlignbare uavhengig av enhet.

Percentile rank er robust mot utliggere: et fond med ekstrem verdi forskyver kun sin egen rangering, ikke alle andres score.

**Alternativ: min-max-normalisering** skalerer råverdiene lineært til $[0, 100]$:

$$s_i = \frac{x_i - x_{\min}}{x_{\max} - x_{\min}} \times 100$$

Dette bevarer avstanden mellom fondene i absolutt forstand, men er følsom for utliggere — ett fond med avvikende verdi forskyver $x_{\min}$ eller $x_{\max}$ og komprimerer scoren til alle øvrige fond. Implementasjonen er bevart som kommentar i `scoring.py`.

### Manglende data

Fond med manglende verdi for en faktor ekskluderes fra rangeringen for den faktoren og får `NaN` som delscore — ingen imputering. Totalscore beregnes ved å rebalansere vektene til de tilgjengelige faktorene slik at summen alltid blir 1.

Avkastning og volatilitet er obligatoriske: mangler en av disse settes totalscore til 0.

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
- Rapportert avkastning antas å være netto etter forvaltningsgebyr og inkludere reinvestert direkteavkastning (total return). Kostnadsfaktoren i scoringen er derfor delvis overlappende med avkastningsfaktoren, men inkluderes som et fremoverskuende signal på fondets løpende kostnadsnivå - i tillegg var den nevnt som en eksempelfaktor i kravspesifikasjonen.

---

## Deploy til Azure App Service

### Forutsetninger
- Azure-konto ([gratis prøveperiode](https://azure.microsoft.com/free))
- Azure CLI installert: ([How to install the Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest))

### Steg

```bash
# Logg inn
az login

# Bygg frontend
cd frontend && npm run build && cd ..

# Opprett resource group og App Service
az group create --name fondsoversikt-rg --location norwayeast
az appservice plan create --name fondsoversikt-plan --resource-group fondsoversikt-rg --sku F1 --is-linux
az webapp create --name fondsoversikt-app --resource-group fondsoversikt-rg --plan fondsoversikt-plan --runtime "PYTHON:3.12"

# Sett startup-kommando
az webapp config set --resource-group fondsoversikt-rg --name fondsoversikt-app \
  --startup-file "python -m uvicorn main:app --host 0.0.0.0 --port 8000"

# Deploy
az webapp up --name fondsoversikt-app --resource-group fondsoversikt-rg
```

### GitHub Actions (CI/CD)
Push til `main` trigger automatisk build og deploy via `.github/workflows/deploy.yml`.

Forutsetninger:
1. Last ned publish profile fra Azure Portal → App Service → **Download publish profile**
2. Legg til som GitHub Secret: `AZURE_WEBAPP_PUBLISH_PROFILE`

Workflow bygger React-frontenden, og lar Azure Oryx installere Python-avhengigheter fra `requirements.txt` i roten.
