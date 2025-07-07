# Custom Categories Tutorial

Learn how to create and configure custom categories for your specific documentation needs.

## Understanding Categories

### Default Categories

Trapper Keeper comes with 14 default categories:

| Category | Emoji | Purpose | Keywords |
|----------|-------|---------|----------|
| Architecture | 🏗️ | System design and structure | architecture, design, pattern, structure |
| Database | 🗄️ | Database schemas and queries | database, sql, schema, query |
| Security | 🔐 | Security and authentication | security, auth, encryption, password |
| Features | ✅ | Feature descriptions | feature, functionality, capability |
| Monitoring | 📊 | Logging and observability | monitor, log, metric, trace |
| Critical | 🚨 | Urgent issues | critical, urgent, breaking, important |
| Setup | 📋 | Installation and config | setup, install, configure, init |
| API | 🌐 | API documentation | api, endpoint, route, request |
| Testing | 🧪 | Test strategies | test, spec, unit, integration |
| Performance | ⚡ | Optimization | performance, speed, optimize, cache |
| Documentation | 📚 | Guides and references | docs, guide, tutorial, reference |
| Deployment | 🚀 | Deploy and CI/CD | deploy, ci, cd, release |
| Configuration | ⚙️ | Settings and options | config, setting, option, parameter |
| Dependencies | 📦 | Package management | dependency, package, library, module |

### Category Detection Methods

1. **Keyword Matching**: Searches for specific keywords in content
2. **Pattern Matching**: Uses regex patterns for complex matching
3. **Context Analysis**: Considers section titles and surrounding content
4. **Importance Scoring**: Weights matches based on frequency and position

## Creating Custom Categories

### Method 1: Configuration File

Add custom categories in your `config.yaml`:

```yaml
# config.yaml
extraction:
  categories:
    # Default categories...
    - "🎯 Custom Category"
    - "🔬 Research"
    - "💰 Business Logic"
    - "🎨 UI/UX"

detection:
  custom_patterns:
    "🎯 Custom Category":
      keywords:
        - "custom"
        - "specific"
        - "domain"
      patterns:
        - ".*custom logic.*"
        - ".*business rule.*"
      importance_boost: 0.2
      
    "🔬 Research":
      keywords:
        - "research"
        - "study"
        - "analysis"
        - "findings"
      patterns:
        - ".*research findings.*"
        - ".*data analysis.*"
        - ".*study results.*"
      importance_boost: 0.3
      
    "💰 Business Logic":
      keywords:
        - "business"
        - "revenue"
        - "pricing"
        - "customer"
      patterns:
        - ".*business logic.*"
        - ".*revenue model.*"
        - ".*pricing strategy.*"
      importance_boost: 0.25
      
    "🎨 UI/UX":
      keywords:
        - "design"
        - "ui"
        - "ux"
        - "interface"
        - "component"
      patterns:
        - ".*user interface.*"
        - ".*design system.*"
        - ".*component library.*"
      importance_boost: 0.15
```

### Method 2: CLI Commands

Add categories dynamically:

```bash
# Add a single category
trapper-keeper categories --add "🎯 Custom Category"

# Add with keywords
trapper-keeper categories --add "🔬 Research" \
  --keywords "research,study,analysis,findings"

# Add with patterns
trapper-keeper categories --add "💰 Business Logic" \
  --patterns ".*business rule.*,.*revenue.*"
```

### Method 3: Python API

```python
from trapper_keeper.core.config import Config
from trapper_keeper.extractor import CategoryDetector

# Load config
config = Config.load()

# Add custom category
config.add_category(
    name="🎯 Custom Category",
    keywords=["custom", "specific", "domain"],
    patterns=[".*custom logic.*", ".*domain specific.*"],
    importance_boost=0.2
)

# Save config
config.save()

# Use in detection
detector = CategoryDetector(config)
category, confidence = detector.detect_category(
    "This is custom domain-specific logic for our application"
)
```

## Domain-Specific Examples

### 1. Healthcare Documentation

```yaml
detection:
  custom_patterns:
    "🏥 Patient Care":
      keywords:
        - "patient"
        - "treatment"
        - "diagnosis"
        - "medical"
      patterns:
        - ".*patient care.*"
        - ".*treatment plan.*"
        - ".*medical record.*"
      importance_boost: 0.4
      
    "💊 Medications":
      keywords:
        - "medication"
        - "prescription"
        - "dosage"
        - "drug"
      patterns:
        - ".*medication.*"
        - ".*prescription.*"
        - ".*dosage.*"
      importance_boost: 0.35
      
    "🔬 Lab Results":
      keywords:
        - "lab"
        - "test"
        - "result"
        - "analysis"
      patterns:
        - ".*lab result.*"
        - ".*test result.*"
        - ".*blood work.*"
      importance_boost: 0.3
      
    "📋 Compliance":
      keywords:
        - "hipaa"
        - "compliance"
        - "regulation"
        - "privacy"
      patterns:
        - ".*HIPAA.*"
        - ".*compliance.*"
        - ".*regulation.*"
      importance_boost: 0.45
```

