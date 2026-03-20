# OCR-alapú Felhőalkalmazás

Ez a projekt a **Felhők hálózati szolgáltatásai laboratórium** keretében készült házi feladat. A cél egy olyan mikroszolgáltatás-alapú felhőalkalmazás létrehozása, amely képes képek feltöltésére, tárolására és rajtuk automatikus karakterfelismerés (OCR) futtatására.

## Architektúra (Cloud-Native megközelítés)

A rendszer monorepo struktúrában épül fel, szétválasztott felelősségi körökkel

- **Frontend (Next.js):** Felhasználói felület a képfeltöltéshez és az eredmények megjelenítéséhez.
- **Backend (FastAPI):** Központi API Gateway, amely kezeli a metaadatokat és koordinálja a fájlműveleteket.
- **Adattárolás**: 
  - **PostgreSQL:** Relációs adatbázis a képleírások és OCR eredmények tárolására.
  - **MinIO:** S3-kompatibilis objektumtároló a nyers képfájloknak.
- **OCR Worker (Fejlesztés alatt):** Aszinkron feldolgozó egység a karakterfelismeréshez.

## Gyorsindítás (Fejlesztői környezet)

A projekt lokális futtatásához szükség van a Docker és a Docker Compose telepítésére.

1. Inditás
   
`docker compose -f infra/compose.yaml up --build -d`

2. Elérhetőség

   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - MinIO Console: http://localhost:9001
