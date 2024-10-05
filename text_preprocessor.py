import nltk
import logging
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

def download_nltk_data():
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        logger.info("NLTK data downloaded successfully")
    except Exception as e:
        logger.error(f"Error downloading NLTK data: {e}")
        logger.warning("Using fallback tokenization and stopwords removal.")

download_nltk_data()

# Add fallback tokenization and stopwords
def fallback_tokenize(text):
    logger.info("Using fallback tokenization method")
    return text.lower().split()

fallback_stopwords = set(['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"])

def preprocess_text(text, progress_callback=None):
    try:
        logger.info("Starting text preprocessing")
        
        # Tokenize the text
        logger.info("Tokenizing text")
        tokens = word_tokenize(text.lower())
        logger.info(f"Text tokenized successfully: {len(tokens)} tokens")
        
        # Remove stopwords in batches
        logger.info("Removing stopwords")
        stop_words = set(stopwords.words('english'))
        filtered_tokens = []
        batch_size = 10000  # Adjust this based on memory constraints
        total_batches = (len(tokens) + batch_size - 1) // batch_size
        
        for i in range(0, len(tokens), batch_size):
            batch = tokens[i:i+batch_size]
            filtered_batch = [token for token in batch if token not in stop_words]
            filtered_tokens.extend(filtered_batch)
            
            if progress_callback:
                progress = ((i + batch_size) / len(tokens)) * 100
                progress_callback(min(progress, 100))
            
            logger.info(f"Processed batch {(i // batch_size) + 1}/{total_batches}")
        
        logger.info(f"Stopwords removed: {len(tokens) - len(filtered_tokens)} stopwords")
        
        # Join the tokens back into a string
        logger.info("Joining tokens back into a string")
        preprocessed_text = ' '.join(filtered_tokens)
        
        logger.info(f"Preprocessing complete: {len(preprocessed_text)} characters in preprocessed text")
        return preprocessed_text
    except Exception as e:
        logger.error(f"Error during text preprocessing: {e}")
        logger.warning("Using fallback preprocessing method.")
        
        # Check for specific NLTK resource issues
        if "Resource punkt not found" in str(e):
            logger.error("NLTK 'punkt' resource is missing. Please download it using nltk.download('punkt')")
        if "Resource stopwords not found" in str(e):
            logger.error("NLTK 'stopwords' resource is missing. Please download it using nltk.download('stopwords')")
        
        # Fallback tokenization and stopwords removal
        logger.info("Starting fallback preprocessing")
        tokens = fallback_tokenize(text)
        logger.info(f"Fallback tokenization complete: {len(tokens)} tokens")
        filtered_tokens = [token for token in tokens if token not in fallback_stopwords]
        logger.info(f"Fallback stopwords removed: {len(tokens) - len(filtered_tokens)} stopwords")
        return ' '.join(filtered_tokens)
