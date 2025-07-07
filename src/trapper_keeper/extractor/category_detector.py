"""Category detection for extracted content."""

import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from ..core.types import ExtractionCategory


@dataclass
class CategoryPattern:
    """Pattern for detecting a category."""
    
    category: ExtractionCategory
    keywords: List[str]
    patterns: List[str]
    weight: float = 1.0


class CategoryDetector:
    """Detects categories for content based on patterns and keywords."""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.custom_rules = []
        self.ml_model = None  # Placeholder for future ML integration
        self.category_scores_cache = {}
        
    def _initialize_patterns(self) -> List[CategoryPattern]:
        """Initialize category detection patterns."""
        return [
            CategoryPattern(
                category=ExtractionCategory.ARCHITECTURE,
                keywords=["architecture", "design", "structure", "pattern", "component", "module", "system design"],
                patterns=[
                    r"architect(?:ure|ural)",
                    r"design\s+pattern",
                    r"system\s+(?:design|architecture)",
                    r"(?:micro)?service",
                    r"component\s+(?:design|structure)",
                ],
                weight=1.0
            ),
            CategoryPattern(
                category=ExtractionCategory.DATABASE,
                keywords=["database", "sql", "nosql", "schema", "migration", "query", "index"],
                patterns=[
                    r"database",
                    r"(?:sql|nosql)",
                    r"schema",
                    r"migration",
                    r"(?:table|index|query)",
                    r"(?:postgres|mysql|mongodb|redis)",
                ],
                weight=1.0
            ),
            CategoryPattern(
                category=ExtractionCategory.SECURITY,
                keywords=["security", "authentication", "authorization", "encryption", "vulnerability", "attack"],
                patterns=[
                    r"secur(?:e|ity)",
                    r"auth(?:entication|orization)",
                    r"encrypt(?:ion)?",
                    r"vulnerabilit(?:y|ies)",
                    r"(?:xss|csrf|sql\s*injection)",
                    r"(?:password|token|credential)",
                ],
                weight=1.2
            ),
            CategoryPattern(
                category=ExtractionCategory.FEATURES,
                keywords=["feature", "functionality", "requirement", "user story", "use case"],
                patterns=[
                    r"feature",
                    r"functionalit(?:y|ies)",
                    r"requirement",
                    r"user\s+stor(?:y|ies)",
                    r"use\s+case",
                    r"capabilit(?:y|ies)",
                ],
                weight=0.9
            ),
            CategoryPattern(
                category=ExtractionCategory.MONITORING,
                keywords=["monitoring", "logging", "metrics", "observability", "alerting", "dashboard"],
                patterns=[
                    r"monitor(?:ing)?",
                    r"logg(?:ing|er)",
                    r"metric(?:s)?",
                    r"observability",
                    r"alert(?:ing|s)?",
                    r"dashboard",
                    r"(?:prometheus|grafana|elk)",
                ],
                weight=1.0
            ),
            CategoryPattern(
                category=ExtractionCategory.CRITICAL,
                keywords=["critical", "urgent", "emergency", "breaking", "severe", "blocker"],
                patterns=[
                    r"critical",
                    r"urgent",
                    r"emergency",
                    r"breaking\s+change",
                    r"severe",
                    r"blocker",
                    r"high\s+priority",
                ],
                weight=1.5
            ),
            CategoryPattern(
                category=ExtractionCategory.SETUP,
                keywords=["setup", "installation", "configuration", "initialization", "bootstrap"],
                patterns=[
                    r"setup",
                    r"install(?:ation)?",
                    r"configur(?:e|ation)",
                    r"initializ(?:e|ation)",
                    r"bootstrap",
                    r"getting\s+started",
                ],
                weight=0.8
            ),
            CategoryPattern(
                category=ExtractionCategory.API,
                keywords=["api", "endpoint", "rest", "graphql", "webhook", "integration"],
                patterns=[
                    r"api",
                    r"endpoint",
                    r"rest(?:ful)?",
                    r"graphql",
                    r"webhook",
                    r"integration",
                    r"(?:get|post|put|delete|patch)",
                ],
                weight=1.0
            ),
            CategoryPattern(
                category=ExtractionCategory.TESTING,
                keywords=["test", "testing", "unit test", "integration test", "e2e", "coverage"],
                patterns=[
                    r"test(?:s|ing)?",
                    r"unit\s+test",
                    r"integration\s+test",
                    r"e2e",
                    r"coverage",
                    r"(?:jest|pytest|mocha|jasmine)",
                ],
                weight=0.9
            ),
            CategoryPattern(
                category=ExtractionCategory.PERFORMANCE,
                keywords=["performance", "optimization", "speed", "latency", "throughput", "scalability"],
                patterns=[
                    r"performance",
                    r"optimi(?:z|s)(?:e|ation)",
                    r"speed",
                    r"latency",
                    r"throughput",
                    r"scalability",
                    r"(?:fast|slow|quick)",
                ],
                weight=1.1
            ),
            CategoryPattern(
                category=ExtractionCategory.DOCUMENTATION,
                keywords=["documentation", "docs", "readme", "guide", "tutorial", "reference"],
                patterns=[
                    r"documentation",
                    r"docs?",
                    r"readme",
                    r"guide",
                    r"tutorial",
                    r"reference",
                    r"example",
                ],
                weight=0.7
            ),
            CategoryPattern(
                category=ExtractionCategory.DEPLOYMENT,
                keywords=["deployment", "deploy", "release", "ci/cd", "pipeline", "production"],
                patterns=[
                    r"deploy(?:ment)?",
                    r"release",
                    r"ci/?cd",
                    r"pipeline",
                    r"production",
                    r"(?:docker|kubernetes|k8s)",
                ],
                weight=1.0
            ),
            CategoryPattern(
                category=ExtractionCategory.CONFIGURATION,
                keywords=["configuration", "config", "settings", "environment", "variables", "options"],
                patterns=[
                    r"configur(?:e|ation)",
                    r"config",
                    r"settings?",
                    r"environment",
                    r"variable",
                    r"option",
                    r"parameter",
                ],
                weight=0.8
            ),
            CategoryPattern(
                category=ExtractionCategory.DEPENDENCIES,
                keywords=["dependency", "dependencies", "package", "library", "module", "import"],
                patterns=[
                    r"dependenc(?:y|ies)",
                    r"package",
                    r"library",
                    r"module",
                    r"import",
                    r"require",
                    r"(?:npm|pip|maven|gradle)",
                ],
                weight=0.8
            ),
        ]
        
    def detect_category(self, content: str, title: Optional[str] = None) -> Tuple[ExtractionCategory, float]:
        """Detect the most likely category for the content."""
        content_lower = content.lower()
        title_lower = title.lower() if title else ""
        
        scores: Dict[ExtractionCategory, float] = {}
        
        for pattern in self.patterns:
            score = 0.0
            
            # Check keywords
            for keyword in pattern.keywords:
                if keyword in content_lower:
                    score += 1.0
                if keyword in title_lower:
                    score += 2.0  # Title matches are weighted higher
                    
            # Check regex patterns
            for regex in pattern.patterns:
                matches = len(re.findall(regex, content_lower, re.IGNORECASE))
                score += matches * 0.5
                
                if title and re.search(regex, title_lower, re.IGNORECASE):
                    score += 3.0  # Strong signal in title
                    
            # Apply weight
            score *= pattern.weight
            
            if score > 0:
                scores[pattern.category] = score
                
        # Return the category with highest score, or CUSTOM if no matches
        if scores:
            best_category = max(scores.items(), key=lambda x: x[1])
            return best_category[0], best_category[1]
        else:
            return ExtractionCategory.CUSTOM, 0.0
            
    def detect_multiple_categories(
        self,
        content: str,
        title: Optional[str] = None,
        threshold: float = 0.3
    ) -> List[Tuple[ExtractionCategory, float]]:
        """Detect multiple applicable categories for the content."""
        content_lower = content.lower()
        title_lower = title.lower() if title else ""
        
        scores: Dict[ExtractionCategory, float] = {}
        
        for pattern in self.patterns:
            score = 0.0
            
            # Check keywords
            for keyword in pattern.keywords:
                if keyword in content_lower:
                    score += 1.0
                if keyword in title_lower:
                    score += 2.0
                    
            # Check regex patterns
            for regex in pattern.patterns:
                matches = len(re.findall(regex, content_lower, re.IGNORECASE))
                score += matches * 0.5
                
                if title and re.search(regex, title_lower, re.IGNORECASE):
                    score += 3.0
                    
            # Apply weight
            score *= pattern.weight
            
            if score > 0:
                scores[pattern.category] = score
                
        # Normalize scores
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                scores = {cat: score / max_score for cat, score in scores.items()}
                
        # Return categories above threshold
        results = [(cat, score) for cat, score in scores.items() if score >= threshold]
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
        
    def add_custom_rule(
        self,
        name: str,
        category: ExtractionCategory,
        keywords: List[str],
        patterns: List[str],
        weight: float = 1.0
    ) -> None:
        """Add a custom category detection rule."""
        custom_pattern = CategoryPattern(
            category=category,
            keywords=keywords,
            patterns=patterns,
            weight=weight
        )
        self.custom_rules.append((name, custom_pattern))
        
    def remove_custom_rule(self, name: str) -> bool:
        """Remove a custom rule by name."""
        for i, (rule_name, _) in enumerate(self.custom_rules):
            if rule_name == name:
                del self.custom_rules[i]
                return True
        return False
        
    def get_custom_rules(self) -> Dict[str, CategoryPattern]:
        """Get all custom rules."""
        return {name: pattern for name, pattern in self.custom_rules}
        
    def detect_with_ml(self, content: str, title: Optional[str] = None) -> Tuple[ExtractionCategory, float]:
        """Detect category using ML model (placeholder for future implementation)."""
        if self.ml_model is None:
            # Fall back to pattern-based detection
            return self.detect_category(content, title)
            
        # Future ML implementation would go here
        # For now, just use pattern detection
        return self.detect_category(content, title)
        
    def analyze_content_features(self, content: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Extract features from content for ML or advanced analysis."""
        features = {
            "content_length": len(content),
            "word_count": len(content.split()),
            "line_count": len(content.split('\n')),
            "has_code": bool(re.search(r'```', content)),
            "has_urls": bool(re.search(r'https?://', content)),
            "has_emails": bool(re.search(r'[\w\.-]+@[\w\.-]+', content)),
            "has_numbers": bool(re.search(r'\d+', content)),
            "uppercase_ratio": sum(1 for c in content if c.isupper()) / len(content) if content else 0,
            "special_char_ratio": sum(1 for c in content if not c.isalnum() and not c.isspace()) / len(content) if content else 0,
        }
        
        # Title features
        if title:
            features["title_length"] = len(title)
            features["title_word_count"] = len(title.split())
            features["title_has_numbers"] = bool(re.search(r'\d+', title))
            
        # Pattern matching scores
        pattern_scores = {}
        for pattern in self.patterns:
            score = self._calculate_pattern_score(content.lower(), title.lower() if title else "", pattern)
            if score > 0:
                pattern_scores[pattern.category.value] = score
                
        features["pattern_scores"] = pattern_scores
        
        # Keyword density
        keyword_density = {}
        content_lower = content.lower()
        for pattern in self.patterns:
            keyword_count = sum(1 for keyword in pattern.keywords if keyword in content_lower)
            if keyword_count > 0:
                keyword_density[pattern.category.value] = keyword_count / len(content.split())
                
        features["keyword_density"] = keyword_density
        
        return features
        
    def _calculate_pattern_score(self, content: str, title: str, pattern: CategoryPattern) -> float:
        """Calculate score for a single pattern."""
        score = 0.0
        
        # Check keywords
        for keyword in pattern.keywords:
            if keyword in content:
                score += 1.0
            if keyword in title:
                score += 2.0
                
        # Check regex patterns
        for regex in pattern.patterns:
            matches = len(re.findall(regex, content, re.IGNORECASE))
            score += matches * 0.5
            
            if title and re.search(regex, title, re.IGNORECASE):
                score += 3.0
                
        return score * pattern.weight
        
    def batch_detect(
        self,
        contents: List[Tuple[str, Optional[str]]]
    ) -> List[Tuple[ExtractionCategory, float]]:
        """Detect categories for multiple contents efficiently."""
        results = []
        
        for content, title in contents:
            # Check cache first
            cache_key = hash((content[:100], title))  # Use first 100 chars for cache key
            
            if cache_key in self.category_scores_cache:
                category, score = self.category_scores_cache[cache_key]
            else:
                category, score = self.detect_category(content, title)
                self.category_scores_cache[cache_key] = (category, score)
                
                # Limit cache size
                if len(self.category_scores_cache) > 1000:
                    # Remove oldest entries
                    keys_to_remove = list(self.category_scores_cache.keys())[:100]
                    for key in keys_to_remove:
                        del self.category_scores_cache[key]
                        
            results.append((category, score))
            
        return results
        
    def suggest_categories(
        self,
        content: str,
        title: Optional[str] = None,
        top_n: int = 3
    ) -> List[Tuple[ExtractionCategory, float, str]]:
        """Suggest top N categories with explanations."""
        categories = self.detect_multiple_categories(content, title, threshold=0.1)
        
        suggestions = []
        for category, score in categories[:top_n]:
            # Generate explanation
            explanation = self._generate_category_explanation(content, title, category)
            suggestions.append((category, score, explanation))
            
        return suggestions
        
    def _generate_category_explanation(
        self,
        content: str,
        title: Optional[str],
        category: ExtractionCategory
    ) -> str:
        """Generate explanation for why a category was suggested."""
        content_lower = content.lower()
        title_lower = title.lower() if title else ""
        
        # Find matching pattern
        for pattern in self.patterns:
            if pattern.category == category:
                matched_keywords = [kw for kw in pattern.keywords if kw in content_lower or kw in title_lower]
                matched_patterns = []
                
                for regex in pattern.patterns:
                    if re.search(regex, content_lower, re.IGNORECASE) or (title and re.search(regex, title_lower, re.IGNORECASE)):
                        matched_patterns.append(regex)
                        
                explanation_parts = []
                
                if matched_keywords:
                    explanation_parts.append(f"Keywords found: {', '.join(matched_keywords[:3])}")
                    
                if matched_patterns:
                    explanation_parts.append(f"Patterns matched: {len(matched_patterns)}")
                    
                if title and any(kw in title_lower for kw in pattern.keywords):
                    explanation_parts.append("Strong match in title")
                    
                return " | ".join(explanation_parts) if explanation_parts else "Pattern-based match"
                
        return "No specific pattern match"