import streamlit as st
import pandas as pd
from datetime import date
import io
from twilio.rest import Client

st.set_page_config(page_title="🥖 Panadería", layout="wide")

# ─── ESTILOS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #fdf6ec;
    color: #2c1a0e;
}
h1, h2, h3 {
    font-family: 'Playfair Display', serif;
    color: #7b3f00;
}
.stButton > button {
    background-color: #c8692a;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.5rem;
    font-size: 1rem;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    transition: background 0.2s;
}
.stButton > button:hover {
    background-color: #a0501e;
    color: white;
}
.orden-box {
    background: #fff8f0;
    border: 2px solid #c8692a;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-top: 1rem;
}
.orden-fila {
    display: flex;
    justify-content: space-between;
    padding: 0.4rem 0;
    border-bottom: 1px dashed #e0c8b0;
    font-size: 1rem;
}
.orden-titulo {
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem;
    color: #7b3f00;
    margin-bottom: 1rem;
}
.badge-prod {
    background: #fde8d0;
    color: #7b3f00;
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.85rem;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ─── PRODUCTOS Y ÓPTIMOS ─────────────────────────────────────────────────────
PRODUCTOS_DEFAULT = {
    "Banofee":                          0,
    "Galleta Canela":                   5,
    "Galleta Chispas Masa Madre":       5,
    "Galleta Choco Nuez":               5,
    "Galleta Matcha":                   5,
    "Galleta Ola":                      8,
    "Galleta Pistache":                 5,
    "Muffin":                           6,
    "Tarta Vasca Dulce":                3,
    "Tarta Vasca Pistache":             3,
    "Tarta Vasca Tradicional Chica":    3,
    "Tarta Vasca Tradicional Grande":   3,
}

# ─── ESTADO DE SESIÓN ────────────────────────────────────────────────────────
if "productos" not in st.session_state:
    st.session_state.productos = PRODUCTOS_DEFAULT.copy()
if "inv_perisur" not in st.session_state:
    st.session_state.inv_perisur = {p: None for p in st.session_state.productos}
if "inv_primavera" not in st.session_state:
    st.session_state.inv_primavera = {p: None for p in st.session_state.productos}
if "perisur_guardado" not in st.session_state:
    st.session_state.perisur_guardado = False
if "primavera_guardado" not in st.session_state:
    st.session_state.primavera_guardado = False
if "sms_enviado" not in st.session_state:
    st.session_state.sms_enviado = False

# ─── FUNCIÓN ENVIAR SMS ──────────────────────────────────────────────────────
def enviar_sms_orden():
    try:
        account_sid = st.secrets["TWILIO_ACCOUNT_ID"]
        auth_token  = st.secrets["TWILIO_AUTH_TOKEN"]
        from_number = st.secrets["TWILIO_FROM"]
        to_number   = st.secrets["TWILIO_TO"]

        hoy = date.today().strftime("%d/%m/%Y")
        lineas = [f"Orden Panaderia {hoy}", ""]
        total = 0
        for prod, optimo in st.session_state.productos.items():
            p = st.session_state.inv_perisur.get(prod, 0) or 0
            v = st.session_state.inv_primavera.get(prod, 0) or 0
            a_hornear = max(0, optimo - p - v)
            if a_hornear > 0:
                lineas.append(f"{a_hornear} - {prod}")
                total += a_hornear
        lineas.append(f"-------------")
        lineas.append(f"TOTAL: {total} piezas")
        mensaje = "\n".join(lineas)

        client = Client(account_sid, auth_token)
        client.messages.create(body=mensaje, from_=from_number, to=to_number)
        st.session_state.sms_enviado = True
    except Exception as e:
        st.error(f"❌ Error al enviar SMS: {e}")

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("# 🥖 Panadería — Control de Producción")
st.markdown(f"**{date.today().strftime('%A %d de %B, %Y')}**")
st.divider()

# ─── PESTAÑAS ────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs([
    "🌙 Inventario Nocturno",
    "⚙️ Productos y Óptimos",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — INVENTARIO NOCTURNO
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Captura el inventario al cierre de cada sucursal")
    st.info("Anota cuántas piezas quedan en cada sucursal.")

    col_perisur, col_primavera = st.columns(2, gap="large")

    # — PERISUR —
    with col_perisur:
        st.markdown("#### 🏪 Sucursal Perisur")
        inv_p = {}
        for prod in st.session_state.productos:
            valor_guardado = st.session_state.inv_perisur.get(prod, None)
            opciones = ["— elige —"] + list(range(9))
            if valor_guardado is not None:
                idx = valor_guardado + 1  # +1 por el "— elige —"
            else:
                idx = 0
            sel = st.selectbox(prod, options=opciones, index=idx, key=f"perisur_{prod}")
            inv_p[prod] = None if sel == "— elige —" else int(sel)

        perisur_completo = all(v is not None for v in inv_p.values())
        faltantes_p = [p for p, v in inv_p.items() if v is None]

        if faltantes_p:
            st.warning(f"⚠️ Faltan {len(faltantes_p)} productos por capturar")
        else:
            if st.button("💾 Guardar Perisur", use_container_width=True):
                st.session_state.inv_perisur = inv_p
                st.session_state.perisur_guardado = True
                st.success("✅ Inventario Perisur guardado")
                if st.session_state.primavera_guardado and not st.session_state.sms_enviado:
                    enviar_sms_orden()
                    st.success("📱 SMS enviado automáticamente")

    # — PRIMAVERA —
    with col_primavera:
        st.markdown("#### 🏪 Sucursal Primavera")
        inv_v = {}
        for prod in st.session_state.productos:
            valor_guardado = st.session_state.inv_primavera.get(prod, None)
            opciones = ["— elige —"] + list(range(9))
            if valor_guardado is not None:
                idx = valor_guardado + 1
            else:
                idx = 0
            sel = st.selectbox(prod, options=opciones, index=idx, key=f"primavera_{prod}")
            inv_v[prod] = None if sel == "— elige —" else int(sel)

        faltantes_v = [p for p, v in inv_v.items() if v is None]

        if faltantes_v:
            st.warning(f"⚠️ Faltan {len(faltantes_v)} productos por capturar")
        else:
            if st.button("💾 Guardar Primavera", use_container_width=True):
                st.session_state.inv_primavera = inv_v
                st.session_state.primavera_guardado = True
                st.success("✅ Inventario Primavera guardado")
                if st.session_state.perisur_guardado and not st.session_state.sms_enviado:
                    enviar_sms_orden()
                    st.success("📱 SMS enviado automáticamente")

    st.divider()
    # — RESUMEN RÁPIDO —
    if st.session_state.perisur_guardado or st.session_state.primavera_guardado:
        st.markdown("#### 📋 Resumen de inventarios capturados")
        df_res = pd.DataFrame({
            "Producto": list(st.session_state.productos.keys()),
            "Óptimo": list(st.session_state.productos.values()),
            "Perisur": [st.session_state.inv_perisur.get(p, 0) for p in st.session_state.productos],
            "Primavera": [st.session_state.inv_primavera.get(p, 0) for p in st.session_state.productos],
        })
        df_res["Total inventario"] = df_res["Perisur"] + df_res["Primavera"]
        df_res["A hornear"] = (df_res["Óptimo"] - df_res["Total inventario"]).clip(lower=0)
        st.dataframe(df_res, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PRODUCTOS Y ÓPTIMOS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### ⚙️ Productos y Óptimos")
    st.info("El **óptimo** es la cantidad ideal que debe haber en total entre las dos sucursales cada mañana.")

    # Editar óptimos
    st.markdown("#### Editar óptimos actuales")
    nuevos_optimos = {}
    cols = st.columns(3)
    for i, (prod, opt) in enumerate(st.session_state.productos.items()):
        with cols[i % 3]:
            nuevos_optimos[prod] = st.number_input(
                prod, min_value=0, value=opt, key=f"opt_{prod}", step=1
            )

    if st.button("💾 Guardar óptimos", use_container_width=True):
        st.session_state.productos = nuevos_optimos
        # Sincronizar inventarios con nuevos productos
        for p in nuevos_optimos:
            if p not in st.session_state.inv_perisur:
                st.session_state.inv_perisur[p] = 0
            if p not in st.session_state.inv_primavera:
                st.session_state.inv_primavera[p] = 0
        st.success("✅ Óptimos actualizados")

    st.divider()

    # Agregar producto nuevo
    st.markdown("#### ➕ Agregar nuevo producto")
    col_n1, col_n2, col_n3 = st.columns([3, 2, 1])
    with col_n1:
        nuevo_nombre = st.text_input("Nombre del producto", placeholder="Ej: Croissant")
    with col_n2:
        nuevo_optimo = st.number_input("Óptimo", min_value=1, value=30, step=5)
    with col_n3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Agregar"):
            if nuevo_nombre and nuevo_nombre not in st.session_state.productos:
                st.session_state.productos[nuevo_nombre] = nuevo_optimo
                st.session_state.inv_perisur[nuevo_nombre] = 0
                st.session_state.inv_primavera[nuevo_nombre] = 0
                st.success(f"✅ '{nuevo_nombre}' agregado")
                st.rerun()
            elif nuevo_nombre in st.session_state.productos:
                st.error("Ya existe ese producto")

    st.divider()

    # Eliminar producto
    st.markdown("#### 🗑️ Eliminar producto")
    prod_eliminar = st.selectbox("Selecciona el producto a eliminar", list(st.session_state.productos.keys()))
    if st.button("Eliminar producto seleccionado"):
        del st.session_state.productos[prod_eliminar]
        st.session_state.inv_perisur.pop(prod_eliminar, None)
        st.session_state.inv_primavera.pop(prod_eliminar, None)
        st.success(f"🗑️ '{prod_eliminar}' eliminado")
        st.rerun()
