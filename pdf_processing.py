# pdf_processing.py
import os
import pandas as pd
from pypdf import PdfReader, PdfWriter
from google.api_core.client_options import ClientOptions
from google.cloud import documentai
from rapidfuzz import fuzz

def split_pdf(file_path, pages_per_chunk=15):
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)
    output_files = []
    for start in range(0, total_pages, pages_per_chunk):
        writer = PdfWriter()
        for i in range(start, min(start + pages_per_chunk, total_pages)):
            writer.add_page(reader.pages[i])
        output_path = f"{file_path}_part_{start//pages_per_chunk + 1}.pdf"
        with open(output_path, "wb") as f:
            writer.write(f)
        output_files.append(output_path)
    return output_files

def extract_fields_from_pdf(project_id, location, processor_id, file_path, processor_version_id=None):
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)

    if processor_version_id:
        name = client.processor_version_path(project_id, location, processor_id, processor_version_id)
    else:
        name = client.processor_path(project_id, location, processor_id)

    with open(file_path, "rb") as f:
        content = f.read()
    raw_doc = documentai.RawDocument(content=content, mime_type="application/pdf")
    request = documentai.ProcessRequest(name=name, raw_document=raw_doc)

    try:
        result = client.process_document(request=request)
        document = result.document
    except Exception as e:
        return {"error": str(e)}

    key_map = {
        "name": "name",
        "client name": "name",
        "patient name": "name",
        "doa": "doa",
        "date of accident": "doa",
        "date of injury": "doa",
        "service date": "doa",
        "dob": "dob",
        "date of birth": "dob",
        "birth date": "dob",
        "birth": "dob",
        "referral": "referral",
        "reason for visit": "referral",
        "referral details": "referral",
        "referral note": "referral",
        "instructions": "referral"
    }

    extracted_data = {}
    for entity in document.entities:
        key = entity.type_.lower()
        if key in key_map:
            if key_map[key] in extracted_data:
                extracted_data[key_map[key]] += f"; {entity.mention_text}"
            else:
                extracted_data[key_map[key]] = entity.mention_text

    return extracted_data

def preprocess_string(value):
    if not value:
        return ""
    return str(value).strip().lower()

def preprocess_date(value):
    try:
        dt = pd.to_datetime(value, errors="coerce")
        if hasattr(dt, "tzinfo") and dt.tzinfo is not None:
            dt = dt.tz_localize(None)
        return dt
    except:
        return pd.NaT

def load_dataset(file_path):
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Only CSV or XLSX supported")
    df.columns = [col.strip() for col in df.columns]
    return df

def detect_column(df, possible_names, threshold=80):
    best_col, best_score = None, 0
    for col in df.columns:
        for name in possible_names:
            score = fuzz.ratio(preprocess_string(col), preprocess_string(name))
            if score > best_score:
                best_score = score
                best_col = col
    return best_col if best_score >= threshold else None

def match_extracted_data_dynamic(extracted_data, df, date_tolerance_days=3):
    NAME_COLUMNS = ["Name", "Client Name", "Patient Name", "Full Name"]
    DOA_COLUMNS = ["DOA", "Date of Accident", "Date of Injury", "Service Date"]
    DOB_COLUMNS = ["DOB", "Date of Birth", "Birth Date", "Birth"]
    REFERRAL_COLUMNS = ["Referral", "Reason for Visit", "Referral Notes", "Instructions"]

    name_col = detect_column(df, NAME_COLUMNS)
    doa_col = detect_column(df, DOA_COLUMNS)
    dob_col = detect_column(df, DOB_COLUMNS)
    referral_col = detect_column(df, REFERRAL_COLUMNS)

    ex_name = preprocess_string(extracted_data.get("name"))
    ex_doa = preprocess_date(extracted_data.get("doa"))
    ex_dob = preprocess_date(extracted_data.get("dob"))
    ex_referral = preprocess_string(extracted_data.get("referral"))

    matches = []
    for idx, row in df.iterrows():
        row_name = preprocess_string(row.get(name_col, ""))
        row_doa = preprocess_date(row.get(doa_col, ""))
        row_dob = preprocess_date(row.get(dob_col, ""))
        row_referral = preprocess_string(row.get(referral_col, ""))

        name_score = fuzz.token_sort_ratio(ex_name, row_name)
        name_match = name_score > 90
        doa_match = pd.notna(ex_doa) and pd.notna(row_doa) and abs((ex_doa - row_doa).days) <= date_tolerance_days
        dob_match = pd.notna(ex_dob) and ex_dob == row_dob
        referral_score = fuzz.partial_ratio(ex_referral, row_referral) if ex_referral and row_referral else 0
        referral_match = referral_score > 70

        if name_match and doa_match and dob_match:
            status = "Strong Match"
        elif name_match and (doa_match or dob_match):
            status = "Probable Match"
        elif name_match:
            status = "Name Match Only"
        else:
            status = "Mismatch"

        matches.append({
            "Dataset_Index": idx,
            "Dataset_Name": row.get(name_col, ""),
            "Dataset_DOA": str(row.get(doa_col, "")),
            "Dataset_DOB": str(row.get(dob_col, "")),
            "Dataset_Referral": row.get(referral_col, ""),
            "Extracted_Name": ex_name,
            "Extracted_DOA": str(ex_doa),
            "Extracted_DOB": str(ex_dob),
            "Extracted_Referral": ex_referral,
            "Name_Score": name_score,
            "DOA_Match": doa_match,
            "DOB_Match": dob_match,
            "Referral_Score": referral_score,
            "Referral_Match": referral_match,
            "Match_Status": status
        })

    return matches

def process_pdf(pdf_path, dataset_file, project_id, location, processor_id):
    df = load_dataset(dataset_file)
    pdf_parts = split_pdf(pdf_path)
    extracted_combined = {}

    for part in pdf_parts:
        part_extracted = extract_fields_from_pdf(project_id, location, processor_id, part)
        for k, v in part_extracted.items():
            if k in extracted_combined:
                extracted_combined[k] += f"; {v}"
            else:
                extracted_combined[k] = v
        os.remove(part)

    if not extracted_combined:
        return {"error": f"No data extracted from {pdf_path}"}

    result = match_extracted_data_dynamic(extracted_combined, df)
    return result
