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

def guardar_test_en_disco(nombre, respuestas):
    registro = {
        "nombre": nombre,
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
        st.title("🧠 Evaluación de Personalidad")
        st.caption("Por favor, responda de forma sincera.")
        st.markdown("---")
        
        nombre_paciente = st.text_input("Introduzca su Nombre y Apellido completo:")
        
        if not nombre_paciente:
            st.warning("⚠️ Se requiere ingresar su nombre para inicializar el instrumento.")
        else:
            total_preguntas = len(PF16_QUESTIONS)
            PREGUNTAS_POR_PAGINA = 5
            total_paginas = (total_preguntas // PREGUNTAS_POR_PAGINA) + (1 if total_preguntas % PREGUNTAS_POR_PAGINA > 0 else 0)
            
            progreso = len(st.session_state.respuestas) / total_preguntas
            st.progress(progreso)
            
            inicio = st.session_state.pagina_actual * PREGUNTAS_POR_PAGINA
            fin = min(inicio + PREGUNTAS_POR_PAGINA, total_preguntas)
            bloque_preguntas = PF16_QUESTIONS[inicio:fin]
            
            with st.form(key=f"form_paciente_{st.session_state.pagina_actual}"):
                for q in bloque_preguntas:
                    st.markdown(f"<div class='question-card'><span class='badge'>Ítem {q['id']}</span><p style='margin-top:8px;'>{q['text']}</p></div>", unsafe_allow_html=True)
                    
                    default_idx = 0
                    if str(q["id"]) in st.session_state.respuestas:
                        prev = st.session_state.respuestas[str(q["id"])]
                        default_idx = list(q["options"].keys()).index(prev)
                        
                    opcion = st.radio(
                        "Opciones:", 
                        options=list(q["options"].keys()), 
                        format_func=lambda x: f"{x.upper()}) {q['options'][x]}",
                        key=f"prod_q_{q['id']}",
                        index=default_idx,
                        label_visibility="collapsed"
                    )
                    st.session_state.respuestas[str(q["id"])] = opcion
                    
                c1, c2 = st.columns(2)
                with c1:
                    if st.session_state.pagina_actual > 0:
                        if st.form_submit_button("⬅️ Atrás"):
                            st.session_state.pagina_actual -= 1
                            st.rerun()
                with c2:
                    if st.session_state.pagina_actual < total_paginas - 1:
                        if st.form_submit_button("Siguiente ➡️"):
                            st.session_state.pagina_actual += 1
                            st.rerun()
                    else:
                        if st.form_submit_button("🔒 Enviar Evaluación"):
                            guardar_test_en_disco(nombre_paciente, st.session_state.respuestas)
                            st.session_state.test_enviado = True
                            st.rerun()
                            
    else:
        st.balloons()
        st.markdown("""
            <div style='background-color: #1e293b; padding: 35px; border-radius: 12px; text-align: center; margin-top: 20px; border-top: 5px solid #10b981;'>
                <h2 style='color: #10b981;'>✅ Evaluación Finalizada</h2>
                <p style='font-size: 16px; margin-top:15px; color:#f3f4f6;'>Tus respuestas han sido procesadas de forma segura.</p>
                <p style='font-size: 14px; color:#9ca3af;'>Ya puedes cerrar el navegador de tu teléfono.</p>
            </div>
        """, unsafe_allow_html=True)

elif modo_app == "👨‍⚕️ Panel Especialista":
    st.title("👨‍⚕️ Consola del Especialista Clínico")
    st.markdown("---")
    
    password = st.text_input("Por seguridad, introduzca su contraseña de especialista:", type="password")
    
    if password == "Miriam16PF":
        st.success("🔓 Acceso Clínico Autorizado")
        historial = cargar_historial_clinico()
        
        if not historial:
            st.info("Aún no hay registros de respuestas de pacientes guardados.")
        else:
            nombres_pacientes = [f"{p['nombre']} ({p['fecha']})" for p in historial]
            seleccion = st.selectbox("Seleccione el expediente del paciente:", nombres_pacientes)
            
            idx_seleccionado = nombres_pacientes.index(seleccion)
            paciente_data = historial[idx_seleccionado]
            
            st.markdown("---")
            st.header(f"📊 Expediente: {paciente_data['nombre']}")
            
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
                cant_c = lista_respuestas.count("c")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"<div class='counter-box'><p style='color:#10b981; font-weight:bold; margin-bottom:2px;'>Total Opción A</p><div class='counter-num'>{cant_a}</div></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div class='counter-box'><p style='color:#f59e0b; font-weight:bold; margin-bottom:2px;'>Total Opción B</p><div class='counter-num'>{cant_b}</div></div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div class='counter-box'><p style='color:#ef4444; font-weight:bold; margin-bottom:2px;'>Total Opción C</p><div class='counter-num'>{cant_c}</div></div>", unsafe_allow_html=True)
                
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