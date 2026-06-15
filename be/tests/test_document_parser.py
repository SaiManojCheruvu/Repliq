import io
import csv
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


def make_upload_file(content: bytes, filename: str, content_type: str):
    mock_file = MagicMock()
    mock_file.filename = filename
    mock_file.content_type = content_type
    mock_file.read = AsyncMock(return_value=content)
    return mock_file



@pytest.mark.anyio
async def test_parse_pdf_success():
    from services.parser import parse_file

    mock_page = MagicMock()
    mock_page.extract_text.return_value = "This is page one content."

    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page]

    with patch("services.parser.pdfplumber.open", return_value=mock_pdf):
        file = make_upload_file(b"%PDF fake", "test.pdf", "application/pdf")
        result = await parse_file(file)

    assert "[Page 1]" in result
    assert "This is page one content." in result


@pytest.mark.anyio
async def test_parse_pdf_empty_raises():
    from services.parser import parse_file

    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""

    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page]

    with patch("services.parser.pdfplumber.open", return_value=mock_pdf):
        file = make_upload_file(b"%PDF fake", "empty.pdf", "application/pdf")
        with pytest.raises(ValueError, match="No text could be extracted"):
            await parse_file(file)


@pytest.mark.anyio
async def test_parse_pdf_multiple_pages():
    from services.parser import parse_file

    pages = []
    for i in range(3):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = f"Content of page {i + 1}"
        pages.append(mock_page)

    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = pages

    with patch("services.parser.pdfplumber.open", return_value=mock_pdf):
        file = make_upload_file(b"%PDF fake", "multi.pdf", "application/pdf")
        result = await parse_file(file)

    assert "[Page 1]" in result
    assert "[Page 2]" in result
    assert "[Page 3]" in result



def make_csv_bytes(rows: list[dict]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


@pytest.mark.anyio
async def test_parse_csv_success():
    from services.parser import parse_file

    csv_bytes = make_csv_bytes([
        {"name": "iPhone 15", "price": "999", "category": "Electronics"},
        {"name": "MacBook Pro", "price": "1999", "category": "Computers"},
    ])
    file = make_upload_file(csv_bytes, "products.csv", "text/csv")
    result = await parse_file(file)

    assert "[Row 1]" in result
    assert "iPhone 15" in result
    assert "[Row 2]" in result
    assert "MacBook Pro" in result


@pytest.mark.anyio
async def test_parse_csv_key_value_format():
    from services.parser import parse_file

    csv_bytes = make_csv_bytes([{"product": "Widget", "price": "10"}])
    file = make_upload_file(csv_bytes, "test.csv", "text/csv")
    result = await parse_file(file)

    assert "product: Widget" in result
    assert "price: 10" in result


@pytest.mark.anyio
async def test_parse_csv_empty_raises():
    from services.parser import parse_file

    file = make_upload_file(b"name,price\n", "empty.csv", "text/csv")
    with pytest.raises(ValueError, match="CSV file is empty"):
        await parse_file(file)


@pytest.mark.anyio
async def test_parse_csv_skips_empty_values():
    from services.parser import parse_file

    csv_bytes = make_csv_bytes([{"name": "Widget", "price": "", "category": "Tools"}])
    file = make_upload_file(csv_bytes, "test.csv", "text/csv")
    result = await parse_file(file)

    assert "name: Widget" in result
    assert "category: Tools" in result
    assert "price:" not in result


@pytest.mark.anyio
async def test_parse_xlsx_success():
    from services.parser import parse_file
    import pandas as pd

    df = pd.DataFrame([
        {"product": "Widget", "price": 10},
        {"product": "Gadget", "price": 20},
    ])

    with patch("services.parser.pd.read_excel", return_value=df):
        file = make_upload_file(b"fake xlsx", "products.xlsx",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        result = await parse_file(file)

    assert "[Row 1]" in result
    assert "Widget" in result
    assert "[Row 2]" in result
    assert "Gadget" in result



@pytest.mark.anyio
async def test_unsupported_file_type_raises():
    from services.parser import parse_file

    file = make_upload_file(b"some content", "doc.docx", "application/msword")
    with pytest.raises(ValueError, match="Unsupported file type"):
        await parse_file(file)


@pytest.mark.anyio
async def test_unsupported_image_raises():
    from services.parser import parse_file

    file = make_upload_file(b"\x89PNG", "image.png", "image/png")
    with pytest.raises(ValueError, match="Unsupported file type"):
        await parse_file(file)