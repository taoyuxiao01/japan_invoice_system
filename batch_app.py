import os
import uuid

import pandas as pd
import requests
import streamlit as st


st.set_page_config(page_title="Japan Invoice Extraction System", layout="wide")

API_URL = "http://127.0.0.1:8000/api/extract_invoice"
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "data", "exports")

FIELD_LABELS = {
    "date": "日期",
    "items": "商品明细",
    "total_amount": "总金额",
}


def init_state():
    defaults = {
        "batch_results": [],
        "is_processing": False,
        "saved_excel_bytes": None,
        "saved_excel_filename": None,
        "saved_excel_path": None,
        "saved_row_count": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def parse_field(field_data, default_warning=False):
    if isinstance(field_data, dict):
        return str(field_data.get("value", "")), bool(
            field_data.get("needs_review", default_warning)
        )
    return str(field_data or ""), bool(default_warning)


def invoice_to_rows(result):
    data = result.get("invoice_data") or {}
    default_warning = bool(result.get("global_warning", True))
    rows = []

    value, needs_review = parse_field(data.get("date", ""), default_warning)
    rows.append(
        {
            "字段": FIELD_LABELS["date"],
            "识别结果": value,
            "需要人工核对": needs_review,
        }
    )

    items = data.get("items", [])
    if not items:
        rows.append({"字段": "商品 1", "识别结果": "", "需要人工核对": True})
    else:
        for index, item in enumerate(items, start=1):
            value, needs_review = parse_field(item, default_warning)
            rows.append(
                {
                    "字段": f"商品 {index}",
                    "识别结果": value,
                    "需要人工核对": needs_review,
                }
            )

    value, needs_review = parse_field(data.get("total_amount", ""), default_warning)
    rows.append(
        {
            "字段": FIELD_LABELS["total_amount"],
            "识别结果": value,
            "需要人工核对": needs_review,
        }
    )

    return pd.DataFrame(rows)


def rows_to_record(filename, edited_df):
    date_rows = edited_df[edited_df["字段"] == FIELD_LABELS["date"]]
    amount_rows = edited_df[edited_df["字段"] == FIELD_LABELS["total_amount"]]
    item_rows = edited_df[edited_df["字段"].str.startswith("商品", na=False)]

    final_date = date_rows.iloc[0]["识别结果"] if not date_rows.empty else ""
    final_amount = amount_rows.iloc[0]["识别结果"] if not amount_rows.empty else ""
    final_items = ", ".join(
        str(value).strip()
        for value in item_rows["识别结果"].tolist()
        if str(value).strip()
    )

    return {
        "文件名": filename,
        "日期": final_date,
        "包含商品明细": final_items,
        "总金额": final_amount,
    }


def create_export_file(records):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    export_id = uuid.uuid4().hex
    filename = f"invoices_{export_id}.xlsx"
    path = os.path.join(EXPORT_DIR, filename)

    df = pd.DataFrame(records)
    df.to_excel(path, index=False, sheet_name="invoices")

    with open(path, "rb") as excel_file:
        excel_bytes = excel_file.read()

    return filename, path, excel_bytes


def cleanup_export_file(path):
    if path and os.path.exists(path):
        os.remove(path)


def extract_all(uploaded_files):
    results = []
    progress = st.progress(0, text="准备开始提取...")

    for index, uploaded_file in enumerate(uploaded_files, start=1):
        progress.progress(
            (index - 1) / len(uploaded_files),
            text=f"正在提取 {index}/{len(uploaded_files)}: {uploaded_file.name}",
        )

        image_bytes = uploaded_file.getvalue()
        result = {
            "filename": uploaded_file.name,
            "mime_type": uploaded_file.type,
            "image_bytes": image_bytes,
            "invoice_data": {},
            "global_warning": True,
            "error": None,
        }

        try:
            files = {"file": (uploaded_file.name, image_bytes, uploaded_file.type)}
            response = requests.post(API_URL, files=files, timeout=180)

            if response.status_code == 200:
                payload = response.json()
                result["invoice_data"] = payload.get("invoice_data", payload)
                result["global_warning"] = payload.get("global_warning", True)
            else:
                result["error"] = response.text
        except Exception as exc:
            result["error"] = str(exc)

        results.append(result)

    progress.progress(1.0, text="全部图片提取完成")
    return results


init_state()

st.title("Japan Invoice Extraction System")
st.caption("批量上传发票或收据图片，全部提取完成后统一人工核对，并生成总 Excel。")

uploaded_files = st.file_uploader(
    "请选择一批图片",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

top_left, top_right = st.columns([1.2, 1], gap="large")

with top_left:
    if uploaded_files:
        st.subheader("1. 批量上传")
        st.write(f"已选择 {len(uploaded_files)} 张图片")

        preview_cols = st.columns(min(4, len(uploaded_files)))
        for index, uploaded_file in enumerate(uploaded_files[:4]):
            with preview_cols[index]:
                st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)

        if len(uploaded_files) > 4:
            st.caption(f"还有 {len(uploaded_files) - 4} 张图片会一起处理。")

        if st.button(
            "开始批量提取",
            type="primary",
            disabled=st.session_state.is_processing,
            use_container_width=True,
        ):
            st.session_state.is_processing = True
            st.session_state.saved_excel_bytes = None
            st.session_state.saved_excel_filename = None
            cleanup_export_file(st.session_state.saved_excel_path)
            st.session_state.saved_excel_path = None
            with st.spinner("本地 AI 正在逐张识别，请稍候..."):
                st.session_state.batch_results = extract_all(uploaded_files)
            st.session_state.is_processing = False
            st.rerun()
    else:
        st.info("先选择多张图片，然后点击开始批量提取。")

with top_right:
    st.subheader("2. 当前状态")
    results = st.session_state.batch_results
    success_count = sum(1 for result in results if not result.get("error"))
    error_count = sum(1 for result in results if result.get("error"))
    review_count = sum(
        1 for result in results if result.get("global_warning") and not result.get("error")
    )

    metric_cols = st.columns(3)
    metric_cols[0].metric("已提取", success_count)
    metric_cols[1].metric("需关注", review_count)
    metric_cols[2].metric("失败", error_count)

    if st.session_state.saved_excel_bytes:
        st.success(f"已保存 {st.session_state.saved_row_count} 条记录。")
        downloaded = st.download_button(
            "下载总 Excel",
            data=st.session_state.saved_excel_bytes,
            file_name=st.session_state.saved_excel_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        if downloaded:
            cleanup_export_file(st.session_state.saved_excel_path)
            st.session_state.saved_excel_bytes = None
            st.session_state.saved_excel_filename = None
            st.session_state.saved_excel_path = None
            st.success("下载已开始，本地临时 Excel 已删除。")

results = st.session_state.batch_results

if results:
    st.divider()
    st.subheader("3. 人工检查")

    editable_results = [result for result in results if not result.get("error")]
    failed_results = [result for result in results if result.get("error")]

    for result in failed_results:
        with st.expander(f"{result['filename']} - 提取失败", expanded=True):
            st.error(result["error"])
            st.image(result["image_bytes"], use_container_width=True)

    edited_tables = {}
    has_warnings = False

    for index, result in enumerate(editable_results):
        review_flag = "需要核对" if result.get("global_warning") else "置信度较高"
        with st.expander(f"{index + 1}. {result['filename']} - {review_flag}", expanded=True):
            image_col, table_col = st.columns([0.9, 1.4], gap="large")

            with image_col:
                st.image(result["image_bytes"], use_container_width=True)

            with table_col:
                df_display = invoice_to_rows(result)
                edited_df = st.data_editor(
                    df_display,
                    column_config={
                        "字段": st.column_config.TextColumn("字段", disabled=True),
                        "识别结果": st.column_config.TextColumn("识别结果"),
                        "需要人工核对": st.column_config.CheckboxColumn("需要人工核对"),
                    },
                    hide_index=True,
                    use_container_width=True,
                    key=f"invoice_editor_{index}_{result['filename']}",
                )
                edited_tables[result["filename"]] = edited_df

                if edited_df["需要人工核对"].any():
                    has_warnings = True
                    st.warning("请确认并修改识别结果，确认无误后取消勾选。")

    st.divider()
    save_disabled = has_warnings or not editable_results

    if failed_results:
        st.warning("有图片提取失败，失败图片不会写入 Excel。可以重新上传后再处理。")

    if st.button(
        "保存全部已核对记录",
        type="primary",
        disabled=save_disabled,
        use_container_width=True,
    ):
        records = [
            rows_to_record(filename, edited_df)
            for filename, edited_df in edited_tables.items()
        ]

        try:
            filename, path, excel_bytes = create_export_file(records)
            cleanup_export_file(st.session_state.saved_excel_path)
            st.session_state.saved_excel_bytes = excel_bytes
            st.session_state.saved_excel_filename = filename
            st.session_state.saved_excel_path = path
            st.session_state.saved_row_count = len(records)
            st.success("保存完成，可以下载总 Excel 文件。")
            st.rerun()
        except PermissionError:
            st.error("写入失败：Excel 文件正在被其他程序占用，请先关闭后再保存。")
        except Exception as exc:
            st.error(f"写入失败：{exc}")

    if save_disabled and editable_results:
        st.error("还有记录被标记为需要人工核对，全部取消勾选后才能保存。")
