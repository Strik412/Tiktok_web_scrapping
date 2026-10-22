import os
import pandas as pd
from google import genai
from pathlib import Path
from dotenv import load_dotenv

# 1. Cargar las variables de entorno de forma segura (evita bloqueos en GitHub)
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("[ERROR] No se encontró la clave. Asegúrate de tener un archivo .env con GEMINI_API_KEY=tu_clave")
    exit()

# Inicializar el cliente con la nueva librería
client = genai.Client(api_key=API_KEY)

def main():
    username = "_rl9"
    
    # 2. Resolver la ruta dinámicamente desde 'analisis' hacia 'resultados'
    ruta_base = Path(__file__).parent.parent
    ruta_csv = ruta_base / "resultados" / username / "ultimos_posts.csv"
    
    try:
        df = pd.read_csv(ruta_csv)
    except FileNotFoundError:
        print(f"[ERROR] Archivo no encontrado en: {ruta_csv}")
        return

    # Extraer y unir los textos, eliminando valores nulos
    descripciones = df['descripcion'].dropna().tolist()
    texto_completo = "\n- ".join(descripciones)

    if not texto_completo.strip():
        print("[!] No hay descripciones de texto para analizar.")
        return

    # 3. Prompt Avanzado: Fenotipado + Lógica de Negocio
    prompt = f"""
    Actúa como un analista de datos y estratega de marketing digital especializado en fenotipado.
    A continuación te proporciono descripciones extraídas del TikTok de @{username}:
    
    - {texto_completo}
    
    Realiza un perfilado psicolingüístico "Big Five" (OCEAN) e intégralo con lógica de negocio corporativa. 
    
    Devuelve la respuesta estructurada ESTRICTAMENTE con este formato:
    
    1. PERFIL BIG FIVE (Distribución 100%):
    - Evalúa el perfil y reparte EXACTAMENTE el 100% entre los 5 rasgos (Apertura, Responsabilidad, Extraversión, Amabilidad, Neuroticismo) según su predominancia. La suma total de los 5 valores debe ser 100%.
    - Añade una justificación muy breve (1 línea) por cada rasgo citando el texto.
    
    2. LÓGICA DE NEGOCIO Y ESTRATEGIA COMERCIAL:
    - Afinidad de Marca (Brand Match): ¿Qué tipo de industrias o marcas (ej. deportivas, lujo, ONGs, tecnología) tendrían el mayor Retorno de Inversión (ROI) al patrocinar a este creador y por qué?
    - Riesgo de Marca (Brand Safety): Basado en su nivel de Neuroticismo y Amabilidad, ¿existe algún riesgo reputacional para una marca al asociarse con este perfil?
    - Oportunidad de Monetización: ¿Qué tipo de producto digital, mercancía o formato de campaña funcionaría mejor para monetizar a esta audiencia específica?
    """

    print("[*] Conectando con Gemini y evaluando el perfil y estrategia comercial...")
    
    try:
        # 4. Llamada con el modelo actualizado
        respuesta = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt
        )
        
        # Imprimir en consola
        print("\n" + "="*70)
        print(f"ANÁLISIS BIG FIVE & BUSINESS STRATEGY: @{username}")
        print("="*70)
        print(respuesta.text)
        
        # Guardar en archivo de texto
        ruta_reporte = ruta_base / "resultados" / username / "reporte_big_five.txt"
        ruta_reporte.write_text(respuesta.text, encoding="utf-8")
        print("\n" + "="*70)
        print(f"[*] ¡Éxito! Reporte analítico y corporativo guardado en: {ruta_reporte}")
        
    except Exception as e:
        print(f"\n[ERROR] Ocurrió un problema al comunicarse con Gemini: {e}")

if __name__ == "__main__":
    main()
