import pandas as pd
from google import genai
from pathlib import Path

# Configura tu clave de API aquí
API_KEY = "AQ.Ab8RN6J37TVIsbGkEf3teZcPmD4w1tQntClS34uBcI2Kz6446A"
client = genai.Client(api_key=API_KEY)

def main():
    username = "_rl9"
    
    # Resolver la ruta dinámicamente desde 'analisis' hacia 'resultados'
    ruta_base = Path(__file__).parent.parent
    ruta_csv = ruta_base / "resultados" / username / "ultimos_posts.csv"
    
    try:
        df = pd.read_csv(ruta_csv)
    except FileNotFoundError:
        print(f"[ERROR] Archivo no encontrado en: {ruta_csv}")
        return

    # Extraer y unir los textos
    descripciones = df['descripcion'].dropna().tolist()
    texto_completo = "\n- ".join(descripciones)

    if not texto_completo.strip():
        print("[!] No hay descripciones de texto para analizar.")
        return

    # Diseñar el Prompt
    prompt = f"""
    Actúa como un analista de datos especializado en psicología lingüística y fenotipado digital.
    A continuación te proporciono una lista de descripciones extraídas de la cuenta de TikTok de @{username}:
    
    - {texto_completo}
    
    Con base en el tono, las palabras utilizadas, los temas y los emojis de estas publicaciones, 
    realiza una aproximación al perfil de personalidad "Big Five" (OCEAN) de este creador de contenido. 
    
    Devuelve la respuesta estructurada con:
    1. Una puntuación estimada (Alta, Media, Baja) para cada uno de los 5 rasgos (Apertura, Responsabilidad, Extraversión, Amabilidad, Neuroticismo).
    2. Una breve justificación para cada rasgo citando ejemplos exactos del texto.
    3. Una conclusión general sobre la imagen de marca que proyecta.
    """

    print("[*] Conectando con Gemini y analizando la huella digital...")
    
    # Llamada con el nuevo SDK de Google
    respuesta = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt
    )
    
    # Imprimir en consola
    print("\n" + "="*50)
    print(f"ANÁLISIS BIG FIVE: @{username}")
    print("="*50)
    print(respuesta.text)
    
    # Guardar en archivo de texto
    ruta_reporte = ruta_base / "resultados" / username / "reporte_big_five.txt"
    ruta_reporte.write_text(respuesta.text, encoding="utf-8")
    print("\n" + "="*50)
    print(f"[*] ¡Éxito! Reporte analítico guardado en: {ruta_reporte}")

if __name__ == "__main__":
    main()