### 2. Financial Services

```yaml
detection:
  custom_patterns:
    "💰 Trading":
      keywords:
        - "trade"
        - "order"
        - "execution"
        - "market"
      patterns:
        - ".*trading strategy.*"
        - ".*order execution.*"
        - ".*market data.*"
      importance_boost: 0.35
      
    "📊 Risk Management":
      keywords:
        - "risk"
        - "exposure"
        - "hedge"
        - "portfolio"
      patterns:
        - ".*risk management.*"
        - ".*exposure limit.*"
        - ".*portfolio risk.*"
      importance_boost: 0.4
      
    "🏦 Compliance":
      keywords:
        - "regulatory"
        - "compliance"
        - "audit"
        - "reporting"
      patterns:
        - ".*regulatory.*"
        - ".*compliance.*"
        - ".*audit trail.*"
      importance_boost: 0.45
      
    "💳 Payments":
      keywords:
        - "payment"
        - "transaction"
        - "settlement"
        - "clearing"
      patterns:
        - ".*payment processing.*"
        - ".*transaction.*"
        - ".*settlement.*"
      importance_boost: 0.3
```

### 3. E-commerce

```yaml
detection:
  custom_patterns:
    "🛒 Shopping Cart":
      keywords:
        - "cart"
        - "basket"
        - "checkout"
        - "order"
      patterns:
        - ".*shopping cart.*"
        - ".*checkout process.*"
        - ".*order management.*"
      importance_boost: 0.3
      
    "📦 Inventory":
      keywords:
        - "inventory"
        - "stock"
        - "warehouse"
        - "fulfillment"
      patterns:
        - ".*inventory management.*"
        - ".*stock level.*"
        - ".*warehouse.*"
      importance_boost: 0.25
      
    "💰 Pricing":
      keywords:
        - "price"
        - "discount"
        - "promotion"
        - "coupon"
      patterns:
        - ".*pricing strategy.*"
        - ".*discount rule.*"
        - ".*promotion.*"
      importance_boost: 0.3
      
    "🚚 Shipping":
      keywords:
        - "shipping"
        - "delivery"
        - "logistics"
        - "tracking"
      patterns:
        - ".*shipping method.*"
        - ".*delivery option.*"
        - ".*tracking.*"
      importance_boost: 0.25
```

### 4. Game Development

```yaml
detection:
  custom_patterns:
    "🎮 Gameplay":
      keywords:
        - "gameplay"
        - "mechanic"
        - "level"
        - "player"
      patterns:
        - ".*game mechanic.*"
        - ".*level design.*"
        - ".*player action.*"
      importance_boost: 0.35
      
    "🎨 Graphics":
      keywords:
        - "render"
        - "shader"
        - "texture"
        - "model"
      patterns:
        - ".*rendering.*"
        - ".*shader.*"
        - ".*3D model.*"
      importance_boost: 0.3
      
    "🎵 Audio":
      keywords:
        - "audio"
        - "sound"
        - "music"
        - "sfx"
      patterns:
        - ".*audio system.*"
        - ".*sound effect.*"
        - ".*music.*"
      importance_boost: 0.2
      
    "🎯 AI/NPCs":
      keywords:
        - "ai"
        - "npc"
        - "behavior"
        - "pathfinding"
      patterns:
        - ".*AI behavior.*"
        - ".*NPC.*"
        - ".*pathfinding.*"
      importance_boost: 0.3
```

## Advanced Category Configuration

### Category Hierarchies

Create category hierarchies for better organization:

```yaml
detection:
  category_hierarchy:
    "🏗️ Architecture":
      subcategories:
        "🔧 Backend Architecture":
          keywords: ["backend", "server", "api"]
        "🎨 Frontend Architecture":
          keywords: ["frontend", "ui", "component"]
        "🔌 Integration Architecture":
          keywords: ["integration", "connector", "adapter"]
    
    "🔐 Security":
      subcategories:
        "🔑 Authentication":
          keywords: ["auth", "login", "token"]
        "🛡️ Authorization":
          keywords: ["permission", "role", "access"]
        "🔒 Encryption":
          keywords: ["encrypt", "decrypt", "cipher"]
```

### Contextual Categories

Categories that consider context:

