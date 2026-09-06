# Tavily MCP 集成指南

## 概述

本指南說明如何將 Tavily MCP 集成到 Between Coffee 系統的工作流中，以增強系統的智能搜索和市場研究能力。

## 集成架構

```
Between Coffee 系統
    ├── Django 後端
    ├── PostgreSQL 數據庫
    ├── WebSocket 實時通訊
    └── Tavily MCP (新增)
        ├── 市場研究
        ├── 技術問題解決
        ├── 競爭對手分析
        └── 行業趨勢監控
```

## 集成場景

### 1. 市場研究與競爭對手分析

#### 使用場景
- 分析咖啡店行業趨勢
- 研究競爭對手的功能和定價
- 監控市場新產品和服務

#### 集成示例

```javascript
// 市場研究工具
async function researchCoffeeMarket() {
  const results = await search_tavily({
    query: "2024 咖啡店行業趨勢 香港",
    max_results: 10,
    search_depth: "advanced",
    include_answer: true
  });
  
  // 分析結果並生成報告
  const analysis = analyzeMarketTrends(results);
  saveMarketReport(analysis);
  
  return analysis;
}

// 競爭對手分析
async function analyzeCompetitors() {
  const competitors = ["星巴克", "太平洋咖啡", "麥咖啡"];
  const competitorData = [];
  
  for (const competitor of competitors) {
    const results = await search_tavily({
      query: `${competitor} 咖啡店 香港 價格 菜單`,
      max_results: 5,
      include_answer: true
    });
    
    competitorData.push({
      name: competitor,
      data: results,
      analysis: analyzeCompetitorData(results)
    });
  }
  
  return competitorData;
}
```

### 2. 技術問題解決

#### 使用場景
- 解決 Django 和 WebSocket 技術問題
- 優化數據庫查詢性能
- 學習新的技術最佳實踐

#### 集成示例

```javascript
// 技術問題解決工具
async function solveTechnicalIssue(issue) {
  const results = await search_tavily({
    query: `Django ${issue} 解決方案 最佳實踐`,
    max_results: 8,
    search_depth: "advanced",
    include_answer: true
  });
  
  // 提取相關解決方案
  const solutions = extractSolutions(results);
  
  // 生成代碼示例
  const codeExamples = generateCodeExamples(solutions);
  
  return {
    issue,
    solutions,
    codeExamples,
    references: results
  };
}

// 性能優化建議
async function getPerformanceOptimizationTips() {
  const results = await search_tavily({
    query: "PostgreSQL 查詢優化 索引 性能調優",
    max_results: 6,
    include_answer: true
  });
  
  return {
    tips: extractOptimizationTips(results),
    implementationSteps: generateImplementationSteps(results)
  };
}
```

### 3. 業務決策支持

#### 使用場景
- 價格策略制定
- 新產品開發決策
- 客戶體驗優化

#### 集成示例

```javascript
// 價格策略研究
async function researchPricingStrategies() {
  const results = await search_tavily({
    query: "咖啡店定價策略 香港 市場分析",
    max_results: 7,
    include_answer: true,
    include_raw_content: true
  });
  
  const strategies = analyzePricingStrategies(results);
  
  return {
    marketAnalysis: results,
    recommendedStrategies: strategies,
    implementationPlan: createImplementationPlan(strategies)
  };
}

// 客戶體驗優化
async function optimizeCustomerExperience() {
  const results = await search_tavily({
    query: "咖啡店客戶體驗 最佳實踐 2024",
    max_results: 8,
    search_depth: "advanced",
    include_answer: true
  });
  
  return {
    bestPractices: extractBestPractices(results),
    improvementAreas: identifyImprovementAreas(results),
    actionPlan: createActionPlan(results)
  };
}
```

## 集成實現

### 1. 創建 Tavily 服務層

```python
# eshop/services/tavily_service.py
import os
import json
import requests
from django.conf import settings

class TavilyService:
    """Tavily 搜索服務"""
    
    def __init__(self):
        self.api_key = os.getenv('TAVILY_API_KEY')
        self.base_url = 'https://api.tavily.com'
        
    def search(self, query, max_results=5, include_answer=True, search_depth='basic'):
        """執行 Tavily 搜索"""
        payload = {
            'api_key': self.api_key,
            'query': query,
            'max_results': max_results,
            'include_answer': include_answer,
            'search_depth': search_depth
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/search',
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # 記錄錯誤並返回空結果
            logger.error(f'Tavily 搜索失敗: {e}')
            return {
                'query': query,
                'results': [],
                'error': str(e)
            }
    
    def search_with_options(self, query, **options):
        """進階搜索選項"""
        payload = {
            'api_key': self.api_key,
            'query': query,
            **options
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/search',
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f'Tavily 進階搜索失敗: {e}')
            return {
                'query': query,
                'results': [],
                'error': str(e)
            }
```

