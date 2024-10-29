import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from nltk.stem import WordNetLemmatizer


nltk.download('omw-1.4',download_dir='.')
nltk.download('wordnet',download_dir='.')
nltk.download('punkt', download_dir='.')
nltk.download('punkt_tab', download_dir='.')
nltk.data.path.append('.')

# lowercase
# Remove non-sense(digits, url, ..)
# Stripping
# Punctuation
# Remove Stopword
# Steeming/Lemmatization

steemer = PorterStemmer()
lemmatizater = WordNetLemmatizer()
def stem(x):
    L = []
    for i in x.split():
        L.append(steemer.stem(i))

    return ' '.join(L)

def text_preprocessing(x):
    x = x.lower()
    x = re.compile(r'https?://\S+').sub('', x)
    x = re.sub(r'[^\w\s]', '', x)
    x = re.sub(r'\d', '', x)
    tokens = word_tokenize(x)
    tokens = [steemer.stem(i) for i in tokens]
    tokens = [lemmatizater.lemmatize(i) for i in tokens]

    return ' '.join(tokens)