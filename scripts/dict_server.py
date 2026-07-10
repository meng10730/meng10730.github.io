# -*- coding: utf-8 -*-
import sqlite3
import re
import os
import json
import random
from urllib.parse import parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

PORT = 5001
db_path = os.environ.get("CLASSICAL_DICT_DB", r"c:\workspace\資料庫蒐集\dict_revised_2015_20260325\dict_revised.db")

COMMON_SIMPLE_WORDS = {"冷", "寒", "涼", "熱", "溫", "冰", "風", "秋", "落", "葉", "月", "光", "獨", "空", "紅", "赤", "靜", "幽", "深", "寂", "暗", "破", "敗", "荒", "廢"}

ASSOCIATION_EXPANSIONS = {
    "照": ["照", "映", "臨", "吐", "耀", "光", "篩", "照臨", "吐輝"],
    "遮": ["遮", "蔽", "隱", "翳", "藏", "護", "掩", "蔽月"],
    "揮": ["揮", "舞", "動", "拂", "擊", "斬", "劈", "持", "按"],
    "吹": ["吹", "拂", "襲", "掠", "送", "颳", "吼", "嘯"],
    "飄": ["飄", "落", "舞", "旋", "飛", "灑", "紛", "零"]
}

RANDOM_CONCEPTS = [
    "月", "風", "雨", "雪", "霜", "露", "霧", "雲", "雷", "電",
    "寒", "冷", "涼", "幽", "深", "寂", "暗", "影", "空", "獨",
    "劍", "刀", "琴", "簫", "棋", "書", "畫", "茶", "酒", "香",
    "古", "荒", "廢", "破", "老", "枯", "殘", "衰", "塵", "埃",
    "紅", "赤", "青", "黛", "絳", "蒨", "綠", "蒼", "白", "素",
    "山", "水", "石", "竹", "松", "梅", "蘭", "季", "荷", "蓮",
    "神", "佛", "仙", "鬼", "魔", "妖", "道", "禪", "寺", "廟"
]

def load_exclusions():
    exclusions = set()
    paths_to_check = [
        os.path.join(os.getcwd(), "exclude_list.txt"),
        os.path.join(os.getcwd(), ".agents", "exclude_list.txt"),
        r"c:\workspace\資料庫蒐集\dict_revised_2015_20260325\exclude_list.txt",
        r"c:\workspace\資料庫蒐集\classical_writing_helper\exclude_list.txt"
    ]
    for path in paths_to_check:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        w = line.strip()
                        if w:
                            exclusions.add(w)
                break
            except:
                pass
    return exclusions

def space_tokenize(text):
    if not text:
        return ""
    chars = []
    for char in text:
        if re.match(r'[\u4e00-\u9fa5a-zA-Z0-9]', char):
            chars.append(char + " ")
        else:
            chars.append(char)
    return "".join(chars).strip()

def extract_citation(explanation, book_name=None):
    citation_pattern = r'(《[^》]+》[：:][「『].*?[」』])'
    citation_pattern_2 = r'(〈[^〉]+〉[：:][「『].*?[」』])'
    
    citations = re.findall(citation_pattern, explanation)
    citations_2 = re.findall(citation_pattern_2, explanation)
    all_citations = citations + citations_2
    
    if all_citations:
        if book_name:
            for cit in all_citations:
                if book_name in cit:
                    if len(cit) > 60:
                        match = re.search(r'[。；]', cit)
                        if match:
                            cit = cit[:match.start() + 1]
                    return cit
                    
        cit = all_citations[0]
        if len(cit) > 60:
            match = re.search(r'[。；]', cit)
            if match:
                cit = cit[:match.start() + 1]
        return cit
        
    example_pattern = r'(如[：:][「『].*?[」』])'
    examples = re.findall(example_pattern, explanation)
    if examples:
        return examples[0]
        
    clean_exp = re.sub(r'\d+\.', '', explanation).strip()
    return clean_exp[:40] + "..." if len(clean_exp) > 40 else clean_exp

