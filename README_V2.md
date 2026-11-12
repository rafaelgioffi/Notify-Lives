# Notify Lives v2

Base inicial da modernização, mantendo [Notify-Lives-1.0.py](./Notify-Lives-1.0.py) intacto.

## Princípios

- APIs oficiais para Facebook, Instagram e TikTok.
- Cloudinary somente para produzir URLs HTTPS temporárias das mídias.
- SQLite no desenvolvimento; PostgreSQL por variável `DATABASE_URL` no Debian.
- WhatsApp Desktop em modo assistido, com confirmação do primeiro envio e retry progressivo.
- Cada canal terá seu próprio adaptador e histórico de tentativas.

## Preparação local

```powershell
Copy-Item .env.example .env
pip install -r requirements-v2.txt
```

O arquivo `.env` não deve ser versionado.

## PostgreSQL no Debian

Defina `POSTGRES_DB`, `POSTGRES_USER` e `POSTGRES_PASSWORD` no ambiente do servidor e execute:

```bash
docker compose -f docker-compose.postgres.yml up -d
```

O banco da aplicação deverá usar uma URL `postgresql+psycopg://...` e o container poderá permanecer isolado dos demais serviços.

