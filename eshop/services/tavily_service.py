"""
Tavily 搜索服務
為 Between Coffee 系統提供智能搜索功能
"""

import os
import json
import requests
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings

# 設置日誌
logger = logging.getLogger(__name__)

class TavilyService:
    """Tavily 搜索服務"""
    
    def __init__(self):
        self.api_key = os.getenv('TAVILY_API_KEY')
        self.base_url = 'https://api.tavily.com'
        
        if not self.api_key:
            logger.warning('TAVILY_API_KEY 環境變數未設置，Tavily 服務將無法使用')
    
    def search(self, query: str, max_results: int = 5, include_answer: bool = True, 
               search_depth: str = 'basic') -> Dict[str, Any]:
        """
        執行 Tavily 搜索
        
        Args:
            query: 搜索查詢
            max_results: 最大結果數量 (1-10)
            include_answer: 是否包含 AI 生成的答案
            search_depth: 搜索深度 ('basic' 或 'advanced')
            
        Returns:
            搜索結果字典
        """
        if not self.api_key:
            return {
                'query': query,
                'results': [],
                'error': 'TAVILY_API_KEY 環境變數未設置',
                'success': False
            }
        
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
            
            data = response.json()
            data['success'] = True
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f'Tavily 搜索失敗: {e}')
            return {
                'query': query,
                'results': [],
                'error': str(e),
                'success': False
            }
    
    def search_with_options(self, query: str, **options) -> Dict[str, Any]:
        """
        進階搜索選項
        
        Args:
            query: 搜索查詢
            **options: 其他搜索選項
            
        Returns:
            搜索結果字典
        """
        if not self.api_key:
            return {
                'query': query,
                'results': [],
                'error': 'TAVILY_API_KEY 環境變數未設置',
                'success': False
            }
        
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
            
            data = response.json()
            data['success'] = True
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f'Tavily 進階搜索失敗: {e}')
            return {
                'query': query,
                'results': [],
                'error': str(e),
                'success': False
            }
    
    def research_coffee_market(self, location: str = '香港', year: str = '2024') -> Dict[str, Any]:
        """
        研究咖啡市場
        
        Args:
            location: 地理位置
            year: 年份
            
        Returns:
            市場研究結果
        """
        query = f'{location} 咖啡店行業趨勢 {year}'
        
        results = self.search(
            query=query,
            max_results=8,
            include_answer=True,
            search_depth='advanced'
        )
        
        if results['success']:
            # 分析市場趨勢
            analysis = self._analyze_market_trends(results)
            results['analysis'] = analysis
        
        return results
    
    def analyze_competitors(self, competitors: List[str] = None) -> Dict[str, Any]:
        """
        分析競爭對手
        
        Args:
            competitors: 競爭對手列表
            
        Returns:
            競爭對手分析結果
        """
        if competitors is None:
            competitors = ['星巴克', '太平洋咖啡', '麥咖啡', 'Pret A Manger']
        
        analysis_results = []
        
        for competitor in competitors:
            query = f'{competitor} 咖啡 香港 價格 菜單 評價'
            
            results = self.search(
                query=query,
                max_results=5,
                include_answer=True
            )
            
            if results['success']:
                summary = self._summarize_competitor_data(results)
                analysis_results.append({
                    'competitor': competitor,
                    'results': results.get('results', []),
                    'summary': summary,
                    'answer': results.get('answer', '')
                })
            else:
                analysis_results.append({
                    'competitor': competitor,
                    'results': [],
                    'summary': {},
                    'error': results.get('error', '搜索失敗')
                })
        
        return {
            'success': True,
            'competitors': competitors,
            'analysis': analysis_results
        }
    
    def solve_technical_issue(self, issue: str, technology: str = 'Django') -> Dict[str, Any]:
        """
        解決技術問題
        
        Args:
            issue: 技術問題描述
            technology: 技術棧
            
        Returns:
            技術解決方案
        """
        query = f'{technology} {issue} 解決方案 最佳實踐'
        
        results = self.search(
            query=query,
            max_results=6,
            include_answer=True,
            search_depth='advanced'
        )
        
        if results['success']:
            solutions = self._extract_solutions(results)
            code_examples = self._extract_code_examples(results)
            
            results['solutions'] = solutions
            results['code_examples'] = code_examples
        
        return results
    
    def research_pricing_strategies(self) -> Dict[str, Any]:
        """
        研究價格策略
        
        Returns:
            價格策略研究結果
        """
        topics = [
            '咖啡店定價策略',
            '香港咖啡市場價格',
            '精品咖啡定價',
            '咖啡店促銷策略'
        ]
        
        all_results = []
        
        for topic in topics:
            query = f'{topic} 2024'
            
            results = self.search(
                query=query,
                max_results=4,
                include_answer=True
            )
            
            if results['success']:
                insights = self._extract_insights(results)
                all_results.append({
                    'topic': topic,
                    'results': results.get('results', []),
                    'insights': insights,
                    'answer': results.get('answer', '')
                })
        
        recommendations = self._generate_recommendations(all_results)
        
        return {
            'success': True,
            'analysis': all_results,
            'recommendations': recommendations
        }
    
    def _analyze_market_trends(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """分析市場趨勢"""
        trends = {
            'growth_areas': [],
            'challenges': [],
            'opportunities': []
        }
        
        for result in results.get('results', []):
            content = result.get('content', '').lower()
            
            if '增長' in content or '上升' in content or '增加' in content:
                trends['growth_areas'].append({
                    'title': result.get('title', ''),
                    'trend': '增長'
                })
            
            if '挑戰' in content or '困難' in content or '問題' in content:
                trends['challenges'].append({
                    'title': result.get('title', ''),
                    'challenge': '挑戰'
                })
            
            if '機會' in content or '機遇' in content or '潛力' in content:
                trends['opportunities'].append({
                    'title': result.get('title', ''),
                    'opportunity': '機會'
                })
        
        return trends
    
    def _summarize_competitor_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """總結競爭對手數據"""
        summary = {
            'price_range': self._extract_price_range(results),
            'popular_items': self._extract_popular_items(results),
            'customer_reviews': self._analyze_reviews(results)
        }
        return summary
    
    def _extract_price_range(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """提取價格範圍"""
        price_range = {
            'min': None,
            'max': None,
            'average': None,
            'currency': 'HKD'
        }
        
        # 簡單的價格提取邏輯
        for result in results.get('results', []):
            content = result.get('content', '')
            # 這裡可以實現更複雜的價格提取邏輯
            pass
        
        return price_range
    
    def _extract_popular_items(self, results: Dict[str, Any]) -> List[str]:
        """提取熱門商品"""
        popular_items = []
        
        for result in results.get('results', []):
            content = result.get('content', '').lower()
            
            # 簡單的關鍵詞匹配
            coffee_types = ['拿鐵', '卡布奇諾', '美式咖啡', '摩卡', '馥芮白']
            for coffee in coffee_types:
                if coffee in content:
                    popular_items.append(coffee)
        
        # 去重
        popular_items = list(set(popular_items))
        return popular_items[:5]  # 返回前5個
    
    def _analyze_reviews(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """分析客戶評價"""
        reviews = {
            'positive': [],
            'negative': [],
            'neutral': []
        }
        
        for result in results.get('results', []):
            content = result.get('content', '').lower()
            
            # 簡單的情感分析
            positive_words = ['好', '棒', '優秀', '推薦', '喜歡']
            negative_words = ['差', '糟糕', '不推薦', '失望', '貴']
            
            positive_count = sum(1 for word in positive_words if word in content)
            negative_count = sum(1 for word in negative_words if word in content)
            
            if positive_count > negative_count:
                reviews['positive'].append(result.get('title', ''))
            elif negative_count > positive_count:
                reviews['negative'].append(result.get('title', ''))
            else:
                reviews['neutral'].append(result.get('title', ''))
        
        return reviews
    
    def _extract_solutions(self, results: Dict[str, Any]) -> List[Dict[str, str]]:
        """提取解決方案"""
        solutions = []
        
        for result in results.get('results', []):
            content = result.get('content', '').lower()
            
            if 'solution' in content or 'fix' in content or '解決' in content:
                solutions.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'summary': result.get('content', '')[:200] + '...'
                })
        
        return solutions
    
    def _extract_code_examples(self, results: Dict[str, Any]) -> List[Dict[str, str]]:
        """提取代碼示例"""
        code_examples = []
        
        for result in results.get('results', []):
            content = result.get('content', '').lower()
            
            if 'code' in content or 'example' in content or '示例' in content:
                language = self._detect_language(content)
                code_examples.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'language': language
                })
        
        return code_examples
    
    def _detect_language(self, content: str) -> str:
        """檢測編程語言"""
        content_lower = content.lower()
        
        if 'python' in content_lower:
            return 'Python'
        elif 'javascript' in content_lower or 'js' in content_lower:
            return 'JavaScript'
        elif 'sql' in content_lower:
            return 'SQL'
        elif 'html' in content_lower:
            return 'HTML'
        elif 'css' in content_lower:
            return 'CSS'
        else:
            return 'Unknown'
    
    def _extract_insights(self, results: Dict[str, Any]) -> List[Dict[str, str]]:
        """提取洞察"""
        insights = []
        
        for result in results.get('results', []):
            content = result.get('content', '').lower()
            
            if 'price' in content or 'cost' in content or '定價' in content or '價格' in content:
                insights.append({
                    'title': result.get('title', ''),
                    'key_points': self._extract_key_points(result.get('content', ''))
                })
        
        return insights
    
    def _extract_key_points(self, content: str) -> List[str]:
        """提取關鍵點"""
        # 簡單的句子分割
        sentences = content.split('.')
        key_points = []
        
        for sentence in sentences[:5]:  # 取前5個句子
            sentence = sentence.strip()
            if len(sentence) > 20:
                key_points.append(sentence)
        
        return key_points
    
    def _generate_recommendations(self, analysis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成推薦"""
        recommendations = []
        
        for item in analysis:
            topic = item.get('topic', '')
            
            if '定價' in topic or '價格' in topic:
                recommendations.append({
                    'type': '定價策略',
                    'suggestion': '考慮採用分層定價策略，針對不同客戶群體提供不同價格選項',
                    'priority': '高',
                    'implementation': '短期 (1-2個月)'
                })
            
            if '促銷' in topic:
                recommendations.append({
                    'type': '促銷策略',
                    'suggestion': '實施會員計劃和忠誠度獎勵，提高客戶回頭率',
                    'priority': '中',
                    'implementation': '中期 (3-6個月)'
                })
            
            if '市場' in topic:
                recommendations.append({
                    'type': '市場擴展',
                    'suggestion': '考慮擴展到線上訂購和配送服務，吸引更多年輕客戶',
                    'priority': '高',
                    'implementation': '長期 (6-12個月)'
                })
        
        return recommendations