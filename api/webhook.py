from http.server import BaseHTTPRequestHandler
import json, requests, os, re, threading

WEB_API_BASE_URL = os.environ.get('WEB_API_BASE_URL', '').rstrip('/')
LARK_APP_ID = os.environ.get('LARK_APP_ID', '')
LARK_APP_SECRET = os.environ.get('LARK_APP_SECRET', '')
LARK_BASE_URL = 'https://open.larksuite.com'

# ✅ 修复3：user_sessions 改为带过期时间的结构，并加锁保护
# 格式: {open_id: {'products': [...], 'timestamp': time.time()}}
import time
sessions_lock = threading.Lock()
user_sessions = {}
SESSION_TTL = 300  # session 保留 5 分钟

# ✅ 修复2：event_id 去重缓存，防止 Lark 重试导致重复处理
processed_events_lock = threading.Lock()
processed_events = {}
EVENT_TTL = 60  # event_id 缓存 60 秒

def is_event_processed(event_id):
    """检查 event_id 是否已处理过，已处理返回 True"""
    if not event_id:
        return False
    now = time.time()
    with processed_events_lock:
        # 清理过期的 event_id
        expired = [k for k, v in processed_events.items() if now - v > EVENT_TTL]
        for k in expired:
            del processed_events[k]
        # 检查是否已处理
        if event_id in processed_events:
            return True
        # 标记为已处理
        processed_events[event_id] = now
        return False

def get_session(open_id):
    """获取用户 session，过期自动清除"""
    now = time.time()
    with sessions_lock:
        session = user_sessions.get(open_id)
        if session and now - session['timestamp'] < SESSION_TTL:
            return session['products']
        elif session:
            del user_sessions[open_id]
        return []

def set_session(open_id, products):
    """设置用户 session"""
    with sessions_lock:
        user_sessions[open_id] = {
            'products': products,
            'timestamp': time.time()
        }

def get_lark_token():
    resp = requests.post(
        f'{LARK_BASE_URL}/open-apis/auth/v3/tenant_access_token/internal',
        json={'app_id': LARK_APP_ID, 'app_secret': LARK_APP_SECRET},
        timeout=10
    )
    return resp.json().get('tenant_access_token', '')

def is_ean(keyword):
    return bool(re.match(r'^\d{8,14}$', keyword.strip()))

def fetch_all_inventory():
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
    all_rows = fetch_all_inventory()
    matched = [r for r in all_rows if str(r.get('ean', '')).strip() == keyword]
    return merge_products(matched)

def search_by_model(keyword):
    resp = requests.get(
        f'{WEB_API_BASE_URL}/tables/inventory',
        params={'search': keyword, 'limit': 500},
        timeout=15
    )
    if resp.status_code != 200:
        return []
    rows = resp.json().get('data', [])
    kw = keyword.lower()
    filtered_rows = [r for r in rows if kw in r.get('model', '').lower()]
    products = merge_products(filtered_rows)

    def sort_key(p):
        model = p['model'].lower()
        if model == kw:
            return 0
        elif model.startswith(kw):
            return 1
        elif kw in model:
            return 2
        else:
            return 3
    products.sort(key=sort_key)
    return products

def format_qty(qty):
    if qty is None:
        return "—"
    if qty > 0:
        return f"✅ {qty} 件"
    elif qty < 0:
        return f"⚠️ {qty} 件"
    else:
        return "❌ 无库存"

def format_product_detail(p):
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
    total = len(products)
    top10 = products[:10]
    lines = [f"🔍 「{keyword}」找到 {total} 个相关产品\n"]
    lines.append("📋 请输入编号查看库存详情：\n")
    for i, p in enumerate(top10, 1):
        lines.append(f"{i}. {p['model']}")
    lines.append(f"\n💡 输入数字 1-{len(top10)} 查看详情")
    return "\n".join(lines)

