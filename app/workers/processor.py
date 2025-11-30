"""
Text processor worker for extracting and tokenizing web page content.
This would typically run as a separate service consuming from a processing queue.
"""
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup


class TextProcessor:
    """Processes raw HTML content into clean, tokenized text."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters (keep alphanumeric and basic punctuation)
        text = re.sub(r'[^\w\s\-.,!?]', '', text)
        
        # Lowercase
        text = text.lower().strip()
        
        return text
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Tokenize text into individual words.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        # Simple word tokenization (split on whitespace and punctuation)
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        # Remove very short tokens (< 2 characters)
        tokens = [t for t in tokens if len(t) >= 2]
        
        # Remove stop words (common words with little meaning)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
            'for', 'of', 'as', 'by', 'is', 'was', 'are', 'were', 'be', 
            'been', 'has', 'have', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'it', 'its', 'this', 'that'
        }
        
        tokens = [t for t in tokens if t not in stop_words]
        
        return tokens
    
    def process_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a crawled page into clean, tokenized content.
        
        Args:
            page_data: Raw page data from crawler
            
        Returns:
            Processed data ready for indexing
        """
        # Clean the content
        clean_content = self.clean_text(page_data['content'])
        
        # Tokenize
        tokens = self.tokenize(clean_content)
        
        # Extract metadata
        processed_data = {
            'url': page_data['url'],
            'title': page_data['title'],
            'content': clean_content,
            'tokens': tokens,
            'domain': page_data['domain'],
            'crawl_date': page_data['crawl_date'],
            'token_count': len(tokens),
            'content_hash': hash(clean_content)  # Simple hash for deduplication
        }
        
        return processed_data
    
    def extract_keywords(self, tokens: List[str], top_n: int = 20) -> List[str]:
        """
        Extract top keywords from tokens.
        
        Args:
            tokens: List of tokens
            top_n: Number of top keywords to return
            
        Returns:
            List of top keywords
        """
        from collections import Counter
        
        # Count token frequencies
        token_counts = Counter(tokens)
        
        # Get top N most common
        top_keywords = [word for word, count in token_counts.most_common(top_n)]
        
        return top_keywords


# Example usage in a worker context
def process_crawl_result(crawl_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a crawl result.
    This function would be called by the crawler worker or a separate processor worker.
    
    Args:
        crawl_result: Result from crawler
        
    Returns:
        Processed data ready for indexing
    """
    processor = TextProcessor()
    
    if crawl_result.get('page_data', {}).get('success'):
        page_data = crawl_result['page_data']
        processed_data = processor.process_page(page_data)
        
        # Add keywords
        processed_data['keywords'] = processor.extract_keywords(
            processed_data['tokens']
        )
        
        return {
            'job_id': crawl_result['job_id'],
            'processed_data': processed_data,
            'ready_for_indexing': True
        }
    
    return {
        'job_id': crawl_result['job_id'],
        'ready_for_indexing': False,
        'error': 'Crawl failed'
    }


if __name__ == "__main__":
    # Example test
    sample_page = {
        'url': 'https://example.com/test',
        'title': 'Test Page',
        'content': '''
            This is a test page about Python programming.
            Python is a popular programming language.
            It is used for web development and data science.
        ''',
        'domain': 'example.com',
        'crawl_date': '2024-11-29T12:00:00'
    }
    
    processor = TextProcessor()
    result = processor.process_page(sample_page)
    
    print("Processed Result:")
    print(f"Tokens: {result['tokens']}")
    print(f"Token count: {result['token_count']}")
    print(f"Keywords: {processor.extract_keywords(result['tokens'])}")