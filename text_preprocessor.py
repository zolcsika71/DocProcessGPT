import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

def download_nltk_data():
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
    except Exception as e:
        print(f"Error downloading NLTK data: {e}")

download_nltk_data()

def preprocess_text(text):
    try:
        # Tokenize the text
        tokens = word_tokenize(text.lower())
        
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        filtered_tokens = [token for token in tokens if token not in stop_words]
        
        # Join the tokens back into a string
        preprocessed_text = ' '.join(filtered_tokens)
        
        return preprocessed_text
    except Exception as e:
        print(f"Error during text preprocessing: {e}")
        return text  # Return original text if preprocessing fails
