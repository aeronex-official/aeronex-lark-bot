from http.server import BaseHTTPRequestHandler
import json, requests, os, re

WEB_API_BASE_URL = os.environ.get('WEB_API_BASE_URL', '').rstrip('/')
LARK_APP_ID = os.environ.get('LARK_APP_ID', '')
LARK_APP_SECRET = os.environ.get('LARK_APP_SECRET', '')
LARK_BASE_URL = 'https://open.larksuite.com'

def get_lark_token():
    resp = requests.post(
        f'{LARK_BASE_URL}/open-apis/auth/v3/tenant_access_token/internal',
        json={'app_id': LARK_APP_ID, 'app_secret': LARK_APP_SECRET},
        timeout=10
    )
    return resp.json().get('tenant_access_token', '')

def is_ean(keyword):
    """判断是否为EAN码（纯数字，8-14位）"""
    return bool(re.match(r'^\d{8,14}$', keyword.strip()))

def search_inventory(keyword):
    keyword = keyword.strip()
    all_rows = []

    if is_ean(keyword):
        # EAN精确查询：获取所有数据后精确匹配
        page = 1
        while True:
            resp = requests.get(
                f'{WEB_API_BASE_URL}/tables/inventory',
                params={'page': page, 'limit': 500},
                timeout=15
            )
            if resp.status_code != 200:
                break
            data = resp.json()
            rows = data.get('data', [])
            all_rows.extend(rows)
            if len(rows) < 500:
                break
            page += 1

        # 精确匹配EAN
        matched = [r for r in all_rows if str(r.get('ean', '')).strip() == keyword]
    else:
        # 型号关键词搜索
        resp = requests.get(
            f'{WEB_API_BASE_URL}/tables/inventory',
            params={'search': keyword, 'limit': 100},
            timeout=15
        )
        if resp.status_code != 200:
            return []
        matched = resp.json().get('data', [])

        # 按匹配度排序：完全匹配 > 开头匹配 > 包含匹配
        keyword_lower = keyword.lower()
        def sort_key(r):
            model = r.get('model', '').lower()
            if model == keyword_lower:
                return 0  # 完全匹配
            elif model.startswith(keyword_lower):
                return 1  # 开头匹配
            elif keyword_lower in model:
                return 2  # 包含匹配
            else:
                return 3  # 其他
        matched.sort(key=sort_key)

    # 合并同一EAN的两个仓库数据
    products = {}
    for row in matched:
        ean = row.get('ean', '')
        if not ean:
            continue
        if ean not in products:
            products[ean] = {
                'ean': ean,
                'model': row.get('model', ''),
                'dubai_qty': None,
                'saudi_qty': None
            }
        warehouse = row.get('warehouse', '')
        qty = row.get('available_qty', 0)
        if 'Dubai' in warehouse:
            products[ean]['dubai_qty'] = qty
        elif 'Saudi' in warehouse:
            products[ean]['saudi_qty'] = qty

    return list(products.values())

def format_reply(keyword, products):
    if not products:
        if is_ean(keyword):
            return (
                f"❌ 未找到 EAN「{keyword}」\n\n"
                "请确认EAN码是否正确，或尝试输入型号关键词查询"
            )
        return (
            f"❌ 未找到与「{keyword}」相关的产品\n\n"
            "请尝试：\n"
            "• 输入完整 EAN 码（如：6937224106420）\n"
            "• 输入型号关键词（如：Zenmuse X7、Matrice 400）"
        )

    if len(products) > 5:
        # 显示产品名称列表供用户选择
        lines = [f"⚠️ 找到 {len(products)} 个相关产品，请输入更精确的关键词\n\n📋 前10个结果："]
        for p in products[:10]:
            dubai = f"🇦🇪{p['dubai_qty']}件" if p['dubai_qty'] else "🇦🇪—"
            saudi = f"🇸🇦{p['saudi_qty']}件" if p['saudi_qty'] else "🇸🇦—"
            lines.append(f"• {p['model']} ({dubai} {saudi})")
        return "\n".join(lines)

    lines = [f"🔍 「{keyword}」查询结果：\n", "━" * 28]
    for p in products:
        dubai_qty = p['dubai_qty']
        saudi_qty = p['saudi_qty']
        dubai_str = "—" if dubai_qty is None else (f"✅ {dubai_qty} 件" if dubai_qty > 0 else "❌ 无库存")
        saudi_str = "—" if saudi_qty is None else (f"✅ {saudi_qty} 件" if saudi_qty > 0 else "❌ 无库存")
        lines.extend([
            f"📦 {p['model']}",
            f"EAN: {p['ean']}",
            f"🇦🇪 Dubai:  {dubai_str}",
            f"🇸🇦 Saudi:  {saudi_str}",
            "━" * 28
        ])
    return "\n".join(lines)

def send_reply(open_id, text, token):
    requests.post(
        f'{LARK_BASE_URL}/open-apis/im/v1/messages',
        headers={'Authorization': f'Bearer {token}'},
        params={'receive_id_type': 'open_id'},
        json={
            'receive_id': open_id,
            'msg_type': 'text',
            'content': json.dumps({'text': text})
        },
        timeout=10
    )

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = {}
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))

            if body.get('type') == 'url_verification':
                self._respond(200, {'challenge': body.get('challenge')})
                return

            event = body.get('event', {})
            msg = event.get('message', {})
            sender = event.get('sender', {})

            if msg.get('chat_type') != 'p2p' or msg.get('message_type') != 'text':
                self._respond(200, {'code': 0})
                return

            content = json.loads(msg.get('content', '{}'))
            keyword = content.get('text', '').strip()
            open_id = sender.get('sender_id', {}).get('open_id', '')

            if not keyword or not open_id or keyword.startswith('/'):
                self._respond(200, {'code': 0})
                return

            token = get_lark_token()
            products = search_inventory(keyword)
            reply = format_reply(keyword, products)
            send_reply(open_id, reply, token)

        except Exception as e:
            try:
                token = get_lark_token()
                open_id = body.get('event', {}).get('sender', {}).get('sender_id', {}).get('open_id', '')
                if open_id:
                    send_reply(open_id, f"⚠️ 查询出错，请稍后重试", token)
            except Exception:
                pass

        self._respond(200, {'code': 0})

    def do_GET(self):
        self._respond(200, {'status': 'AERONEX Lark Bot is running', 'version': '1.1.0'})

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, *args):
        pass

