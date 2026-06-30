# scoring.py

def calcular_puntajes_brutos(respuestas, banco_preguntas):
    """Calcula la suma de puntos directos por factor corrigiendo el tipo de dato del ID."""
    puntajes_brutos = {f: 0 for f in ["A", "B", "C", "E", "F", "G", "H", "I", "L", "M", "N", "O", "Q1", "Q2", "Q3", "Q4"]}
    
    for q_id, opcion_elegida in respuestas.items():
        pregunta = next((q for q in banco_preguntas if q["id"] == int(q_id)), None)
        if not pregunta or pregunta["factor"] not in puntajes_brutos:
            continue
            
        factor = pregunta["factor"]
        
        if factor == "A":
            if int(q_id) == 2 and opcion_elegida == "c": puntajes_brutos[factor] += 2
            elif opcion_elegida == "b": puntajes_brutos[factor] += 1
        elif factor == "B":
            if int(q_id) == 3 and opcion_elegida == "a": puntajes_brutos[factor] += 1
        else:
            if opcion_elegida == "a": puntajes_brutos[factor] += 2
            elif opcion_elegida == "b": puntajes_brutos[factor] += 1
            
    return puntajes_brutos

def convertir_a_decatipos(puntajes_brutos):
    """Mapea los puntajes brutos a decatipos normativos (Stens del 1 al 10)."""
    decatipos = {}
    for factor, bruto in puntajes_brutos.items():
        if bruto <= 2: decatipos[factor] = 1
        elif bruto <= 4: decatipos[factor] = 2
        elif bruto <= 6: decatipos[factor] = 3
        elif bruto <= 8: decatipos[factor] = 4
        elif bruto <= 10: decatipos[factor] = 5
        elif bruto <= 12: decatipos[factor] = 6
        elif bruto <= 14: decatipos[factor] = 7
        elif bruto <= 16: decatipos[factor] = 8
        elif bruto <= 18: decatipos[factor] = 9
        else: decatipos[factor] = 10
    return decatipos

def generar_descripcion_factor(factor, decatipo):
    descripciones = {
        "A": {"bajo": "Reservado, alejado, crítico y formal.", "alto": "Abierto, afectuoso, sociable y participativo."},
        "B": {"bajo": "Pensamiento concreto, baja capacidad mental operativa.", "alto": "Pensamiento abstracto, inteligente, brillante."},
        "C": {"bajo": "Afectado por los sentimientos, inestable emocionalmente.", "alto": "Emocionalmente estable, maduro, afronta la realidad."},
        "E": {"bajo": "Sumiso, dócil, acomodaticio, humilde.", "alto": "Dominante, asertivo, competitivo, agresivo."},
        "F": {"bajo": "Sobrio, prudente, serio, taciturno.", "alto": "Entusiasta, descuidado, alegre, expresivo."},
        "G": {"bajo": "Despreocupado por las normas, informal.", "alto": "Escrupuloso, responsable, moralista, concienzudo."},
        "H": {"bajo": "Tímido, retraído, cohibido, sensible.", "alto": "Atrevido, aventurero, inmune a la amenaza."},
        "I": {"bajo": "Sensibilidad dura, racional, práctico, realista.", "alto": "Sensibilidad blanda, tierno, imaginativo, idealista."},
        "L": {"bajo": "Confiable, adaptable, libre de celos.", "alto": "Suspicaz, propenso a los celos, desconfiado."},
        "M": {"bajo": "Práctico, cuidadoso, regulado por la realidad.", "alto": "Imaginativo, bohemio, absorto en sus ideas."},
        "N": {"bajo": "Ingenuo, directo, genuino, natural.", "alto": "Astuto, calculador, refinado, socialmente consciente."},
        "O": {"bajo": "Seguro de sí mismo, apacible, sereno.", "alto": "Aprehensivo, insecure, preocupado, culpable."},
        "Q1": {"bajo": "Conservador, respetuoso de las ideas tradicionales.", "alto": "Radical, experimental, liberal, analítico."},
        "Q2": {"bajo": "Dependiente del grupo, seguidor, imitador.", "alto": "Autosuficiente, prefiere sus propias decisiones."},
        "Q3": {"bajo": "Autoconcepto bajo, descuidado con los protocolos.", "alto": "Controlado, perfeccionista, fuerza de voluntad."},
        "Q4": {"bajo": "Tranquilo, relajado, sereno, baja activación.", "alto": "Tenso, frustrado, presionado, sobreexcitado."}
    }
    if decatipo <= 3:
        return f"Puntuación Baja: {descripciones[factor]['bajo']}"
    elif decatipo >= 8:
        return f"Puntuación Alta: {descripciones[factor]['alto']}"
    else:
        return "Término Medio: Equilibrio adaptativo y normativo del rasgo."