def search_concept(core_synonyms, peripheral_associations, pos_filter=None, common_mode='y', limit=150):
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    exclusions = load_exclusions()
    
    core_match = " OR ".join([f'"{space_tokenize(w)}"' for w in core_synonyms if w])
    
    expanded_associations = []
    for w in peripheral_associations:
        if w in ASSOCIATION_EXPANSIONS:
            expanded_associations.extend(ASSOCIATION_EXPANSIONS[w])
        else:
            expanded_associations.append(w)
            
    if expanded_associations:
        peripheral_match = " OR ".join([f'"{space_tokenize(w)}"' for w in expanded_associations if w])
    else:
        peripheral_match = ""
        
    if core_match and peripheral_match:
        full_match_query = f"({core_match}) AND ({peripheral_match})"
    elif core_match:
        full_match_query = core_match
    elif peripheral_match:
        full_match_query = peripheral_match
    else:
        return []
    
    pos_condition = "AND w.pos = ?" if pos_filter else ""
    
    sql = f"""
    SELECT 
        w.word, 
        w.bopomofo, 
        w.pos, 
        w.explanation, 
        w.word_count,
        w.radical,
        f.rank as fts_rank,
        (
            CASE 
                WHEN w.explanation LIKE ? OR w.explanation LIKE ? OR w.explanation LIKE ? OR w.explanation LIKE ? OR w.explanation LIKE ? THEN -150
                ELSE 0
            END +
            CASE 
                WHEN SUBSTR(w.explanation, 1, 15) LIKE ? THEN -80
                ELSE 0
            END +
            CASE 
                WHEN (w.radical IN ('刀', '刂', '金', '釒')) AND (? LIKE '%劍%' OR ? LIKE '%刀%' OR ? LIKE '%兵%') THEN -50
                ELSE 0
            END +
            CASE 
                WHEN w.explanation NOT LIKE ? AND w.explanation LIKE ? THEN 60
                ELSE 0
            END
        ) as semantic_score,
        (CASE WHEN w.explanation LIKE ? OR w.explanation LIKE ? OR w.explanation LIKE ? OR w.explanation LIKE ? OR w.explanation LIKE ? THEN 1 ELSE 0 END) as is_alias
    FROM words w
    JOIN words_fts f ON w.id = f.rowid
    WHERE words_fts MATCH ? {pos_condition}
    ORDER BY 
        semantic_score ASC,
        fts_rank ASC
    LIMIT ?
    """
    
    first_query_word = core_synonyms[0] if core_synonyms else ""
    def_like_param = f"%{first_query_word}%"
    
    alias_param1 = f"%代稱%{first_query_word}%"
    alias_param2 = f"%借指%{first_query_word}%"
    alias_param3 = f"%代指%{first_query_word}%"
    alias_param4 = f"%{first_query_word}%別稱%"
    alias_param5 = f"%{first_query_word}%古稱%"
    
    params = [
        alias_param1, alias_param2, alias_param3, alias_param4, alias_param5,
        def_like_param, 
        first_query_word, first_query_word, first_query_word,
        f"%{first_query_word}%《%", 
        f"%《%{first_query_word}%》%", 
        alias_param1, alias_param2, alias_param3, alias_param4, alias_param5,
        full_match_query
    ]
    if pos_filter:
        params.append(pos_filter)
    params.append(limit)
    
    try:
        cursor.execute(sql, tuple(params))
        results = cursor.fetchall()
        
        grouped_results = {}
        for row in results:
            word, bopomofo, pos, explanation, word_count, radical, fts_rank, semantic_score, is_alias = row
            
            if common_mode == 'h' and word in COMMON_SIMPLE_WORDS:
                continue
            if word in exclusions:
                continue
                
            clean_bopomofo = bopomofo.replace(" ", "")
            citation = extract_citation(explanation, book_name=first_query_word)
            clean_exp = explanation.replace(citation, "").strip()
            clean_exp = re.sub(r'^\d+\.', '', clean_exp).strip()
            clean_exp = clean_exp[:65] + "..." if len(clean_exp) > 65 else clean_exp
            
            is_simple = 0
            if common_mode == 'y' and (word in COMMON_SIMPLE_WORDS or "如：" in explanation[:30]):
                is_simple = 1
                
            length_key = 1 if is_alias == 1 else len(word)
            
            if word not in grouped_results:
                grouped_results[word] = {
                    "word": word,
                    "bopomofo": clean_bopomofo,
                    "is_simple": is_simple,
                    "length_key": length_key,
                    "definitions": []
                }
            grouped_results[word]["definitions"].append({
                "pos": pos or "[無]",
                "citation": citation,
                "explanation": clean_exp
            })
            
        sorted_results = sorted(
            grouped_results.values(),
            key=lambda x: (x["is_simple"], x["length_key"])
        )
        return sorted_results
    except Exception as e:
        print("API SQL Error:", e)
        return []
    finally:
        conn.close()

