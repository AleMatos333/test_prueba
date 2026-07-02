# app.py
import streamlit as st
import pandas as pd
import json
import os
import io  # Requerido para la conversión en memoria de los archivos descargables
from datetime import datetime
from questions import PF16_QUESTIONS
from scoring import calcular_puntajes_brutos, convertir_a_decatipos, generar_descripcion_factor, generar_informe_global

st.set_page_config(page_title="16-PF Portal Clínico", page_icon="🧠", layout="centered")

st.markdown("""
    <style>
    /* --- LIMPIEZA DE RECUADROS EN LA BARRA LATERAL --- */
    div[data-testid="stSidebarNav"] {
        background-color: transparent;
    }
    div[data-testid="stRadio"] > div {
        background-color: transparent !important;
        border: none !important;
        padding: 0px !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: transparent !important;
        box-shadow: none !important;
        border: none !important;
    }
    
    /* --- ESTILOS ORIGINALES DE LAS TARJETAS --- */
    .question-card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 6px solid #6366f1;
        color: #f3f4f6; /* CORRECCIÓN: Texto claro para alta legibilidad */
    }
    .question-card p {
        color: #f3f4f6 !important; /* Fuerza a que los párrafos hereden el color claro */
        font-size: 16px;
    }
    .badge {
        background-color: #4f46e5;
        color: white;
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 11px;
        font-weight: bold;
    }
    /* Estilo de la auditoría compacto pero legible */
    .audit-block {
        background-color: #111827;
        padding: 14px 20px;
        border-radius: 8px;
        margin-bottom: 12px;
        border-left: 4px solid #3b82f6;
    }
    .audit-title {
        font-size: 14px;
        font-weight: bold;
        color: #f3f4f6;
        margin-bottom: 6px;
    }
    /* LETRA GRANDE Y RESALTADA PARA LA OPCIÓN ELEGIDA */
    .audit-choice-highlight {
        font-size: 20px; 
        font-weight: 800;
        color: #10b981; /* Verde brillante */
        background-color: #064e3b;
        padding: 2px 10px;
        border-radius: 6px;
        margin-right: 8px;
    }
    .audit-text-desc {
        font-size: 14px;
        color: #e5e7eb;
    }
    .factor-tag {
        font-size: 12px;
        color: #9ca3af;
        font-style: italic;
        margin-left: 8px;
    }
    /* Tarjetas de contadores de letras */
    .counter-box {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        border-top: 4px solid #6366f1;
    }
    .counter-num {
        font-size: 26px;
        font-weight: bold;
        color: #f3f4f6;
    }
    </style>
""", unsafe_allow_html=True)

DB_FILE = "historial_clinico_16pf.json"

def obtener_password_especialista():
    """Lee la contraseña desde .streamlit/secrets.toml (clave PSY_PASSWORD).
    Si no existe un secrets.toml configurado, usa la contraseña actual como
    respaldo para no romper el acceso existente."""
    try:
        return st.secrets["PSY_PASSWORD"]
    except Exception:
        return os.getenv("PSY_PASSWORD", "Miriam16PF")

def guardar_test_en_disco(nombre, respuestas, edad=None, empresa=None):
    registro = {
        "nombre": nombre,
        "edad": edad,
        "empresa": empresa,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "respuestas": respuestas
    }
    datos = []
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except:
            datos = []
            
    datos.append(registro)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

def cargar_historial_clinico():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

# Funciones auxiliares para exportación de datos (Panel del Especialista)
def generar_excel_descargable(paciente_name, df_factores, respuestas_paciente, preguntas_def):
    """Genera un archivo Excel en memoria con los resultados y respuestas detalladas."""
    output = io.BytesIO()
    
    # Procesar las respuestas de manera tabular para el Excel
    filas_respuestas = []
    for q in preguntas_def:
        id_str = str(q["id"])
        resp_letra = respuestas_paciente.get(id_str, "N/A")
        resp_texto = q["options"].get(resp_letra, "Sin respuesta")
        filas_respuestas.append({
            "Ítem": q["id"],
            "Pregunta": q["text"],
            "Opción Seleccionada": resp_letra.upper(),
            "Texto Respuesta": resp_texto,
            "Factor Asociado": q["factor"]
        })
    df_respuestas = pd.DataFrame(filas_respuestas)
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_factores.to_excel(writer, sheet_name='Matriz de Factores', index=False)
        df_respuestas.to_excel(writer, sheet_name='Respuestas del Paciente', index=False)
        
    return output.getvalue()