### 2. 創建市場研究視圖

```python
# eshop/views/market_research.py
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from eshop.services.tavily_service import TavilyService

class MarketResearchView(LoginRequiredMixin, View):
    """市場研究視圖"""
    
    def get(self, request):
        """獲取市場研究數據"""
        topic = request.GET.get('topic', '咖啡店行業趨勢')
        
        tavily = TavilyService()
        results = tavily.search(
            query=f'{topic} 香港 2024',
            max_results=8,
            include_answer=True,
            search_depth='advanced'
        )
        
        return JsonResponse({
            'success': True,
            'topic': topic,
            'results': results.get('results', []),
            'answer': results.get('answer', ''),
            'response_time': results.get('response_time', 0)
        })

class CompetitorAnalysisView(LoginRequiredMixin, View):
    """競爭對手分析視圖"""
    
    def get(self, request):
        """分析競爭對手"""
        competitors = ['星巴克', '太平洋咖啡', '麥咖啡', 'Pret A Manger']
        analysis_results = []
        
        tavily = TavilyService()
        
        for competitor in competitors:
            results = tavily.search(
                query=f'{competitor} 咖啡 香港 價格 菜單 評價',
                max_results=5,
                include_answer=True
            )
            
            analysis_results.append({
                'competitor': competitor,
                'results': results.get('results', []),
                'summary': self._summarize_competitor_data(results)
            })
        
        return JsonResponse({
            'success': True,
            'competitors': competitors,
            'analysis': analysis_results
        })
    
    def _summarize_competitor_data(self, results):
        """總結競爭對手數據"""
        # 實現數據分析邏輯
        return {
            'price_range': self._extract_price_range(results),
            'popular_items': self._extract_popular_items(results),
            'customer_reviews': self._analyze_reviews(results)
        }
```

### 3. 創建技術支持視圖

```python
# eshop/views/technical_support.py
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from eshop.services.tavily_service import TavilyService

class TechnicalSupportView(LoginRequiredMixin, View):
    """技術支持視圖"""
    
    def post(self, request):
        """搜索技術問題解決方案"""
        data = json.loads(request.body)
        issue = data.get('issue', '')
        technology = data.get('technology', 'Django')
        
        if not issue:
            return JsonResponse({
                'success': False,
                'error': '請提供技術問題描述'
            })
        
        tavily = TavilyService()
        results = tavily.search(
            query=f'{technology} {issue} 解決方案 最佳實踐',
            max_results=6,
            include_answer=True,
            search_depth='advanced'
        )
        
        return JsonResponse({
            'success': True,
            'issue': issue,
            'technology': technology,
            'solutions': self._extract_solutions(results),
            'code_examples': self._extract_code_examples(results),
            'references': results.get('results', [])
        })
    
    def _extract_solutions(self, results):
        """提取解決方案"""
        solutions = []
        for result in results.get('results', []):
            if 'solution' in result['content'].lower() or 'fix' in result['content'].lower():
                solutions.append({
                    'title': result['title'],
                    'url': result['url'],
                    'summary': result['content'][:200]
                })
        return solutions
    
    def _extract_code_examples(self, results):
        """提取代碼示例"""
        code_examples = []
        for result in results.get('results', []):
            if 'code' in result['content'].lower() or 'example' in result['content'].lower():
                code_examples.append({
                    'title': result['title'],
                    'url': result['url'],
                    'language': self._detect_language(result['content'])
                })
        return code_examples
    
    def _detect_language(self, content):
        """檢測編程語言"""
        if 'python' in content.lower():
            return 'Python'
        elif 'javascript' in content.lower():
            return 'JavaScript'
        elif 'sql' in content.lower():
            return 'SQL'
        else:
            return 'Unknown'
```

### 4. 創建業務決策視圖

