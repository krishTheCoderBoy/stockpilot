# StockPilot API Gateway

Run from this directory with `uvicorn app.main:app --host 0.0.0.0 --port 8000`. Configure the upstream service URLs with `.env` or environment variables. The gateway forwards paths and authorization headers; services continue to verify JWTs themselves.

The browser may opt into the gateway by setting `VITE_API_GATEWAY_BASE_URL=http://localhost:8000`. The frontend retains separate auth, inventory, and procurement Axios clients so each call keeps its domain-specific path while sharing the gateway origin. When the variable is unset, each client uses its individual service base URL.
