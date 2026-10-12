from fastapi import FastAPI, Response, HTTPException, Request
import httpx
from models import Product
import time
from collections import defaultdict,deque
import logging
from traffic_analyzer import analyze_ml_traffic
app=FastAPI()
BACKEND_URL = "http://127.0.0.1:8000"

RATE_LIMIT=5
TIME_WINDOW=60
request_history=defaultdict(list)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_gateway")

NOT_FOUND_LIMIT = 5
ANALYSIS_WINDOW = 60

recent_404s = defaultdict(deque)
SERVER_ERROR_LIMIT = 3
recent_server_errors = defaultdict(deque)

def analyze_traffic(client_id: str, status_code: int):
    current_time = time.time()

    if status_code != 404:
        return

    recent_404s[client_id].append(current_time)

    while (
        recent_404s[client_id]
        and current_time - recent_404s[client_id][0] >= ANALYSIS_WINDOW
    ):
        recent_404s[client_id].popleft()

    if len(recent_404s[client_id]) == NOT_FOUND_LIMIT:
        logger.warning(
            "Suspicious traffic: client=%s generated %s not-found responses within %s seconds",
            client_id,
            NOT_FOUND_LIMIT,
            ANALYSIS_WINDOW,
        )


def analyze_server_errors(client_id: str, status_code: int):
    current_time = time.time()

    if not 500 <= status_code < 600:
        return

    recent_server_errors[client_id].append(current_time)

    while (
        recent_server_errors[client_id]
        and current_time - recent_server_errors[client_id][0] >= ANALYSIS_WINDOW
    ):
        recent_server_errors[client_id].popleft()

    if len(recent_server_errors[client_id]) == SERVER_ERROR_LIMIT:
        logger.warning(
            "Repeated server errors: client=%s generated %s 5xx responses within %s seconds",
            client_id,
            SERVER_ERROR_LIMIT,
            ANALYSIS_WINDOW,
        )


def is_rate_limited(client_id: str) -> bool:
    current_time = time.time()

    request_history[client_id] = [
        timestamp
        for timestamp in request_history[client_id]
        if current_time - timestamp < TIME_WINDOW
    ]

    if len(request_history[client_id]) >= RATE_LIMIT:
        return True

    request_history[client_id].append(current_time)
    return False




@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = request.client.host if request.client else "unknown"
    start_time = time.perf_counter()

    if is_rate_limited(client_id):
        response = Response(
            content='{"detail":"Rate limit exceeded. Try again later."}',
            status_code=429,
            media_type="application/json",
        )
    else:
        response = await call_next(request)

    duration_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "method=%s path=%s status=%s duration_ms=%.2f client=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        client_id,
    )
    analyze_traffic(client_id, response.status_code)
    analyze_server_errors(client_id, response.status_code)
    if request.url.path not in {"/docs", "/openapi.json", "/redoc"}:
        analyze_ml_traffic(client_id, response.status_code)
    return response



async def forward_request(path: str, request: Request):
    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            backend_response = await client.request(
                method=request.method,
                url=f"{BACKEND_URL}{path}",
                params=request.query_params,
                content=body if body else None,
                headers={
                    key: value
                    for key, value in request.headers.items()
                    if key.lower() not in {"host","content-length","connection","transfer-encoding"}
                },
            )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Backend API timed out",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to backend API",
        )
    return Response(
        content=backend_response.content,
        status_code=backend_response.status_code,
        headers={
            "content-type": backend_response.headers.get(
                "content-type", "application/json"
            )
        },
    )

@app.get("/products")
async def get_products_through_gateway(request: Request):
    return await forward_request("/products", request)

@app.get("/products/search")
async def search_products_through_gateway(
    max_price: float,
    request: Request,
):
    return await forward_request("/products/search", request)


@app.get("/products/{product_id}")
async def get_product_through_gateway(
    product_id: int,
    request: Request,
):
    return await forward_request(
        f"/products/{product_id}",
        request,
    )

@app.post("/products")
async def create_product_through_gateway(
    product: Product,
    request: Request,
):
    return await forward_request("/products", request)


@app.put("/products/{product_id}")
async def update_product_through_gateway(
    product_id: int,
    product: Product,
    request: Request,
):
    return await forward_request(
        f"/products/{product_id}",
        request,
    )


@app.delete("/products/{product_id}")
async def delete_product_through_gateway(
    product_id: int,
    request: Request,
):
    return await forward_request(
        f"/products/{product_id}",
        request,
    )