```python
class ContextualCategoryDetector:
    def detect_with_context(self, content, context):
        """Detect category considering context."""
        
        # Check document metadata
        if context.get('file_path', '').startswith('api/'):
            return "🌐 API", 0.9
        
        # Check section hierarchy
        if context.get('parent_section', '').lower() == 'security':
            return "🔐 Security", 0.85
        
        # Check surrounding sections
        prev_category = context.get('previous_category')
        if prev_category == "🏗️ Architecture":
            # Architecture sections often followed by implementation
            if "implement" in content.lower():
                return "💻 Implementation", 0.7
        
        # Fall back to standard detection
        return self.detect_category(content)
```

### Dynamic Category Loading

Load categories from external sources:

```python
import requests
import yaml

class DynamicCategoryLoader:
    def __init__(self, source_url):
        self.source_url = source_url
    
    def load_categories(self):
        """Load categories from external source."""
        
        response = requests.get(self.source_url)
        categories = yaml.safe_load(response.text)
        
        config = Config.load()
        
        for category in categories:
            config.add_category(
                name=category['name'],
                keywords=category['keywords'],
                patterns=category.get('patterns', []),
                importance_boost=category.get('importance_boost', 0.0)
            )
        
        config.save()
        return len(categories)

# Usage
loader = DynamicCategoryLoader(
    'https://example.com/trapper-keeper-categories.yaml'
)
loaded = loader.load_categories()
print(f"Loaded {loaded} categories")
```

## Category Testing

### Test Your Categories

Create a test script to validate category detection:

```python
#!/usr/bin/env python3
# test_categories.py

from trapper_keeper.extractor import CategoryDetector
from trapper_keeper.core.config import Config

# Test cases
test_cases = [
    {
        'content': 'This section describes our microservices architecture',
        'expected': '🏗️ Architecture'
    },
    {
        'content': 'Patient treatment plans must be reviewed quarterly',
        'expected': '🏥 Patient Care'
    },
    {
        'content': 'The trading algorithm executes market orders',
        'expected': '💰 Trading'
    }
]

# Load config with custom categories
config = Config.load()
detector = CategoryDetector(config)

# Run tests
for test in test_cases:
    category, confidence = detector.detect_category(test['content'])
    
    if category == test['expected']:
        print(f"✅ PASS: '{test['content'][:50]}...' -> {category} ({confidence:.2f})")
    else:
        print(f"❌ FAIL: Expected {test['expected']}, got {category}")
```

### Category Performance Testing

```python
import time
from statistics import mean, stdev

def benchmark_category_detection(detector, test_content, iterations=1000):
    """Benchmark category detection performance."""
    
    times = []
    
    for _ in range(iterations):
        start = time.time()
        category, confidence = detector.detect_category(test_content)
        times.append(time.time() - start)
    
    print(f"Category Detection Performance:")
    print(f"  Average: {mean(times)*1000:.2f}ms")
    print(f"  Std Dev: {stdev(times)*1000:.2f}ms")
    print(f"  Min: {min(times)*1000:.2f}ms")
    print(f"  Max: {max(times)*1000:.2f}ms")
```

## Best Practices

### 1. Choose Meaningful Emojis

Select emojis that are:
- Visually distinct
- Semantically relevant
- Universally understood
- Available across platforms

### 2. Balance Keywords

- Use 3-7 keywords per category
- Include variations (singular/plural)
- Consider synonyms
- Avoid overly generic terms

### 3. Test Patterns Carefully

```bash
# Test your regex patterns
echo "Your test content" | grep -E "your.*pattern.*here"

# Test in Trapper Keeper
trapper-keeper test-pattern "your.*pattern.*here" sample.md
```

### 4. Set Appropriate Importance Boosts

- Critical categories: 0.4 - 0.5
- Important categories: 0.2 - 0.4
- Standard categories: 0.0 - 0.2
- Low priority: -0.1 - 0.0

### 5. Document Your Categories

Create a reference for your team:

```markdown
# Custom Categories Reference

## 🎯 Custom Category
**Purpose**: Identify domain-specific logic
**Keywords**: custom, specific, domain
**When to use**: For business rules unique to our application
**Examples**:
- Custom validation logic
- Domain-specific calculations
- Business rule implementations
```

## Troubleshooting

### Category Not Detected

1. Check keyword spelling
2. Verify patterns are valid regex
3. Increase importance boost
4. Add more keywords
5. Check for conflicting categories

### Wrong Category Detected

1. Make keywords more specific
2. Use negative patterns to exclude
3. Adjust importance boosts
4. Consider context-based detection

### Performance Issues

1. Limit pattern complexity
2. Reduce number of patterns
3. Use keyword matching first
4. Cache detection results

## Next Steps

- [Plugin Development](../development/plugin-development.md) - Create category plugins
- [API Reference](../api-reference.md) - Category detection API
- [Configuration Reference](../configuration.md) - Advanced configuration