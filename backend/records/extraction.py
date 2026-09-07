import re
import shutil
from datetime import date
from io import BytesIO

from pypdf import PdfReader


MEDICINE_SIGNALS = {
    "tab", "tablet", "cap", "capsule", "syrup", "inj", "injection", "drops",
    "cream", "ointment", "mg", "ml", "mcg", "od", "bd", "tds", "sos"
}


def extract_text(uploaded_file, content_type):
    if content_type == "application/pdf" or uploaded_file.name.lower().endswith(".pdf"):
        text, status = extract_pdf_text(uploaded_file)
        return text, status
    if content_type.startswith("image/"):
        text = extract_image_text(uploaded_file)
        return text, "Image OCR extracted text" if text else "Image OCR found no text"
    return "", "Unsupported file type for text extraction"


def extract_pdf_text(uploaded_file):
    uploaded_file.seek(0)
    reader = PdfReader(uploaded_file)
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(page.strip() for page in pages if page.strip())
    if text:
        return text, "PDF text extracted"

    ocr_text = extract_scanned_pdf_text(uploaded_file)
    if ocr_text:
        return ocr_text, "Scanned PDF OCR extracted text"
    return "", "PDF had no selectable text and OCR found no text"


def extract_scanned_pdf_text(uploaded_file):
    if not shutil.which("tesseract"):
        return ""

    try:
        import fitz
        from PIL import Image
        import pytesseract
    except ImportError:
        return ""

    uploaded_file.seek(0)
    pdf_bytes = uploaded_file.read()
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_text = []

    for page in document:
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.open(BytesIO(pixmap.tobytes("png")))
        text = pytesseract.image_to_string(image).strip()
        if text:
            page_text.append(text)

    return "\n".join(page_text)


def extract_image_text(uploaded_file):
    if not shutil.which("tesseract"):
        return ""

    from PIL import Image
    import pytesseract

    uploaded_file.seek(0)
    image = Image.open(uploaded_file)
    return pytesseract.image_to_string(image)


def parse_medicines(text):
    block_medicines = parse_numbered_prescription_blocks(text)
    if block_medicines:
        return block_medicines

    rows = [line.strip() for line in re.split(r"[\n;,]+", text or "") if line.strip()]
    medicines = []

    for row in rows:
        lower = row.lower()
        if not any(signal in lower for signal in MEDICINE_SIGNALS) and not re.search(r"\b\d+(\.\d+)?\s?(mg|ml|mcg)\b", lower):
            continue

        medicines.append({
            "name": clean_name(row),
            "raw_line": row,
            "dosage": first_match(row, r"\b\d+(\.\d+)?\s?(mg|ml|mcg)\b"),
            "quantity": extract_quantity(row),
            "frequency": first_match(row, r"\b(od|bd|tds|qid|sos|daily|twice daily|once daily)\b"),
            "duration": first_match(row, r"\b(for\s+)?\d+\s+(day|days|week|weeks|month|months)\b"),
        })

    seen = set()
    unique = []
    for medicine in medicines:
        key = medicine["raw_line"].lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(medicine)

    return unique[:40]


