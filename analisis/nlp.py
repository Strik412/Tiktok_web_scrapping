import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
from sentence_transformers import SentenceTransformer
import nltk
from nltk.corpus import stopwords
from pathlib import Path

# Descargar stopwords si no existen
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

def limpiar_texto(texto):
    """Limpia el texto eliminando URLs, menciones y caracteres especiales."""
    if pd.isna(texto):
        return ""
    texto = str(texto).lower()
    texto = re.sub(r"http\S+|www\S+|https\S+", '', texto, flags=re.MULTILINE) # Quitar URLs
    texto = re.sub(r'\@\w+|\#', '', texto) # Quitar menciones y el símbolo # (dejamos la palabra)
    texto = re.sub(r'[^\w\s]', '', texto) # Quitar puntuación
    return texto

def main():
    # ---------------------------------------------------------
    # PASO 2: DATASET CSV
    # ---------------------------------------------------------
    username = "_rl9"  # Cambia esto si analizaste a otro usuario
    
    # Path(__file__).parent.parent sube desde '/analisis' a la carpeta raíz del proyecto,
    # y desde allí entra a '/resultados/_rl9/ultimos_posts.csv'
    ruta_base = Path(__file__).parent.parent
    ruta_csv = ruta_base / "resultados" / username / "ultimos_posts.csv"
    
    try:
        df = pd.read_csv(ruta_csv)
        print(f"[*] Dataset cargado: {len(df)} publicaciones encontradas.")
    except FileNotFoundError:
        print(f"[ERROR] No se encontró el archivo en: {ruta_csv}")
        print("Asegúrate de haber extraído los datos de este usuario primero.")
        return

    # ---------------------------------------------------------
    # PASO 3: PROCESAMIENTO NLP (Limpieza y TF-IDF)
    # ---------------------------------------------------------
    print("[*] Ejecutando limpieza de texto y TF-IDF...")
    df['texto_limpio'] = df['descripcion'].apply(limpiar_texto)
    
    # Combinar stopwords en inglés y español
    stop_words_multi = stopwords.words('spanish') + stopwords.words('english')
    
    vectorizer = TfidfVectorizer(stop_words=stop_words_multi, max_features=20)
    tfidf_matrix = vectorizer.fit_transform(df['texto_limpio'])
    palabras_top = vectorizer.get_feature_names_out()
    frecuencias = tfidf_matrix.sum(axis=0).A1
    
    df_tfidf = pd.DataFrame({'Palabra': palabras_top, 'Importancia TF-IDF': frecuencias})
    df_tfidf = df_tfidf.sort_values(by='Importancia TF-IDF', ascending=False)

    # ---------------------------------------------------------
    # PASO 4: EMBEDDINGS SEMÁNTICOS
    # ---------------------------------------------------------
    print("[*] Generando Embeddings (esto puede tardar unos segundos la primera vez)...")
    # Usamos un modelo multilingüe ligero y rápido de HuggingFace
    modelo_emb = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    embeddings = modelo_emb.encode(df['texto_limpio'].tolist())

    # ---------------------------------------------------------
    # PASO 5: SIMILITUD SEMÁNTICA (Similitud Coseno)
    # ---------------------------------------------------------
    print("[*] Calculando similitud coseno entre publicaciones...")
    matriz_similitud = cosine_similarity(embeddings)

    # ---------------------------------------------------------
    # PASO 6: VISUALIZACIÓN
    # ---------------------------------------------------------
    print("[*] Generando gráficos...")
    fig = plt.figure(figsize=(18, 12))
    fig.suptitle(f'Análisis Semántico y NLP de @{username}', fontsize=16, fontweight='bold')

    # Gráfico 1: Top Palabras (TF-IDF)
    ax1 = plt.subplot(2, 2, 1)
    sns.barplot(data=df_tfidf.head(10), x='Importancia TF-IDF', y='Palabra', ax=ax1, palette='viridis')
    ax1.set_title('Top 10 Palabras más relevantes (TF-IDF)')

    # Gráfico 2: Matriz de Similitud (Heatmap)
    ax2 = plt.subplot(2, 2, 2)
    sns.heatmap(matriz_similitud, annot=False, cmap='coolwarm', ax=ax2, 
                xticklabels=[f"Post {i+1}" for i in range(len(df))], 
                yticklabels=[f"Post {i+1}" for i in range(len(df))])
    ax2.set_title('Matriz de Similitud Semántica (Coseno)')

    # Gráfico 3: Mapa Semántico 2D (PCA)
    # Reducimos los embeddings de 384 dimensiones a 2 dimensiones para poder graficarlos
    pca = PCA(n_components=2)
    embeddings_2d = pca.fit_transform(embeddings)
    
    ax3 = plt.subplot(2, 1, 2)
    ax3.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], color='blue', s=100, alpha=0.7)
    
    # Añadir etiquetas numéricas a los puntos
    for i in range(len(embeddings_2d)):
        ax3.text(embeddings_2d[i, 0] + 0.02, embeddings_2d[i, 1] + 0.02, f'P{i+1}', fontsize=9)
        
    ax3.set_title('Mapa Semántico 2D (Publicaciones cercanas hablan de temas similares)')
    ax3.set_xlabel('Componente Principal 1')
    ax3.set_ylabel('Componente Principal 2')
    ax3.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    main()