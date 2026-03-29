from http.server import BaseHTTPRequestHandler
import json, requests, os, re

WEB_API_BASE_URL = os.environ.get('WEB_API_BASE_URL', '').rstrip('/')
LARK_APP_ID = os.environ.get('LARK_APP_ID', '')
LARK_APP_SECRET = os.environ.get('LARK_APP_SECRET', '')
LARK_BASE_URL = 'https://open.larksuite.com'

# 临时存储用户查询上下文 {open_id: [product_list]}
user_sessions = {}

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

def fetch_all_inventory():
    """获取全部库存数据"""
    all_rows = []
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
    return all_rows

def merge_products(rows):
    """合并同EAN的迪拜和沙特库存"""
    products = {}
    for row in rows:
        ean = str(row.get('ean', '')).strip()
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
        if qty is None:
            qty = 0
        if 'Dubai' in warehouse:
            products[ean]['dubai_qty'] = qty
        elif 'Saudi' in warehouse:
            products[ean]['saudi_qty'] = qty
    return list(products.values())

def search_by_ean(keyword):
    """精确EAN查询"""
    all_rows = fetch_all_inventory()
    matched = [r for r in all_rows if str(r.get('ean', '')).strip() == keyword]
    return merge_products(matched)

def search_by_model(keyword):
    """型号模糊查询：只返回包含关键词的结果"""
    resp = requests.get(
        f'{WEB_API_BASE_URL}/tables/inventory',
        params={'search': keyword, 'limit': 500},
        timeout=15
    )
    if resp.status_code != 200:
        return []
    rows = resp.json().get('data', [])

    # 严格过滤：只保留model字段中包含关键词的结果（不区分大小写）
    kw = keyword.lower()
    filtered_rows = [r for r in rows if kw in r.get('model', '').lower()]

    # 合并同EAN产品
    products = merge_products(filtered_rows)

    # 按匹配度排序
    def sort_key(p):
        model = p['model'].lower()
        if model == kw:
            return 0  # 完全匹配
        elif model.startswith(kw):
            return 1  # 开头匹配
        elif kw in model:
            return 2  # 包含匹配
        else:
            return 3
    products.sort(key=sort_key)
    return products

def format_qty(qty):
    """格式化库存数量显示（包括负数）"""
    if qty is None:
        return "—"
    if qty > 0:
        return f"✅ {qty} 件"
    elif qty < 0:
        return f"⚠️ {qty} 件"  # 负数显示
    else:
        return "❌ 无库存"

def format_product_detail(p):
    """格式化单个产品详情"""
    lines = [
        "━" * 28,
        f"📦 {p['model']}",
        f"EAN: {p['ean']}",
        f"🇦🇪 Dubai:  {format_qty(p['dubai_qty'])}",
        f"🇸🇦 Saudi:  {format_qty(p['saudi_qty'])}",
        "━" * 28
    ]
    return "\n".join(lines)

def format_search_list(keyword, products):
    """格式化搜索列表（只显示型号，不显示库存）"""
    total = len(products)
    top10 = products[:10]
    lines = [f"🔍 「{keyword}」找到 {total} 个相关产品\n"]
    lines.append("📋 请输入编号查看库存详情：\n")
    for i, p in enumerate(top10, 1):
        lines.append(f"{i}. {p['model']}")
    lines.append(f"\n💡 输入数字 1-{len(top10)} 查看详情")
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

def handle_message(open_id, keyword):
    keyword = keyword.strip()

    # 判断是否为选择编号
    if re.match(r'^\d{1,2}$', keyword):
        num = int(keyword)
        session = user_sessions.get(open_id, [])
        if session and 1 <= num <= len(session):
            return format_product_detail(session[num - 1])
        elif session:
            return f"⚠️ 请输入 1-{len(session)} 之间的数字"
        else:
            return "⚠️ 查询已过期，请重新输入产品名称或EAN码"

    # 判断是否为EAN码
    if is_ean(keyword):
        products = search_by_ean(keyword)
        if not products:
            return (
                f"❌ 未找到 EAN「{keyword}」\n\n"
                "请确认EAN码是否正确，或尝试输入型号关键词"
            )
        user_sessions[open_id] = products
        return format_product_detail(products[0])

    # 型号关键词搜索
    products = search_by_model(keyword)
    if not products:
        return (
            f"❌ 未找到与「{keyword}」相关的产品\n\n"
            "请尝试：\n"
            "• 输入完整 EAN 码（如：6937224106420）\n"
            "• 输入型号关键词（如：Zenmuse X7、Matrice 400）"
        )

    # 只有1个结果直接显示详情
    if len(products) == 1:
        user_sessions[open_id] = products
        return format_product_detail(products[0])

    # 多个结果显示编号列表
    user_sessions[open_id] = products[:10]
    return format_search_list(keyword, products)


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

            if not keyword or not open_id:
                self._respond(200, {'code': 0})
                return

            token = get_lark_token()
            reply = handle_message(open_id, keyword)
            send_reply(open_id, reply, token)

        except Exception as e:
            try:
                token = get_lark_token()
                open_id = body.get('event', {}).get('sender', {}).get(
                    'sender_id', {}).get('open_id', '')
                if open_id:
                    send_reply(open_id, "⚠️ 查询出错，请稍后重试", token)
            except Exception:
                pass

        self._respond(200, {'code': 0})

    def do_GET(self):
        self._respond(200, {'status': 'AERONEX Lark Bot is running', 'version': '1.3.0'})

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, *args):
        pass
