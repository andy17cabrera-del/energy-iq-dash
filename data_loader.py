import pandas as pd
import numpy as np
import datetime
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUDGET_FILE = os.path.join(BASE_DIR, "presupuesto_energia.xlsx")
REAL_FILE   = os.path.join(BASE_DIR, "real_energia.xlsx")

def _is_date(v):
    return isinstance(v, (pd.Timestamp, datetime.datetime)) and not isinstance(v, bool)

def parse_period(p):
    p = str(p)
    m = re.match(r"(\d{2})m(\d{1,2})$", p)
    if m:
        return pd.Timestamp(int("20"+m.group(1)), int(m.group(2)), 1)
    m = re.match(r"(\d{4})-(\d{2})$", p)
    if m:
        return pd.Timestamp(int(m.group(1)), int(m.group(2)), 1)
    m = re.match(r"(\d{4})$", p)
    if m:
        return pd.Timestamp(int(m.group(1)), 6, 1)
    m = re.match(r"(\d{2})q(\d)$", p)
    if m:
        return pd.Timestamp(int("20"+m.group(1)), (int(m.group(2))-1)*3+1, 1)
    return pd.NaT

BUDGET_COL_MAP = {
    8:"23m1",9:"23m2",10:"23m3",11:"23m4",12:"23m5",13:"23m6",
    14:"23m7",15:"23m8",16:"23m9",17:"23m10",18:"23m11",19:"23m12",
    22:"24m1",23:"24m2",24:"24m3",25:"24m4",26:"24m5",27:"24m6",
    28:"24m7",29:"24m8",30:"24m9",31:"24m10",32:"24m11",33:"24m12",
    36:"25m1",37:"25m2",38:"25m3",39:"25m4",40:"25m5",41:"25m6",
    42:"25m7",43:"25m8",44:"25m9",45:"25m10",46:"25m11",47:"25m12",
    50:"26m1",51:"26m2",52:"26m3",53:"26m4",54:"26m5",55:"26m6",
    56:"26m7",57:"26m8",58:"26m9",59:"26m10",60:"26m11",61:"26m12",
    78:"27m1",79:"27m2",80:"27m3",81:"27m4",82:"27m5",83:"27m6",
    84:"27m7",85:"27m8",86:"27m9",87:"27m10",88:"27m11",89:"27m12",
}

REAL_ROWS   = {"G&A":1,"Mina":12,"Sulfuros":18,"Óxidos":30,"Infraestructura":27,"Mantenimiento":9}
BUDGET_ROWS = {"G&A":86,"Mina":96,"Sulfuros":106,"Infraestructura":116,"Mantenimiento":101,"Óxidos":120}
BILL_ROWS   = {"G&A":65,"Mantenimiento":66,"Mina":67,"Sulfuros":68,"Infraestructura":69,"Óxidos":70}
RATIO_ROWS_BUDGET = {
    "UNITARIO TOTAL":21,"PLANTA SULFUROS_ratio":43,
    "INFRAESTRUCTURA_ratio":53,"OXIDOS_EW_ratio":69,"OXIDOS_SECO_ratio":58,
}

BUDGET_DATES = set(parse_period(p) for p in BUDGET_COL_MAP.values() if pd.notna(parse_period(p)))

def load_real():
    df = pd.read_excel(REAL_FILE, sheet_name="DETALLE ENERGIA Y FACTURA", header=None)
    records = []
    for ci in range(4, min(72, df.shape[1])):
        fv = df.iloc[0, ci]
        if not _is_date(fv):
            continue
        fecha = pd.Timestamp(fv)
        for area, row in REAL_ROWS.items():
            val = pd.to_numeric(df.iloc[row, ci], errors="coerce")
            if pd.notna(val) and val > 0:
                records.append({"area":area,"fecha":fecha,"kwh_real":float(val),
                                 "in_budget": fecha in BUDGET_DATES})
    return pd.DataFrame(records)

def load_budget_kwh():
    df = pd.read_excel(BUDGET_FILE, sheet_name="LOM25 Óptimo", header=None)
    records = []
    for area, row in BUDGET_ROWS.items():
        for col, period in BUDGET_COL_MAP.items():
            if col < df.shape[1]:
                val   = pd.to_numeric(df.iloc[row, col], errors="coerce")
                fecha = parse_period(period)
                if pd.notna(val) and val > 0 and pd.notna(fecha):
                    records.append({"area":area,"fecha":fecha,"kwh_ppto":float(val)})
    return pd.DataFrame(records)

def load_billing():
    df = pd.read_excel(REAL_FILE, sheet_name="DETALLE ENERGIA Y FACTURA", header=None)
    records = []
    for ci in range(4, min(72, df.shape[1])):
        fv = df.iloc[0, ci]
        if not _is_date(fv):
            continue
        fecha = pd.Timestamp(fv)
        for area, row in BILL_ROWS.items():
            val = pd.to_numeric(df.iloc[row, ci], errors="coerce")
            if pd.notna(val):
                records.append({"area":area,"fecha":fecha,"usd":float(val)})
    return pd.DataFrame(records)

def load_budget_ratios():
    df = pd.read_excel(BUDGET_FILE, sheet_name="LOM25 Óptimo", header=None)
    records = []
    for nombre, row in RATIO_ROWS_BUDGET.items():
        for col, period in BUDGET_COL_MAP.items():
            if col < df.shape[1]:
                val   = pd.to_numeric(df.iloc[row, col], errors="coerce")
                fecha = parse_period(period)
                if pd.notna(val) and val > 0 and pd.notna(fecha):
                    records.append({"ratio":nombre,"fecha":fecha,"ratio_ppto":float(val)})
    return pd.DataFrame(records)

def load_real_ratios():
    df = pd.read_excel(REAL_FILE, sheet_name="DETALLE ENERGIA Y FACTURA", header=None)
    records = []
    for ci in range(4, min(72, df.shape[1])):
        fv = df.iloc[0, ci]
        if not _is_date(fv):
            continue
        fecha = pd.Timestamp(fv)
        v59 = pd.to_numeric(df.iloc[59, ci], errors="coerce")
        if pd.notna(v59) and v59 > 0:
            records.append({"ratio":"PLANTA SULFUROS_ratio","fecha":fecha,"valor_real":float(v59)})
        v61 = pd.to_numeric(df.iloc[61, ci], errors="coerce")
        if pd.notna(v61) and v61 > 0:
            records.append({"ratio":"INFRAESTRUCTURA_ratio","fecha":fecha,"valor_real":float(v61)})
        drv = pd.to_numeric(df.iloc[55, ci], errors="coerce")
        if pd.isna(drv) or drv <= 0:
            continue
        kew = pd.to_numeric(df.iloc[42, ci], errors="coerce")
        if pd.notna(kew) and kew > 0:
            records.append({"ratio":"OXIDOS_EW_ratio","fecha":fecha,"valor_real":float(kew/drv)})
        kot = pd.to_numeric(df.iloc[30, ci], errors="coerce")
        if pd.notna(kot) and pd.notna(kew) and kot > kew:
            records.append({"ratio":"OXIDOS_SECO_ratio","fecha":fecha,"valor_real":float((kot-kew)/drv)})
    return pd.DataFrame(records)
