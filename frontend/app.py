import streamlit as st
import pandas as pd
import requests
import os

st.set_page_config(page_title="Japan Invoice Extraction System", layout="wide")

API_URL = "http://127.0.0.1:8000/api/extract_invoice"
EXCEL_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "invoices_database.xlsx")

st.title("Japan Invoice Extraction System")

if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None
if "global_warning" not in st.session_state:
    st.session_state.global_warning = False
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

def start_processing():
    st.session_state.is_processing = True

col_image, col_data = st.columns([1, 1.2], gap="large")

with col_image:
    st.subheader("1. Upload Invoice")
    uploaded_file = st.file_uploader("Please upload Invoice Photo", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        st.image(uploaded_file, use_container_width=True)
        if st.button(
            "Start", 
            type="primary", 
            use_container_width=True,
            on_click=start_processing,
            disabled=st.session_state.is_processing
            ):
            with st.spinner("Local multimodal AI processing..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    res = requests.post(API_URL, files=files)
                    
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.extracted_data = data.get("invoice_data", data)
                        st.session_state.global_warning = data.get("global_warning", True)
                        st.session_state.is_processing = False
                        st.rerun()
                    else:
                        st.error(f"Error: {res.text}")  
                except Exception as e:
                    st.error(f"Error: {e}")    

with col_data:
    st.subheader("2. Write Into Excel")

    if st.session_state.extracted_data is not None:
        if st.session_state.global_warning:
            st.warning("AI detected uncertain characters. Please verify the checked rows on the right!")
        else:
            st.success("AI confidence high. Safe to save directly.") 

        data = st.session_state.extracted_data
        df_rows = []

        def parse_field(field_data, default_warning):
            if isinstance(field_data, dict):
                return str(field_data.get("value", "")), field_data.get("needs_review", default_warning)
            return str(field_data), default_warning

        # 解析日期
        val, req_rev = parse_field(data.get("date", ""), st.session_state.global_warning)
        df_rows.append({"字段": "日期", "识别结果": val, "需人工核对": req_rev})

        # 解析商品列表
        items_list = data.get("items", [])
        if not items_list:
            df_rows.append({"字段": "商品 1", "识别结果": "未识别到商品", "需人工核对": True})
        else:
            for i, item in enumerate(items_list):
                val, req_rev = parse_field(item, st.session_state.global_warning)
                df_rows.append({"字段": f"商品 {i+1}", "识别结果": val, "需人工核对": req_rev})

        # 解析总金额
        val, req_rev = parse_field(data.get("total_amount", ""), st.session_state.global_warning)
        df_rows.append({"字段": "总金额", "识别结果": val, "需人工核对": req_rev})

        # 转换为 DataFrame
        df_display = pd.DataFrame(df_rows)

        # 渲染可编辑表格
        edited_df = st.data_editor(
            df_display,
            column_config={
                "字段": st.column_config.TextColumn(disabled=True),
                "识别结果": st.column_config.TextColumn("识别结果 (可双击修改)"),
                "需人工核对": st.column_config.CheckboxColumn("需人工核对 (确认无误后取消勾选)")
            },
            hide_index=True,
            use_container_width=True,
            key="data_editor"
        )

        has_warnings = edited_df["需人工核对"].any()
        if has_warnings:
            st.error("请人工核对异常字段，确认无误后**取消表格右侧的勾选**才能写入数据库。")

        if st.button("写入 Excel 数据库", type="primary", disabled=has_warnings, use_container_width=True):
            # 安全提取数据写入
            final_date = edited_df[edited_df["字段"] == "日期"].iloc[0]["识别结果"]
            final_amount = edited_df[edited_df["字段"] == "总金额"].iloc[0]["识别结果"]

            items_df = edited_df[edited_df["字段"].str.startswith("商品")]
            items_values = items_df["识别结果"].tolist()
            final_items_str = ", ".join([str(item) for item in items_values if str(item).strip() != ""])

            final_record = {
                "日期": final_date,
                "包含商品明细": final_items_str,
                "总金额": final_amount
            }

            new_df = pd.DataFrame([final_record])

            try:
                os.makedirs(os.path.dirname(EXCEL_FILE), exist_ok=True)
                
                if os.path.exists(EXCEL_FILE):
                    existing_df = pd.read_excel(EXCEL_FILE)
                    existing_df = existing_df.dropna(how='all')
                    updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                else:
                    updated_df = new_df

                updated_df.to_excel(EXCEL_FILE, index=False)
                st.balloons()
                st.success("成功录入！数据已安全保存至 data/invoices_database.xlsx")

                st.session_state.extracted_data = None
                st.session_state.global_warning = False
                
            except PermissionError:
                st.error("写入失败：检测到 Excel 文件正在被其他程序占用，请先关闭该 Excel 文件后再试！")
            except Exception as e:
                st.error(f"写入失败: {e}")