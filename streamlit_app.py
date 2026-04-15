import streamlit as st
import pandas as pd
from datetime import date
import io

st.set_page_config(page_title="🥖 Panadería - Control de Producción", layout="wide")

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
    "Banofee":                          15,
    "Galleta Canela":                   15,
    "Galleta Chispas de Choco":         15,
    "Galleta Choco Nuez":               15,
    "Galleta Masa Madre":               15,
    "Galleta Matcha":                   15,
    "Galleta Pistache":                 15,
    "Muffin":                           15,
    "Tarta Vasca Dulce":                15,
    "Tarta Vasca Pistache":             15,
    "Tarta Vasca Tradicional Chica":    15,
    "Tarta Vasca Tradicional Grande":   15,
}

# ─── ESTADO DE SESIÓN ────────────────────────────────────────────────────────
if "productos" not in st.session_state:
    st.session_state.productos = PRODUCTOS_DEFAULT.copy()
if "inv_perisur" not in st.session_state:
    st.session_state.inv_perisur = {p: 0 for p in st.session_state.productos}
if "inv_primavera" not in st.session_state:
    st.session_state.inv_primavera = {p: 0 for p in st.session_state.productos}
if "perisur_guardado" not in st.session_state:
    st.session_state.perisur_guardado = False
if "primavera_guardado" not in st.session_state:
    st.session_state.primavera_guardado = False

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("# 🥖 Panadería — Control de Producción")
st.markdown(f"**{date.today().strftime('%A %d de %B, %Y')}**")
st.divider()

# ─── PESTAÑAS ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🌙 Inventario Nocturno",
    "☀️ Orden de Horneado",
    "⚙️ Productos y Óptimos",
    "📥 Exportar"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — INVENTARIO NOCTURNO
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Captura el inventario al cierre de cada sucursal")
    st.info("Anota cuántas piezas quedan en cada sucursal al final del día.")

    col_perisur, col_primavera = st.columns(2, gap="large")

    # — PERISUR —
    with col_perisur:
        st.markdown("#### 🏪 Sucursal Perisur")
        inv_p = {}
        for prod in st.session_state.productos:
            inv_p[prod] = st.selectbox(
                prod,
                options=list(range(9)),
                index=st.session_state.inv_perisur.get(prod, 0),
                key=f"perisur_{prod}"
            )
        if st.button("💾 Guardar Perisur", use_container_width=True):
            st.session_state.inv_perisur = inv_p
            st.session_state.perisur_guardado = True
            st.success("✅ Inventario Perisur guardado")

    # — PRIMAVERA —
    with col_primavera:
        st.markdown("#### 🏪 Sucursal Primavera")
        inv_v = {}
        for prod in st.session_state.productos:
            inv_v[prod] = st.selectbox(
                prod,
                options=list(range(9)),
                index=st.session_state.inv_primavera.get(prod, 0),
                key=f"primavera_{prod}"
            )
        if st.button("💾 Guardar Primavera", use_container_width=True):
            st.session_state.inv_primavera = inv_v
            st.session_state.primavera_guardado = True
            st.success("✅ Inventario Primavera guardado")

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
# TAB 2 — ORDEN DE HORNEADO
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### ☀️ Orden de producción para hoy")

    ambos_listos = st.session_state.perisur_guardado and st.session_state.primavera_guardado
    solo_uno = st.session_state.perisur_guardado or st.session_state.primavera_guardado

    if not solo_uno:
        st.warning("⚠️ Aún no hay inventarios guardados. Ve a la pestaña **Inventario Nocturno** primero.")
    else:
        if not ambos_listos:
            faltante = "Primavera" if st.session_state.perisur_guardado else "Perisur"
            st.warning(f"⚠️ Solo está guardado un inventario. Falta **{faltante}**. Se calculará con lo disponible.")

        if st.button("🔥 Generar Orden de Horneado", use_container_width=True):

            orden = []
            for prod, optimo in st.session_state.productos.items():
                p = st.session_state.inv_perisur.get(prod, 0)
                v = st.session_state.inv_primavera.get(prod, 0)
                total_inv = p + v
                a_hornear = max(0, optimo - total_inv)
                orden.append({
                    "Producto": prod,
                    "Óptimo": optimo,
                    "Perisur": p,
                    "Primavera": v,
                    "Total inventario": total_inv,
                    "🔥 A hornear": a_hornear,
                })

            df_orden = pd.DataFrame(orden)
            df_sin_cero = df_orden[df_orden["🔥 A hornear"] > 0]

            # Mostrar orden visual
            st.markdown('<div class="orden-box">', unsafe_allow_html=True)
            st.markdown(f'<div class="orden-titulo">🧾 Orden de Horneado — {date.today().strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)

            if df_sin_cero.empty:
                st.success("🎉 ¡Inventario suficiente! No se necesita hornear nada hoy.")
            else:
                total_piezas = df_sin_cero["🔥 A hornear"].sum()
                for _, row in df_sin_cero.iterrows():
                    st.markdown(
                        f'<div class="orden-fila">'
                        f'<span>{row["Producto"]}</span>'
                        f'<span><b>{int(row["🔥 A hornear"])} piezas</b></span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                st.markdown(
                    f'<div class="orden-fila" style="margin-top:0.8rem;font-weight:bold;font-size:1.1rem;">'
                    f'<span>TOTAL</span><span>{int(total_piezas)} piezas</span></div>',
                    unsafe_allow_html=True
                )

            st.markdown('</div>', unsafe_allow_html=True)

            # Guardar para exportar
            st.session_state.df_orden = df_orden

            # Tabla completa
            st.markdown("#### Detalle completo")
            st.dataframe(df_orden, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — PRODUCTOS Y ÓPTIMOS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### ⚙️ Gestiona los productos y sus cantidades óptimas")
    st.info("El **óptimo** es la cantidad ideal que debe haber en total entre las dos sucursales cada mañana.")

    # Editar óptimos
    st.markdown("#### Editar óptimos actuales")
    nuevos_optimos = {}
    cols = st.columns(3)
    for i, (prod, opt) in enumerate(st.session_state.productos.items()):
        with cols[i % 3]:
            nuevos_optimos[prod] = st.number_input(
                prod, min_value=1, value=opt, key=f"opt_{prod}", step=5
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

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — EXPORTAR
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 📥 Exportar reporte del día")

    if "df_orden" not in st.session_state:
        st.warning("⚠️ Primero genera la orden de horneado en la pestaña ☀️.")
    else:
        df_orden = st.session_state.df_orden
        fecha_hoy = date.today().strftime("%Y-%m-%d")

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_orden.to_excel(writer, sheet_name="Orden_Horneado", index=False)

            # Hoja de inventarios
            df_inv = pd.DataFrame({
                "Producto": list(st.session_state.productos.keys()),
                "Inventario Perisur": [st.session_state.inv_perisur.get(p, 0) for p in st.session_state.productos],
                "Inventario Primavera": [st.session_state.inv_primavera.get(p, 0) for p in st.session_state.productos],
            })
            df_inv.to_excel(writer, sheet_name="Inventarios", index=False)

        buffer.seek(0)
        st.download_button(
            label="⬇️ Descargar Excel del día",
            data=buffer,
            file_name=f"panaderia_orden_{fecha_hoy}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        st.markdown("#### Vista previa de la orden")
        st.dataframe(df_orden, use_container_width=True, hide_index=True)
