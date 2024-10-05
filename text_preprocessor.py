import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Download necessary NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

def preprocess_text(text):
    """
    Preprocess the input text by tokenizing and removing stopwords.
    
    :param text: Input text as a string
    :return: Preprocessed text as a string
    """
    # Tokenize the text
    tokens = word_tokenize(text.lower())
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [token for token in tokens if token not in stop_words]
    
    # Join the tokens back into a string
    preprocessed_text = ' '.join(filtered_tokens)
    
    return preprocessed_text