```python
# eshop/views/business_decisions.py
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from eshop.services.tavily_service import TavilyService

class PricingStrategyView(LoginRequiredMixin, View):
    """價格策略視圖"""
    
    def get(self, request):
        """研究價格策略"""
        tavily = TavilyService()
        
        # 搜索多個相關主題
        topics = [
            '咖啡店定價策略',
            '香港咖啡市場價格',
            '精品咖啡定價',
            '咖啡店促銷策略'
        ]
        
        all_results = []
        for topic in topics:
            results = tavily.search(
                query=f'{topic} 2024',
                max_results=4,
                include_answer=True
            )
            all_results.append({
                'topic': topic,
                'results': results.get('results', []),
                'insights': self._extract_insights(results)
            })
        
        return JsonResponse({
            'success': True,
            'analysis': all_results,
            'recommendations': self._generate_recommendations(all_results)
        })
    
    def _extract_insights(self, results):
        """提取洞察"""
        insights = []
        for result in results.get('results', []):
            if 'price' in result['content'].lower() or 'cost' in result['content'].lower():
                insights.append({
                    'title': result['title'],
                    'key_points': self._extract_key_points(result['content'])
                })
        return insights
    
    def _extract_key_points(self, content):
        """提取關鍵點"""
        # 簡單的關鍵點提取邏輯
        sentences = content.split('.')
        key_points = []
        for sentence in sentences[:5]:  # 取前5個句子
            if len(sentence.strip()) > 20:
                key_points.append(sentence.strip())
        return key_points
    
    def _generate_recommendations(self, analysis):
        """生成推薦"""
        recommendations = []
        
        # 基於分析結果生成推薦
        for item in analysis:
            if '定價' in item['topic']:
                recommendations.append({
                    'type': '定價策略',
                    'suggestion': '考慮採用分層定價策略，針對不同客戶群體提供不同價格選項',
                    'priority': '高'
                })
        
        return recommendations
```

## 前端集成

### 1. 創建市場研究組件

```javascript
// static/js/market-research.js
class MarketResearchComponent {
    constructor() {
        this.apiUrl = '/api/market-research/';
        this.resultsContainer = document.getElementById('market-research-results');
    }
    
    async researchTopic(topic) {
        try {
            const response = await fetch(`${this.apiUrl}?topic=${encodeURIComponent(topic)}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayResults(data);
                return data;
            } else {
                console.error('市場研究失敗:', data.error);
                return null;
            }
        } catch (error) {
            console.error('市場研究請求失敗:', error);
            return null;
        }
    }
    
    displayResults(data) {
        if (!this.resultsContainer) return;
        
        let html = `
            <div class="market-research-results">
                <h3>市場研究: ${data.topic}</h3>
                <div class="ai-answer">${data.answer || '無 AI 生成答案'}</div>
                <div class="results-list">
        `;
        
        data.results.forEach((result, index) => {
            html += `
                <div class="result-item">
                    <h4>${index + 1}. ${result.title}</h4>
                    <p class="url"><a href="${result.url}" target="_blank">${result.url}</a></p>
                    <p class="content">${result.content.substring(0, 200)}...</p>
                    <p class="relevance">相關度: ${(result.score * 100).toFixed(1)}%</p>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
        
        this.resultsContainer.innerHTML = html;
    }
    
    async analyzeCompetitors() {
        try {
            const response = await fetch('/api/competitor-analysis/');
            const data = await response.json();
            
            if (data.success) {
                this.displayCompetitorAnalysis(data);
                return data;
            } else {
                console.error('競爭對手分析失敗:', data.error);
                return null;
            }
        } catch (error) {
            console.error('競爭對手分析請求失敗:', error);
            return null;
        }
    }
    
    displayCompetitorAnalysis(data) {
        // 實現競爭對手分析顯示邏輯
    }
}
```

### 2. 創建技術支持組件

```javascript
// static/js/technical-support.js
class TechnicalSupportComponent {
    constructor() {
        this.apiUrl = '/api/technical-support/';
        this.solutionsContainer = document.getElementById('technical-solutions');
    }
    
    async searchSolution(issue, technology = 'Django') {
        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    issue: issue,
                    technology: technology
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displaySolutions(data);
                return data;
            } else {
                console.error('技術支持搜索失敗:', data.error);
                return null;
            }
        } catch (error) {
            console.error('技術支持請求失敗:', error);
            return null;
        }
    }
    
    displaySolutions(data) {
        if (!this.solutionsContainer) return;
        
        let html = `
            <div class="technical-solutions">
                <h3>技術問題: ${data.issue}</h3>
                <p>技術棧: ${data.technology}</p>
                
                <div class="solutions-section">
                    <h4>解決方案</h4>
        `;
        
        if (data.solutions.length > 0) {
            data.solutions.forEach((solution, index) => {
                html += `
                    <div class="solution-item">
                        <h5>${index + 1}. ${solution.title}</h5>
                        <p>${solution.summary}</p>
                        <a href="${solution.url}" target="_blank">查看詳情</a>
                    </div>
                `;
            });
        } else {
            html += `<p>未找到具體解決方案</p>`;
        }
        
        html += `
                </div>
                
                <div class="code-examples-section">
                    <h4>代碼示例</h4>
        `;
        
        if (data.code_examples.length > 0) {
            data.code_examples.forEach((example, index) => {
                html += `
                    <div class="code-example-item">
                        <h5>${index + 1}. ${example.title} (${example.language})</h5>
                        <a href="${example.url}" target="_blank">查看代碼</a>
                    </div>
                `;
            });
        } else {
            html += `<p>未找到代碼示例</p>`;
        }
        
        html += `
                </div>
            </div>
        `