def extract_prescription_date(text):
    match = re.search(r"\bDate:\s*(?:\n\s*)?(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", text or "", flags=re.IGNORECASE)
    if not match:
        return None

    day, month, year = (int(part) for part in match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_numbered_prescription_blocks(text):
    normalized = normalize_prescription_text(text)
    matches = list(re.finditer(r"(?m)^\s*(\d+)\.\s*$", normalized))
    if not matches:
        return []

    medicines = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        medicine = parse_prescription_block(normalized[start:end])
        if medicine:
            medicines.append(medicine)

    return medicines[:80]


def normalize_prescription_text(text):
    cleaned = (text or "").replace("\t", " ")
    cleaned = re.sub(r"[ ]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def parse_prescription_block(block):
    block = truncate_non_medicine_sections(block)
    lines = [line.strip(" \t,-") for line in block.splitlines() if line.strip(" \t,-")]
    if not lines:
        return None

    name = lines[0]
    detail_lines = lines[1:]
    if not looks_like_medicine_name(name):
        return None

    duration = first_match(" ".join(detail_lines), duration_pattern())
    schedule = extract_schedule(detail_lines)
    raw_line = " ".join(part for part in [name, schedule, duration] if part).strip()

    return {
        "name": name[:260],
        "raw_line": raw_line,
        "dosage": schedule,
        "quantity": extract_quantity(schedule or raw_line),
        "frequency": extract_frequency(schedule),
        "duration": duration,
    }


def truncate_non_medicine_sections(block):
    stop_match = re.search(
        r"(?im)^\s*(Dietary Advice|Instructions|Vaccine Given|Next Vaccination|Dr\.)\b",
        block,
    )
    return block[:stop_match.start()] if stop_match else block


def looks_like_medicine_name(name):
    lower = name.lower()
    if any(signal in lower for signal in MEDICINE_SIGNALS):
        return True
    if re.search(r"\b\d+(\.\d+)?\s?(mg|ml|mcg)\b", lower):
        return True
    return name.isupper() and len(name) > 2


def extract_schedule(lines):
    schedule_parts = []
    for line in lines:
        if is_duration_line(line) or is_note_line(line):
            continue
        if "-" in line or any(signal in line.lower() for signal in ["morning", "afternoon", "evening", "night", "required"]):
            schedule_parts.append(line)

    return ", ".join(schedule_parts)


def is_duration_line(line):
    return bool(re.fullmatch(rf"-|{duration_pattern()}|As needed", line, flags=re.IGNORECASE))


def is_note_line(line):
    lower = line.lower()
    note_starts = (
        "after food", "with food", "at bed time", "if temp", "cut open", "mix with",
        "repeat after", "nausea", "fever", "for gases", "for colic", "after a loose",
        "insert locally", "gum massage"
    )
    return lower.startswith(note_starts)


def first_match(text, pattern):
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(0) if match else ""


def duration_pattern():
    return r"\b\d+\s*(Day\(s\)|days|day|Week\(s\)|weeks|week|Month\(s\)|months|month)(?=\s|$|[,.])"


def extract_quantity(row):
    explicit = first_match(row, r"\b(qty|quantity|dispense|no\.?)\s*[:\-]?\s*\d+\b")
    if explicit:
        return explicit

    schedule_amount = first_match(row, r"\b\d+(\.\d+)?\s*(ml)?\s*-\s*(syrup|suspension|drop|drops|capsule|tablet|spray|sachet|liquid|fingertip)\b")
    if schedule_amount:
        return schedule_amount.split("-")[0].strip()

    units = first_match(row, r"\b\d+\s*(tab|tabs|tablet|tablets|cap|caps|capsule|capsules|ml|bottle|bottles|strip|strips)\b")
    if units:
        return units

    inferred = infer_quantity(row)
    return inferred


def extract_frequency(row):
    matches = re.findall(r"\b(Morning|Afternoon|Evening|Night|If Required|Required|OD|BD|TDS|QID|SOS|daily|twice daily|once daily)\b", row or "", flags=re.IGNORECASE)
    if not matches:
        return ""

    normalized = []
    for match in matches:
        label = match.title()
        if label == "Required":
            label = "If Required"
        if label not in normalized:
            normalized.append(label)
    return ", ".join(normalized)


def infer_quantity(row):
    lower = row.lower()
    duration_match = re.search(r"\b(?:for\s+)?(\d+)\s+(day|days|week|weeks)\b", lower)
    if not duration_match:
        return ""

    count = int(duration_match.group(1))
    unit = duration_match.group(2)
    days = count * 7 if unit.startswith("week") else count
    doses_per_day = {
        "od": 1,
        "once daily": 1,
        "daily": 1,
        "bd": 2,
        "twice daily": 2,
        "tds": 3,
        "qid": 4,
    }

    for token, multiplier in doses_per_day.items():
        if token in lower:
            return f"{days * multiplier} doses estimated"
    return ""


def clean_name(row):
    cleaned = re.sub(r"^(tab|tablet|cap|capsule|syrup|inj|injection|drops|cream|ointment)\.?\s+", "", row, flags=re.IGNORECASE)
    cleaned = re.split(r"\s+-|\s+\d+(\.\d+)?\s?(mg|ml|mcg)\b", cleaned, maxsplit=1, flags=re.IGNORECASE)[0]
    return cleaned.strip(" :-") or row[:260]