def send_reply(open_id, text, token, reply_in_group=False,
               message_id=None, chat_id=None):
    if reply_in_group and chat_id:
        requests.post(
            f'{LARK_BASE_URL}/open-apis/im/v1/messages',
            headers={'Authorization': f'Bearer {token}'},
            params={'receive_id_type': 'chat_id'},
            json={
                'receive_id': chat_id,
                'msg_type': 'text',
                'content': json.dumps({'text': text})
            },
            timeout=10
        )
    else:
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

def extract_keyword_from_group_msg(content_obj, mentions):
    text = content_obj.get('text', '')
    text = re.sub(r'@_user_\d+', '', text)
    text = text.strip()
    return text

def handle_message(open_id, keyword):
    keyword = keyword.strip()
    if not keyword:
        return None

    # 判断是否为选择编号
    if re.match(r'^\d{1,2}$', keyword):
        num = int(keyword)
        # ✅ 修复3：使用新的 get_session 方法
        session = get_session(open_id)
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
        # ✅ 修复3：使用新的 set_session 方法
        set_session(open_id, products)
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

    if len(products) == 1:
        # ✅ 修复3：使用新的 set_session 方法
        set_session(open_id, products)
        return format_product_detail(products[0])

    set_session(open_id, products[:10])
    return format_search_list(keyword, products)


def process_event(open_id, keyword, token, is_group, chat_id):
    """
    ✅ 修复1：将业务逻辑封装到独立函数，在后台线程中执行
    主线程立即返回 200，此函数异步处理查询和回复
    """
    try:
        reply = handle_message(open_id, keyword)
        if reply:
            send_reply(
                open_id=open_id,
                text=reply,
                token=token,
                reply_in_group=is_group,
                chat_id=chat_id
            )
    except Exception:
        # ✅ 修复4：异常时不再额外发送错误消息，避免重试时产生多余提示
        pass


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))

            # URL verification（立即响应，无需异步）
            if body.get('type') == 'url_verification':
                self._respond(200, {'challenge': body.get('challenge')})
                return

            # ✅ 修复2：提取 event_id 并检查是否已处理
            header = body.get('header', {})
            event_id = header.get('event_id', '')
            if is_event_processed(event_id):
                # 重复事件，直接返回 200，不处理
                self._respond(200, {'code': 0})
                return

            event = body.get('event', {})
            msg = event.get('message', {})
            sender = event.get('sender', {})

            chat_type = msg.get('chat_type', '')
            msg_type = msg.get('message_type', '')

            # 只处理私聊和群组的文本消息
            if chat_type not in ('p2p', 'group') or msg_type != 'text':
                self._respond(200, {'code': 0})
                return

            content_str = msg.get('content', '{}')
            content_obj = json.loads(content_str)
            mentions = msg.get('mentions', [])
            open_id = sender.get('sender_id', {}).get('open_id', '')
            chat_id = msg.get('chat_id', '')
            is_group = (chat_type == 'group')

            if is_group:
                text_raw = content_obj.get('text', '')
                if '@_user_' not in text_raw:
                    self._respond(200, {'code': 0})
                    return
                keyword = extract_keyword_from_group_msg(content_obj, mentions)
            else:
                keyword = content_obj.get('text', '').strip()

            if not keyword or not open_id:
                self._respond(200, {'code': 0})
                return

            # ✅ 修复1：先获取 token，然后立即返回 200
            token = get_lark_token()

            # ✅ 修复1：立即返回 200，Lark 不会重试
            self._respond(200, {'code': 0})

            # ✅ 修复1：在后台线程中异步处理查询和回复
            t = threading.Thread(
                target=process_event,
                args=(open_id, keyword, token, is_group, chat_id),
                daemon=True
            )
            t.start()

        except Exception:
            # 解析失败等异常，直接返回 200
            self._respond(200, {'code': 0})

    def do_GET(self):
        self._respond(200, {'status': 'AERONEX Lark Bot is running', 'version': '1.5.0'})

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, *args):
        pass