def generar_txt_descargable(paciente_name, fecha, respuestas_paciente, preguntas_def):
    """Genera un archivo de texto plano resumido con las respuestas."""
    lineas = [
        f"INFORME DE RESPUESTAS - 16PF",
        f"Paciente: {paciente_name}",
        f"Fecha de Aplicación: {fecha}",
        "--------------------------------------------------\n"
    ]
    for q in preguntas_def:
        id_str = str(q["id"])
        resp_letra = respuestas_paciente.get(id_str, "-")
        resp_texto = q["options"].get(resp_letra, "")
        lineas.append(f"Ítem {q['id']}: [{resp_letra.upper()}] - {resp_texto}")
        
    return "\n".join(lineas)


if "respuestas" not in st.session_state:
    st.session_state.respuestas = {}
if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = 0
if "test_enviado" not in st.session_state:
    st.session_state.test_enviado = False

modo_app = st.sidebar.radio("Navegación del Sistema", ["📋 Aplicar Cuestionario", "👨‍⚕️ Panel Especialista"])

if modo_app == "📋 Aplicar Cuestionario":
    if not st.session_state.test_enviado:
        # Añadir el logo en la parte superior antes del título principal
        logo_path = next(
            (p for p in [
                "imagenes/logo_azul_sin_fondo_de_calidad_mas_grande-Photoroom-Photoroom.png",
                "imagenes/logo.png", "imagenes/logo.jpg", "imagenes/logo.jpeg",
                "logo.png", "logo.jpg", "logo.jpeg", "assets/logo.png"
            ] if os.path.exists(p)),
            None
        )
        if logo_path:
            LOGO_ANCHO_PX = 180  # 👈 Cambia solo este número para agrandar o achicar el logo
            import base64
            with open(logo_path, "rb") as f:
                logo_b64 = base64.b64encode(f.read()).decode()
            ext = logo_path.rsplit(".", 1)[-1].lower()
            st.markdown(
                f"""
                <div style='text-align:center; margin-bottom: 8px;'>
                    <img src='data:image/{ext};base64,{logo_b64}' width='{LOGO_ANCHO_PX}'>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<h1 style='text-align:center;'>Evaluación de Impacto y Acompañamiento Post-Sismo</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#9ca3af; font-size:18px;'>Por favor, responda de forma sincera.</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Bloque inicial de captura de datos personales
        nombre_paciente = st.text_input("Introduzca su Nombre y Apellido completo:")
        
        c_edad, c_empresa = st.columns(2)
        with c_edad:
            edad_paciente = st.number_input("Introduzca su Edad:", min_value=1, max_value=120, step=1, value=None, placeholder="Ej. 25")
        with c_empresa:
            empresa_paciente = st.text_input("Empresa de la que proviene:", placeholder="Nombre de la organización")
        
        # VERIFICACIÓN INTERNA: Solo si se completan los 3 campos obligatorios, aparecen las preguntas
        if not nombre_paciente or edad_paciente is None or not empresa_paciente.strip():
            st.warning("⚠️ Se requiere ingresar su Nombre, Edad y Empresa de procedencia para habilitar el cuestionario.")
            st.markdown("<p style='text-align:center; color:#9ca3af; font-size:18px;'>Tu respuesta es completamente confidencial.</p>", unsafe_allow_html=True)
        else:
            st.success("📝 Datos registrados. Puede proceder con el cuestionario a continuación.")
            st.markdown("---")
            
            total_preguntas = len(PF16_QUESTIONS)
            PREGUNTAS_POR_PAGINA = 5
            total_paginas = (total_preguntas // PREGUNTAS_POR_PAGINA) + (1 if total_preguntas % PREGUNTAS_POR_PAGINA > 0 else 0)
            
            progreso = len(st.session_state.respuestas) / total_preguntas
            st.progress(progreso)
            
            inicio = st.session_state.pagina_actual * PREGUNTAS_POR_PAGINA
            fin = min(inicio + PREGUNTAS_POR_PAGINA, total_preguntas)
            bloque_preguntas = PF16_QUESTIONS[inicio:fin]
            
            with st.form(key=f"form_paciente_{st.session_state.pagina_actual}"):
                respuestas_pagina = {}
                for q in bloque_preguntas:
                    st.markdown(f"<div class='question-card'><span class='badge'>Ítem {q['id']}</span><p style='margin-top:8px;'>{q['text']}</p></div>", unsafe_allow_html=True)
                    
                    default_idx = None
                    if str(q["id"]) in st.session_state.respuestas:
                        prev = st.session_state.respuestas[str(q["id"])]
                        opciones_disponibles = list(q["options"].keys())
                        if prev in opciones_disponibles:
                            default_idx = opciones_disponibles.index(prev)
                        
                    opcion = st.radio(
                        "Opciones:", 
                        options=list(q["options"].keys()), 
                        format_func=lambda x: f"{x.upper()}) {q['options'][x]}",
                        key=f"prod_q_{q['id']}",
                        index=default_idx,
                        label_visibility="collapsed"
                    )
                    respuestas_pagina[str(q["id"])] = opcion
                    
                c1, c2 = st.columns(2)
                with c1:
                    if st.session_state.pagina_actual > 0:
                        if st.form_submit_button("⬅️ Atrás"):
                            st.session_state.respuestas.update(
                                {k: v for k, v in respuestas_pagina.items() if v is not None}
                            )
                            st.session_state.pagina_actual -= 1
                            st.rerun()
                with c2:
                    if st.session_state.pagina_actual < total_paginas - 1:
                        if st.form_submit_button("Siguiente ➡️"):
                            if any(v is None for v in respuestas_pagina.values()):
                                st.warning("⚠️ Por favor responda todas las preguntas de esta página antes de continuar.")
                            else:
                                st.session_state.respuestas.update(respuestas_pagina)
                                st.session_state.pagina_actual += 1
                                st.rerun()
                    else:
                        if st.form_submit_button("🔒 Enviar Evaluación"):
                            if any(v is None for v in respuestas_pagina.values()):
                                st.warning("⚠️ Por favor responda todas las preguntas de esta página antes de enviar.")
                            else:
                                st.session_state.respuestas.update(respuestas_pagina)
                                # Se guardan el nombre, respuestas, edad y empresa ingresados
                                guardar_test_en_disco(nombre_paciente, st.session_state.respuestas, edad=edad_paciente, empresa=empresa_paciente)
                                st.session_state.test_enviado = True
                                st.rerun()
                            
    else:
        st.balloons()
        st.markdown("""
            <div style='background-color: #1e293b; padding: 35px; border-radius: 12px; text-align: center; margin-top: 20px; border-top: 5px solid #10b981;'>
                <h2 style='color: #10b981;'>✅ Evaluación Finalizada</h2>
                <p style='font-size: 16px; margin-top:15px; color:#f3f4f6;'>Tus respuestas han sido procesadas de forma segura.</p>
                <p style='font-size: 14px; color:#9ca3af;'>Agradecemos tu sinceridad. Atentamente Lic. Miriam Araujo.</p>
            </div>
        """, unsafe_allow_html=True)

elif modo_app == "👨‍⚕️ Panel Especialista":
    st.markdown("<h1 style='text-align:center;'>Consola del Especialista Clínico</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    password = st.text_input("Por seguridad, introduzca su contraseña de especialista:", type="password")
    password_correcta = obtener_password_especialista()
    
    if password == password_correcta:
        st.success("🔓 Acceso Clínico Autorizado")
        historial = cargar_historial_clinico()
        
        if not historial:
            st.info("Aún no hay registros de respuestas de pacientes guardados.")
        else:
            st.caption(f"📁 {len(historial)} evaluación(es) registrada(s) en total.")
            
            # Más recientes primero
            historial_ordenado = sorted(historial, key=lambda p: p["fecha"], reverse=True)
            
            busqueda = st.text_input("🔎 Buscar paciente por nombre:", "", placeholder="Ej: Miriam")
            if busqueda.strip():
                historial_filtrado = [
                    p for p in historial_ordenado
                    if busqueda.strip().lower() in p["nombre"].lower()
                ]
            else:
                historial_filtrado = historial_ordenado
            
            if not historial_filtrado:
                st.warning(f"No se encontraron pacientes que coincidan con '{busqueda}'.")
                st.stop()
            
            nombres_pacientes = [f"{p['nombre']} ({p['fecha']})" for p in historial_filtrado]
            seleccion = st.selectbox(
                f"Seleccione el expediente del paciente ({len(historial_filtrado)} encontrado(s)):",
                nombres_pacientes
            )
            
            idx_seleccionado = nombres_pacientes.index(seleccion)
            paciente_data = historial_filtrado[idx_seleccionado]
            
            st.markdown("---")
            st.header(f"📊 Expediente: {paciente_data['nombre']}")
            
            # Mostrar metadatos adicionales si existen en el registro
            if "edad" in paciente_data or "empresa" in paciente_data:
                meta_edad = paciente_data.get("edad", "N/A")
                meta_empresa = paciente_data.get("empresa", "N/A")
                st.markdown(f"**Edad:** {meta_edad} años | **Organización / Empresa:** {meta_empresa}")
            
            # Cálculo de puntajes primarios
            brutos = calcular_puntajes_brutos(paciente_data["respuestas"], PF16_QUESTIONS)
            decatipos = convertir_a_decatipos(brutos)
            
            datos_tabla = []
            for factor, sten in decatipos.items():
                interp = generar_descripcion_factor(factor, sten)
                datos_tabla.append({
                    "Factor Psicológico": factor,
                    "Puntuación Bruta": brutos[factor],
                    "Decatipo (Sten)": sten,
                    "Diagnóstico Clínico": interp
                })
            df_tabla = pd.DataFrame(datos_tabla)
            
            # ZONA DE EXPORTACIÓN EXCLUSIVA (EXCEL Y TXT)
            st.subheader("💾 Exportar Resultados del Instrumento")
            exp_col1, exp_col2 = st.columns(2)
            
            with exp_col1:
                excel_data = generar_excel_descargable(paciente_data["nombre"], df_tabla, paciente_data["respuestas"], PF16_QUESTIONS)
                st.download_button(
                    label="📥 Exportar Informe Completo a Excel (.xlsx)",
                    data=excel_data,
                    file_name=f"16PF_{paciente_data['nombre'].replace(' ', '_')}_{paciente_data['fecha'][:10]}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
            with exp_col2:
                txt_data = generar_txt_descargable(paciente_data["nombre"], paciente_data["fecha"], paciente_data["respuestas"], PF16_QUESTIONS)
                st.download_button(
                    label="📄 Exportar Solo Respuestas (.txt)",
                    data=txt_data,
                    file_name=f"Respuestas_16PF_{paciente_data['nombre'].replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            st.markdown("---")
            
            tab1, tab2, tab3 = st.tabs(["📊 Gráficos y Escalas", "👁️ Respuestas del Paciente", "📝 Informe Final"])
            
            with tab1:
                st.subheader("📋 Matriz Analítica de Factores")
                st.dataframe(df_tabla, use_container_width=True, hide_index=True)
                
                st.subheader("📈 Gráfico de Perfil Continuo (Cattell)")
                df_grafico = df_tabla.set_index("Factor Psicológico")["Decatipo (Sten)"]
                st.line_chart(df_grafico)
            
            with tab2:
                st.subheader("📊 Resumen Métrico de Reactivos")
                
                # Cálculo analítico de frecuencias de respuestas
                lista_respuestas = list(paciente_data["respuestas"].values())
                cant_a = lista_respuestas.count("a")
                cant_b = lista_respuestas.count("b")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"<div class='counter-box'><p style='color:#10b981; font-weight:bold; margin-bottom:2px;'>Total Sí (A)</p><div class='counter-num'>{cant_a}</div></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div class='counter-box'><p style='color:#f59e0b; font-weight:bold; margin-bottom:2px;'>Total No (B)</p><div class='counter-num'>{cant_b}</div></div>", unsafe_allow_html=True)
                
                st.markdown("---")
                st.subheader("👁️ Auditoría de Respuestas Ítem por Ítem")
                st.caption("Marcas guardadas con la letra de respuesta ampliada para fácil lectura:")
                
                for q in PF16_QUESTIONS:
                    id_str = str(q["id"])
                    if id_str in paciente_data["respuestas"]:
                        resp_letra = paciente_data["respuestas"][id_str]
                        resp_texto = q["options"].get(resp_letra, "")
                        
                        st.markdown(f"""
                        <div class="audit-block">
                            <div class="audit-title">Ítem {q['id']}: {q['text']}</div>
                            <div style="margin-top: 6px; display: flex; align-items: center;">
                                <span class="audit-choice-highlight">{resp_letra.upper()}</span>
                                <span class="audit-text-desc">{resp_texto}</span>
                                <span class="factor-tag">(Factor: {q['factor']})</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            with tab3:
                st.subheader("📝 Conclusión Integral Desglosada")
                resumen_clinico = generar_informe_global(decatipos)
                st.markdown(resumen_clinico)
                
                st.markdown("### 🧩 Análisis Factorial Desglosado")
                for r in datos_tabla:
                    with st.expander(f"Análisis Factor {r['Factor Psicológico']} (Decatipo: {r['Decatipo (Sten)']})"):
                        st.write(f"**Puntos Directos:** {r['Puntuación Bruta']}")
                        st.write(f"**Interpretación:** {r['Diagnóstico Clínico']}")
                        
    elif password != "":
        st.error("❌ Contraseña incorrecta. Acceso denegado.")