def generar_informe_global(decatipos):
    ansiedad = (decatipos["O"] + decatipos["Q4"] - decatipos["C"] - decatipos["Q3"]) / 2
    extroversion = (decatipos["A"] + decatipos["F"] + decatipos["H"] - decatipos["Q2"]) / 2
    
    informe = "### 📌 Conclusión General del Diagnóstico Clínico Extendido\n"
    informe += "A partir de la integración multifactorial de las escalas primarias y secundarias evaluadas mediante el instrumento psicométrico de Cattell, se determina el siguiente panorama clínico descriptivo del paciente:\n\n"
    
    # 1. Dimensión Socio-Interpersonal
    informe += "#### 👥 1. Dimensión Socio-Interpersonal y Estilo Relacional\n"
    if extroversion >= 7.5:
        informe += "El examinado denota un perfil marcadamente extrovertido y con una alta disposición hacia el contacto interpersonal. Muestra una marcada facilidad para establecer vínculos afectivos recíprocos, tendencia a la participación en dinámicas grupales y un estilo de comunicación abierto y asertivo. Su energía se orienta al entorno social, asumiendo riesgos vinculares con naturalidad y comodidad adaptativa.\n\n"
    elif extroversion <= 3.5:
        informe += "El examinado exhibe una marcada orientación hacia la introversión psicológica. Su estilo relacional tiende de manera consistente hacia la reserva, la distancia formal y la selectividad en sus interacciones sociales. Prefieres dinámicas de trabajo e introspección individuales, donde se priorice la autonomía ejecutiva antes que la constante deliberación grupal, encontrando mayor estabilidad en ambientes controlados o predecibles.\n\n"
    else:
        informe += "El paciente se ubica en una zona de ambiversión normativa. Presenta un equilibrio adaptativo saludable que le permite alternar de forma flexible entre periodos de interacción sociolaboral activa y momentos de distanciamiento analítico o reserva personal, ajustándose adecuadamente a las demandas contextuales de su entorno sin desgastar sus recursos ejecutivos.\n\n"
        
    # 2. Ajuste Emocional y Estabilidad
    informe += "#### ⚖️ 2. Estabilidad Emocional y Gestión del Estrés\n"
    if ansiedad >= 7.5:
        informe += "Se evidencian índices clínicos significativos de tensión interna, reactividad afectiva y vulnerabilidad actual ante estresores ambientales. El perfil sugiere una tendencia correlativa a experimentar preocupación, aprehensión anticipatoria o labilidad emocional frente a demandas imprevistas. Sus mecanismos homeostáticos instituidos podrían encontrarse saturados, requiriendo un abordaje focalizado en el desarrollo de estrategias de afrontamiento y regulación del self.\n\n"
    elif decatipos["C"] >= 8:
        informe += "El perfil destaca por poseer un excelente ajuste emocional basal. El evaluado muestra una elevada tolerancia a la frustración, fortaleza yoica (capacidad del Yo para integrar la realidad) y resiliencia ante contingencias severas. Es capaz de mantener la ecuanimidad y un pensamiento lógico-analítico operativo incluso bajo condiciones de presión ambiental significativa.\n\n"
    else:
        informe += "El ajuste emocional y el manejo del estrés se sitúan dentro de los parámetros esperados de la norma estadística. Manifiesta un control de impulsos adecuado y una estabilidad general regular, experimentando variaciones anímicas predecibles que no llegan a comprometer de forma orgánica sus esferas de rendimiento laboral o familiar.\n\n"

    # 3. Estilo Cognitivo y Estructura Organizacional
    informe += "#### 🧠 3. Estilo Cognitivo y Apego a la Normativa\n"
    if decatipos["G"] >= 7 or decatipos["Q3"] >= 7:
        informe += "En lo referente a la organización interna, se observa un perfil con alta autodisciplina, meticulosidad y un fuerte sentido del deber (Superyó fuerte). Tiende a estructurar sus tareas de forma escrupulosa, mostrando un riguroso respeto hacia los protocolos establecidos, los marcos normativos e institucionales, y una alta autoexigencia orientada a la calidad y la precisión conductual.\n"
    elif decatipos["G"] <= 4 or decatipos["Q3"] <= 4:
        informe += "Muestra un enfoque cognitivo flexible, adaptable y espontáneo, con una tendencia a priorizar soluciones inmediatas sobre planificaciones exhaustivas a largo plazo. Su nivel de apego a las estructuras formales es bajo, prefiriendo la flexibilidad metodológica y un marco operativo que no restrinja su autonomía de acción o su pensamiento alternativo.\n"
    else:
        informe += "Su estilo de procesamiento cognitivo y nivel de organización se encuentran equilibrados. Capaz de seguir planes de acción estructurados sin perder la flexibilidad necesaria para improvisar o realizar ajustes intermedios cuando la situación real lo amerita.\n"
        
    return informe