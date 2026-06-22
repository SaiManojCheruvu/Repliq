"""
tests/test_kb_pipeline.py
──────────────────────────
Integration-style unit tests for the full
  parse_file  →  store_chunks  →  query_chunks
pipeline, using an in-memory ChromaDB client so no disk state is written.
"""

import io
import csv
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def make_upload_file(content: bytes, filename: str, content_type: str):
    mock = MagicMock()
    mock.filename = filename
    mock.content_type = content_type
    mock.read = AsyncMock(return_value=content)
    return mock


def make_csv_bytes(rows: list[dict]) -> bytes:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")

@pytest.fixture(autouse=True)
def in_memory_chroma(monkeypatch):
    """
    Replace the persistent ChromaDB client with an ephemeral in-memory
    client so tests are isolated and leave no files on disk.
    """
    import chromadb
    mem_client = chromadb.EphemeralClient()

    # Patch the module-level singleton in vector_store
    import services.vector_store as vs
    monkeypatch.setattr(vs, "_client", mem_client)
    yield
    # Cleanup: drop all collections created during the test
    for col in mem_client.list_collections():
        mem_client.delete_collection(col.name)


def test_store_chunks_returns_chunk_count():
    from services.vector_store import store_chunks

    text = "This is a short KB entry about our product." * 3
    count = store_chunks("biz1", text, "manual.txt", "text")
    assert count >= 1


def test_store_chunks_empty_text_returns_zero():
    from services.vector_store import store_chunks

    count = store_chunks("biz1", "   ", "empty.txt", "text")
    assert count == 0


def test_store_chunks_creates_isolated_collection_per_business():
    from services.vector_store import store_chunks, list_chunks

    store_chunks("bizA", "FoodHub menu: pizza $14.99", "menu.txt", "text")
    store_chunks("bizB", "TechStore laptop specs: RAM 16GB", "specs.txt", "text")

    entries_a = list_chunks("bizA")
    entries_b = list_chunks("bizB")

    source_names_a = {e["source_name"] for e in entries_a}
    source_names_b = {e["source_name"] for e in entries_b}

    assert "menu.txt" in source_names_a
    assert "menu.txt" not in source_names_b
    assert "specs.txt" in source_names_b
    assert "specs.txt" not in source_names_a

def test_query_chunks_returns_relevant_results():
    from services.vector_store import store_chunks, query_chunks

    store_chunks(
        "foodhub",
        "Margherita Pizza: tomato sauce, mozzarella, basil. Price: $12.99.",
        "menu.txt",
        "text",
    )

    results = query_chunks("foodhub", "What is in the Margherita pizza?")
    assert len(results) >= 1
    assert any("Margherita" in r or "pizza" in r.lower() for r in results)


def test_query_chunks_empty_collection_returns_empty_list():
    from services.vector_store import query_chunks

    results = query_chunks("nonexistent_biz", "anything")
    assert results == []


def test_query_chunks_respects_n_results():
    from services.vector_store import store_chunks, query_chunks

    # Store enough text to produce multiple chunks
    long_text = " ".join([f"Product {i}: price ${i * 10}." for i in range(50)])
    store_chunks("techstore", long_text, "catalog.txt", "text")

    results = query_chunks("techstore", "product price", n_results=3)
    assert len(results) <= 3


def test_list_chunks_empty_returns_empty():
    from services.vector_store import list_chunks

    assert list_chunks("empty_biz") == []


def test_list_chunks_aggregates_sources():
    from services.vector_store import store_chunks, list_chunks

    store_chunks("biz1", "text about menu items" * 10, "menu.pdf", "pdf")
    store_chunks("biz1", "csv row data: product, price" * 10, "products.csv", "csv")

    entries = list_chunks("biz1")
    source_names = {e["source_name"] for e in entries}

    assert "menu.pdf" in source_names
    assert "products.csv" in source_names
    assert len(entries) == 2


def test_delete_chunks_removes_all_data():
    from services.vector_store import store_chunks, delete_chunks, query_chunks

    store_chunks("biz_del", "important product info here", "info.txt", "text")
    assert query_chunks("biz_del", "product info") != []

    deleted = delete_chunks("biz_del")
    assert deleted is True
    assert query_chunks("biz_del", "product info") == []


def test_delete_chunks_nonexistent_returns_false():
    from services.vector_store import delete_chunks

    result = delete_chunks("ghost_business")
    assert result is False



@pytest.mark.anyio
async def test_full_pipeline_csv_to_query():
    """
    End-to-end: CSV file → parse_file → store_chunks → query_chunks.
    Mirrors KB-05, KB-06, KB-07, KB-08 from the business requirements.
    """
    from services.parser import parse_file
    from services.vector_store import store_chunks, query_chunks

    csv_bytes = make_csv_bytes([
        {"product": "iPhone 15 Pro", "price": "999", "warranty": "1 year"},
        {"product": "MacBook Pro M3", "price": "1999", "warranty": "1 year"},
    ])
    file = make_upload_file(csv_bytes, "products.csv", "text/csv")

    extracted_text = await parse_file(file)
    store_chunks("techstore", extracted_text, "products.csv", "csv")

    results = query_chunks("techstore", "iPhone price")
    assert len(results) >= 1
    assert any("iPhone" in r for r in results)


@pytest.mark.anyio
async def test_full_pipeline_pdf_to_query():
    """
    End-to-end: PDF file → parse_file → store_chunks → query_chunks.
    Mirrors KB-04, KB-06, KB-07, KB-08.
    """
    from services.parser import parse_file
    from services.vector_store import store_chunks, query_chunks

    mock_page = MagicMock()
    mock_page.extract_text.return_value = (
        "Cement Mix Type B — $45 per 50kg bag. "
        "Ideal for load-bearing structures and foundations."
    )
    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page]

    with patch("services.parser.pdfplumber.open", return_value=mock_pdf):
        file = make_upload_file(b"%PDF fake", "catalog.pdf", "application/pdf")
        extracted_text = await parse_file(file)

    store_chunks("rawmat", extracted_text, "catalog.pdf", "pdf")

    results = query_chunks("rawmat", "cement bag price")
    assert len(results) >= 1
    assert any("Cement" in r or "cement" in r for r in results)


@pytest.mark.anyio
async def test_business_isolation_in_full_pipeline():
    """
    Uploading KB for business A must not pollute business B's query results.
    Mirrors NFR-02 (session/context isolation between businesses).
    """
    from services.parser import parse_file
    from services.vector_store import store_chunks, query_chunks

    # Business A: food store
    food_csv = make_csv_bytes([{"item": "BBQ Pizza", "price": "14.99"}])
    food_file = make_upload_file(food_csv, "menu.csv", "text/csv")
    food_text = await parse_file(food_file)
    store_chunks("foodhub", food_text, "menu.csv", "csv")

    # Business B: tech store
    tech_csv = make_csv_bytes([{"product": "MacBook Pro", "price": "1999"}])
    tech_file = make_upload_file(tech_csv, "products.csv", "text/csv")
    tech_text = await parse_file(tech_file)
    store_chunks("techstore", tech_text, "products.csv", "csv")

    food_results = query_chunks("foodhub", "pizza price")
    tech_results = query_chunks("techstore", "pizza price")

    # FoodHub should surface pizza; TechStore should not
    assert any("Pizza" in r or "pizza" in r for r in food_results)
    assert not any("Pizza" in r or "pizza" in r for r in tech_results)