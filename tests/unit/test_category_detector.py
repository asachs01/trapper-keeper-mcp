"""Unit tests for category detector."""

from unittest.mock import Mock, patch
import pytest

from trapper_keeper.extractor.category_detector import CategoryDetector
from trapper_keeper.core.types import ExtractionCategory


class TestCategoryDetector:
    """Test CategoryDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create a category detector."""
        return CategoryDetector()
    
    def test_detect_single_category(self, detector):
        """Test detecting a single category from text."""
        test_cases = [
            # Architecture
            ("System architecture using microservices", ExtractionCategory.ARCHITECTURE),
            ("The architecture follows MVC pattern", ExtractionCategory.ARCHITECTURE),
            ("Service-oriented architecture design", ExtractionCategory.ARCHITECTURE),
            
            # Database
            ("Database schema for users table", ExtractionCategory.DATABASE),
            ("PostgreSQL database configuration", ExtractionCategory.DATABASE),
            ("SQL query optimization tips", ExtractionCategory.DATABASE),
            
            # Security
            ("Security vulnerability in login", ExtractionCategory.SECURITY),
            ("Authentication using JWT tokens", ExtractionCategory.SECURITY),
            ("Implement HTTPS encryption", ExtractionCategory.SECURITY),
            
            # API
            ("REST API endpoint documentation", ExtractionCategory.API),
            ("GraphQL API schema definition", ExtractionCategory.API),
            ("API rate limiting configuration", ExtractionCategory.API),
            
            # Testing
            ("Unit tests for user service", ExtractionCategory.TESTING),
            ("Integration testing strategy", ExtractionCategory.TESTING),
            ("Test coverage report", ExtractionCategory.TESTING),
            
            # Deployment
            ("Deploy to production server", ExtractionCategory.DEPLOYMENT),
            ("CI/CD pipeline configuration", ExtractionCategory.DEPLOYMENT),
            ("Kubernetes deployment manifest", ExtractionCategory.DEPLOYMENT),
            
            # Performance
            ("Performance optimization needed", ExtractionCategory.PERFORMANCE),
            ("Slow query analysis", ExtractionCategory.PERFORMANCE),
            ("Memory usage optimization", ExtractionCategory.PERFORMANCE),
            
            # Monitoring
            ("Monitor system metrics", ExtractionCategory.MONITORING),
            ("Setup alerting rules", ExtractionCategory.MONITORING),
            ("Logging configuration", ExtractionCategory.MONITORING),
        ]
        
        for text, expected_category in test_cases:
            result = detector.detect(text)
            assert result == expected_category, f"Expected {expected_category} for '{text}', got {result}"
    
    def test_detect_multiple_categories(self, detector):
        """Test detecting multiple categories from text."""
        # Text with multiple category indicators
        text = "API security testing for database endpoints"
        
        # Should prioritize based on keyword strength
        result = detector.detect(text)
        assert result in [
            ExtractionCategory.API,
            ExtractionCategory.SECURITY,
            ExtractionCategory.TESTING,
            ExtractionCategory.DATABASE,
        ]
    
    def test_detect_with_title_and_content(self, detector):
        """Test detection using both title and content."""
        # Title suggests one category, content another
        title = "Database Design"
        content = "This section covers security best practices for database access control."
        
        result = detector.detect(content, title)
        # Should consider both, but title often has higher weight
        assert result in [ExtractionCategory.DATABASE, ExtractionCategory.SECURITY]
    
    def test_detect_critical_category(self, detector):
        """Test detecting critical category."""
        critical_texts = [
            "CRITICAL: System failure detected",
            "URGENT: Security breach",
            "Emergency: Database corruption",
            "FATAL ERROR in production",
        ]
        
        for text in critical_texts:
            result = detector.detect(text)
            assert result == ExtractionCategory.CRITICAL
    
    def test_detect_setup_category(self, detector):
        """Test detecting setup/installation category."""
        setup_texts = [
            "Installation guide for developers",
            "Setup instructions",
            "Getting started with the project",
            "Initial configuration steps",
            "Environment setup guide",
        ]
        
        for text in setup_texts:
            result = detector.detect(text)
            assert result == ExtractionCategory.SETUP
    
    def test_detect_features_category(self, detector):
        """Test detecting features category."""
        feature_texts = [
            "New feature: User authentication",
            "Feature request: Dark mode",
            "Implemented feature for export",
            "User story: As a user, I want to...",
        ]
        
        for text in feature_texts:
            result = detector.detect(text)
            assert result == ExtractionCategory.FEATURES
    
    def test_detect_documentation_category(self, detector):
        """Test detecting documentation category."""
        doc_texts = [
            "API documentation updates",
            "README file improvements",
            "Documentation for new features",
            "User manual updates",
        ]
        
        for text in doc_texts:
            result = detector.detect(text)
            assert result == ExtractionCategory.DOCUMENTATION
    
    def test_detect_configuration_category(self, detector):
        """Test detecting configuration category."""
        config_texts = [
            "Configuration file for production",
            "Update config settings",
            "Environment variables setup",
            "Application configuration guide",
        ]
        
        for text in config_texts:
            result = detector.detect(text)
            assert result == ExtractionCategory.CONFIGURATION
    
    def test_detect_dependencies_category(self, detector):
        """Test detecting dependencies category."""
        dep_texts = [
            "Update package dependencies",
            "Third-party library integration",
            "Dependency vulnerability found",
            "Required packages installation",
        ]
        
        for text in dep_texts:
            result = detector.detect(text)
            assert result == ExtractionCategory.DEPENDENCIES
    
    def test_detect_custom_category(self, detector):
        """Test fallback to custom category."""
        # Text with no clear category indicators
        ambiguous_texts = [
            "Random notes about the project",
            "Miscellaneous thoughts",
            "General observations",
            "",  # Empty text
        ]
        
        for text in ambiguous_texts:
            result = detector.detect(text)
            assert result == ExtractionCategory.CUSTOM
    
    def test_case_insensitive_detection(self, detector):
        """Test that detection is case-insensitive."""
        test_cases = [
            ("DATABASE SCHEMA DESIGN", ExtractionCategory.DATABASE),
            ("database schema design", ExtractionCategory.DATABASE),
            ("DaTaBaSe ScHeMa DeSiGn", ExtractionCategory.DATABASE),
        ]
        
        for text, expected in test_cases:
            result = detector.detect(text)
            assert result == expected
    
    def test_detect_with_special_characters(self, detector):
        """Test detection with special characters in text."""
        test_cases = [
            ("API/REST endpoint configuration", ExtractionCategory.API),
            ("Database (PostgreSQL) setup", ExtractionCategory.DATABASE),
            ("Security: Authentication & Authorization", ExtractionCategory.SECURITY),
            ("Performance -> Optimization", ExtractionCategory.PERFORMANCE),
        ]
        
        for text, expected in test_cases:
            result = detector.detect(text)
            assert result == expected
    
    def test_detect_with_code_snippets(self, detector):
        """Test detection with code snippets in text."""
        text_with_code = """
        Database connection example:
        ```python
        conn = psycopg2.connect(database="test")
        ```
        """
        
        result = detector.detect(text_with_code)
        assert result == ExtractionCategory.DATABASE
    
    def test_priority_order(self, detector):
        """Test that certain categories have priority."""
        # Text mentioning multiple categories
        priority_tests = [
            # Critical should take precedence
            ("CRITICAL security issue in API", ExtractionCategory.CRITICAL),
            ("URGENT: Database performance problem", ExtractionCategory.CRITICAL),
            
            # Security often high priority
            ("Security considerations for API design", ExtractionCategory.SECURITY),
            ("Authentication system architecture", ExtractionCategory.SECURITY),
        ]
        
        for text, expected in priority_tests:
            result = detector.detect(text)
            assert result == expected
    
    def test_detect_with_acronyms(self, detector):
        """Test detection with common acronyms."""
        acronym_tests = [
            ("REST API implementation", ExtractionCategory.API),
            ("SQL database design", ExtractionCategory.DATABASE),
            ("TDD approach for testing", ExtractionCategory.TESTING),
            ("CI/CD pipeline setup", ExtractionCategory.DEPLOYMENT),
            ("JWT token security", ExtractionCategory.SECURITY),
        ]
        
        for text, expected in acronym_tests:
            result = detector.detect(text)
            assert result == expected
    
    def test_detect_with_numbers(self, detector):
        """Test detection with numbers in text."""
        number_tests = [
            ("API v2.0 documentation", ExtractionCategory.API),
            ("Database with 1000+ tables", ExtractionCategory.DATABASE),
            ("Performance: 50% improvement", ExtractionCategory.PERFORMANCE),
        ]
        
        for text, expected in number_tests:
            result = detector.detect(text)
            assert result == expected
    
    def test_weighted_detection(self, detector):
        """Test that detection considers word frequency/weight."""
        # Multiple mentions should strengthen detection
        text = "Database database DATABASE - this is all about database design"
        result = detector.detect(text)
        assert result == ExtractionCategory.DATABASE
    
    def test_contextual_detection(self, detector):
        """Test detection based on context clues."""
        context_tests = [
            ("Schema migration script", ExtractionCategory.DATABASE),
            ("Endpoint throttling implementation", ExtractionCategory.API),
            ("Coverage report generation", ExtractionCategory.TESTING),
            ("Container orchestration setup", ExtractionCategory.DEPLOYMENT),
        ]
        
        for text, expected in context_tests:
            result = detector.detect(text)
            assert result == expected
    
    def test_get_category_keywords(self, detector):
        """Test getting keywords for a category."""
        # Should return relevant keywords for each category
        for category in ExtractionCategory:
            keywords = detector.get_keywords(category)
            assert isinstance(keywords, list)
            assert len(keywords) > 0
            assert all(isinstance(k, str) for k in keywords)
    
    def test_add_custom_keywords(self, detector):
        """Test adding custom keywords for categories."""
        # Add custom keyword
        detector.add_keyword(ExtractionCategory.DATABASE, "datastore")
        
        # Should now detect with custom keyword
        result = detector.detect("Datastore configuration")
        assert result == ExtractionCategory.DATABASE
    
    def test_confidence_scoring(self, detector):
        """Test confidence scoring in detection."""
        # If detector supports confidence scores
        if hasattr(detector, 'detect_with_confidence'):
            test_cases = [
                ("Database", 0.7),  # Single keyword, moderate confidence
                ("PostgreSQL database schema design", 0.9),  # Multiple keywords, high confidence
                ("Random text with no keywords", 0.1),  # No keywords, low confidence
            ]
            
            for text, min_confidence in test_cases:
                category, confidence = detector.detect_with_confidence(text)
                assert confidence >= min_confidence