def search_book(book_name, query_word=None, pos_filter=None, limit=150):
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    exclusions = load_exclusions()
    
    conditions = ["(explanation LIKE ? OR explanation LIKE ? OR explanation LIKE ?)"]
    params = [f"%《{book_name}%》%", f"%〈{book_name}%〉%", f"%{book_name}%"]
    
    if query_word:
        conditions.append("explanation LIKE ?")
        params.append(f"%{query_word}%")
        
    if pos_filter:
        conditions.append("pos = ?")
        params.append(pos_filter)
        
    where_clause = " AND ".join(conditions)
    
    sql = f"""
    SELECT 
        word, 
        bopomofo, 
        pos, 
        explanation, 
        word_count
    FROM words
    WHERE {where_clause}
    ORDER BY word_count ASC
    LIMIT ?
    """
    params.append(limit)
    
    try:
        cursor.execute(sql, tuple(params))
        results = cursor.fetchall()
        
        grouped_results = {}
        for row in results:
            word, bopomofo, pos, explanation, word_count = row
            if word in exclusions:
                continue
                
            clean_bopomofo = bopomofo.replace(" ", "")
            citation = extract_citation(explanation, book_name=book_name)
            clean_exp = explanation.replace(citation, "").strip()
            clean_exp = re.sub(r'^\d+\.', '', clean_exp).strip()
            clean_exp = clean_exp[:65] + "..." if len(clean_exp) > 65 else clean_exp
            
            is_simple = 1 if (word in COMMON_SIMPLE_WORDS or "如：" in explanation[:30]) else 0
            
            if word not in grouped_results:
                grouped_results[word] = {
                    "word": word,
                    "bopomofo": clean_bopomofo,
                    "is_simple": is_simple,
                    "definitions": []
                }
            grouped_results[word]["definitions"].append({
                "pos": pos or "[無]",
                "citation": citation,
                "explanation": clean_exp
            })
            
        sorted_results = sorted(
            grouped_results.values(),
            key=lambda x: (x["is_simple"], len(x["word"]))
        )
        return sorted_results
    except Exception as e:
        print("API Book SQL Error:", e)
        return []
    finally:
        conn.close()

def search_synonyms(query_word):
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    exclusions = load_exclusions()
    
    sql = "SELECT word, bopomofo, similar_words, opposite_words, explanation FROM words WHERE word = ?"
    try:
        cursor.execute(sql, (query_word,))
        rows = cursor.fetchall()
        results = []
        for row in rows:
            word, bopomofo, similar, opposite, explanation = row
            if word in exclusions:
                continue
            results.append({
                "word": word,
                "bopomofo": bopomofo.replace(" ", "") if bopomofo else "",
                "similar": similar.strip() if similar else "",
                "opposite": opposite.strip() if opposite else "",
                "explanation": explanation[:120] + "..." if len(explanation) > 120 else explanation
            })
        return results
    except Exception as e:
        print("API Synonym SQL Error:", e)
        return []
    finally:
        conn.close()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class APIHandler(BaseHTTPRequestHandler):
    def end_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_cors_headers()

    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == '/api/query':
            params = parse_qs(parsed_url.query)
            mode = params.get('mode', ['1'])[0]
            
            data = []
            
            if mode == '1':
                core = params.get('core', [''])[0].strip()
                assoc = params.get('assoc', [''])[0].strip()
                pos = params.get('pos', [None])[0]
                common = params.get('common', ['y'])[0]
                
                core_list = core.split() if core else []
                assoc_list = assoc.split() if assoc else []
                
                if core_list:
                    data = search_concept(core_list, assoc_list, pos_filter=pos, common_mode=common)
            
            elif mode == '2':
                book = params.get('book', [''])[0].strip()
                query = params.get('query', [None])[0]
                pos = params.get('pos', [None])[0]
                
                if book:
                    data = search_book(book, query_word=query, pos_filter=pos)
            
            elif mode == '3':
                concept = random.choice(RANDOM_CONCEPTS)
                data = {
                    "concept": concept,
                    "results": search_concept([concept], [], pos_filter=None, common_mode='y')
                }
            
            elif mode == '4':
                word = params.get('word', [''])[0].strip()
                if word:
                    data = search_synonyms(word)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_cors_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"API Endpoint Not Found")

def run():
    print(f"Starting Classical Dict API server on port {PORT}...")
    print(f"Using database: {db_path}")
    if not os.path.exists(db_path):
        print("WARNING: SQLite database file not found! Queries will return empty results.")
    server_address = ('', PORT)
    httpd = ThreadedHTTPServer(server_address, APIHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping API server...")
        httpd.server_close()

if __name__ == '__main__':
    run()
