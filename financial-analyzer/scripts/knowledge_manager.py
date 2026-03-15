#!/usr/bin/env python3
"""
知识库更新工具 - 财务分析知识库版本管理
用于更新 knowledge_base.json 中的知识条目
"""

import datetime
import json
import os
from typing import Dict, List, Any, Optional

class KnowledgeBaseManager:
    def __init__(self, kb_path: str):
        self.kb_path = kb_path
        self.kb = self._load()
    
    def _load(self) -> Dict:
        """加载知识库"""
        with open(self.kb_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save(self):
        """保存知识库"""
        with open(self.kb_path, 'w', encoding='utf-8') as f:
            json.dump(self.kb, f, ensure_ascii=False, indent=2)
    
    def get_version(self) -> str:
        """获取当前版本"""
        return self.kb['metadata']['version']
    
    def add_knowledge_source(self, name: str, summary: str, kb_type: str = "case_study") -> str:
        """添加知识来源"""
        source_id = f"source_{len(self.kb['knowledge_sources']) + 1:03d}"
        source = {
            "id": source_id,
            "name": name,
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "type": kb_type,
            "summary": summary
        }
        self.kb['knowledge_sources'].append(source)
        return source_id
    
    def add_interest_debt_type(self, debt_type: str, is_interest: bool, 
                                reason: str, source: str = None,
                                identification: str = None, note: str = None):
        """添加有息债务类型判定"""
        target_list = "included" if is_interest else "excluded"
        code = f"{'IBD' if is_interest else 'EXC'}_{len(self.kb['knowledge']['interest_bearing_debt']['criteria'][target_list]) + 1:03d}"
        
        entry = {
            "type": debt_type,
            "code": code,
            "interest": is_interest,
            "reason": reason
        }
        if source:
            entry["source"] = source
        if identification:
            entry["identification"] = identification
        if note:
            entry["note"] = note
        
        self.kb['knowledge']['interest_bearing_debt']['criteria'][target_list].append(entry)
        return code
    
    def add_note_extraction_tip(self, section: str, name: str, focus: str, importance: str = "中"):
        """添加附注提取技巧"""
        section_num = section.replace("#", "")
        code = f"NOTE_{section_num:03d}"
        
        self.kb['knowledge']['notes_extraction']['key_sections'][section] = {
            "name": name,
            "importance": importance,
            "focus": focus,
            "code": code
        }
        return code
    
    def add_common_mistake(self, description: str, correction: str, example: str = None) -> str:
        """添加常见错误"""
        mistake_id = f"MST_{len(self.kb['knowledge']['common_mistakes']['mistakes']) + 1:03d}"
        
        entry = {
            "id": mistake_id,
            "description": description,
            "correction": correction
        }
        if example:
            entry["example"] = example
        
        self.kb['knowledge']['common_mistakes']['mistakes'].append(entry)
        return mistake_id
    
    def update_version(self, changes: List[str], source_ids: List[str]):
        """更新版本"""
        # 解析版本号
        current = self.kb['metadata']['version']
        major, minor, patch = map(int, current.split('.'))
        new_version = f"{major}.{minor + 1}.{patch}"
        
        # 更新元数据
        self.kb['metadata']['version'] = new_version
        self.kb['metadata']['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 添加版本历史
        self.kb['version_history'].append({
            "version": new_version,
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "changes": changes,
            "knowledge_sources": source_ids
        })
        
        self._save()
        return new_version
    
    def search_by_keyword(self, keyword: str) -> List[Dict]:
        """关键词搜索"""
        results = []
        keyword = keyword.lower()
        
        # 搜索有息债务判定
        for item in self.kb['knowledge']['interest_bearing_debt']['criteria']['included']:
            if keyword in item['type'].lower() or keyword in item.get('reason', '').lower():
                results.append({"section": "included", "item": item})
        
        for item in self.kb['knowledge']['interest_bearing_debt']['criteria']['excluded']:
            if keyword in item['type'].lower() or keyword in item.get('reason', '').lower():
                results.append({"section": "excluded", "item": item})
        
        # 搜索欺诈识别
        if 'fraud_detection' in self.kb['knowledge']:
            for item in self.kb['knowledge']['fraud_detection'].get('signals', []):
                if keyword in item.get('signal', '').lower() or keyword in item.get('problem', '').lower():
                    results.append({"section": "fraud_detection", "item": item})
        
        return results
    
    def print_summary(self):
        """打印知识库摘要"""
        print(f"=== 财务分析知识库 ===")
        print(f"版本: {self.kb['metadata']['version']}")
        print(f"更新: {self.kb['metadata']['last_updated']}")
        print(f"来源: {self.kb['metadata'].get('source', 'N/A')}")
        print(f"知识来源: {len(self.kb['knowledge_sources'])}个")
        
        included = len(self.kb['knowledge']['interest_bearing_debt']['criteria']['included'])
        excluded = len(self.kb['knowledge']['interest_bearing_debt']['criteria']['excluded'])
        print(f"有息债务判定: {included}项(含) / {excluded}项(不含)")
        
        # 指标统计
        solvency_st = len(self.kb['knowledge']['indicators']['solvency']['short_term'])
        solvency_lt = len(self.kb['knowledge']['indicators']['solvency']['long_term'])
        print(f"偿债指标: {solvency_st + solvency_lt}项")
        
        profitability = len(self.kb['knowledge']['indicators']['profitability'])
        print(f"盈利指标: {profitability}项")
        
        cashflow = len(self.kb['knowledge']['indicators']['cashflow']['debt_coverage'])
        print(f"现金流指标: {cashflow}项")
        
        leverage = len(self.kb['knowledge']['indicators']['leverage']['core'])
        print(f"杠杆指标: {leverage}项")
        
        # 欺诈识别
        if 'fraud_detection' in self.kb['knowledge']:
            signals = len(self.kb['knowledge']['fraud_detection']['signals'])
            print(f"欺诈识别信号: {signals}项")

    def validate_pending_updates(self, pending_updates_path: str) -> List[Dict[str, Any]]:
        """校验 pending_updates.json 的候选项元数据是否完整"""
        required_fields = [
            "source",
            "evidence",
            "applicable_scope",
            "status",
            "introduced_in",
            "confidence",
        ]

        with open(pending_updates_path, 'r', encoding='utf-8') as f:
            pending_updates = json.load(f)

        issues = []
        for index, item in enumerate(pending_updates.get('items', []), start=1):
            missing_fields = [field for field in required_fields if field not in item or item.get(field) in (None, "", [])]
            if missing_fields:
                issues.append({
                    "index": index,
                    "title": item.get("title", f"item_{index}"),
                    "missing_fields": missing_fields,
                })

        return issues

    def summarize_pending_updates(self, pending_updates_path: str) -> Dict[str, Any]:
        """汇总 pending_updates.json 中的候选项分布"""
        with open(pending_updates_path, 'r', encoding='utf-8') as f:
            pending_updates = json.load(f)

        type_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}
        for item in pending_updates.get('items', []):
            item_type = item.get("type", "unknown")
            status = item.get("status", "unknown")
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "generated_at": pending_updates.get("metadata", {}).get("generated_at", ""),
            "item_count": len(pending_updates.get("items", [])),
            "type_counts": type_counts,
            "status_counts": status_counts,
        }


def main():
    """示例用法"""
    # 知识库在上一级目录
    kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'knowledge_base.json')
    manager = KnowledgeBaseManager(kb_path)
    
    # 打印摘要
    manager.print_summary()
    
    # 搜索示例
    print("\n=== 搜索'融资租赁' ===")
    results = manager.search_by_keyword("融资租赁")
    for r in results:
        print(f"- [{r['section']}] {r['item']['type']}: {r['item'].get('reason', '')}")


if __name__ == "__main__":
    main()
