import base64
import io
import json
import os
import re
import urllib.error
import urllib.request

from pypdf import PdfReader
from PIL import Image


OCR_UNAVAILABLE_MESSAGE = '扫描版 PDF 需要 OCR 服务，当前视觉识别不可用，请稍后重试。'


def extract_pdf_text(file_path):
    reader = PdfReader(file_path)
    parts = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ''
        page_text = page_text.strip()
        if page_text:
            parts.append(f'第{page_number}页\n{page_text}')

    if not parts:
        title = (reader.metadata or {}).get('/Title')
        if title:
            parts.append(str(title))

    return '\n\n'.join(parts).strip()


def extract_pdf_content(file_path, filename='document.pdf'):
    local_text = extract_pdf_text(file_path)
    minimum_characters = int(os.getenv('PDF_OCR_MIN_TEXT_CHARACTERS', '120'))
    local_characters = _meaningful_character_count(local_text)

    if local_characters >= minimum_characters:
        return {
            'text': local_text,
            'method': 'local_text',
            'character_count': len(local_text),
            'used_vision': False,
            'warning': '',
        }

    providers = []
    if _openai_vision_enabled():
        providers.append(('openai_vision', lambda: _call_openai_pdf_vision(file_path, filename)))
    if _agnes_vision_enabled():
        providers.append(('agnes_vision', lambda: _call_agnes_pdf_vision(file_path, filename)))

    if not providers:
        raise ValueError(OCR_UNAVAILABLE_MESSAGE)

    errors = []
    for method, provider in providers:
        try:
            vision_text = provider().strip()
            if _meaningful_character_count(vision_text) < minimum_characters:
                raise RuntimeError('识别结果文字过少')
            return {
                'text': vision_text,
                'method': method,
                'character_count': len(vision_text),
                'used_vision': True,
                'warning': '',
            }
        except Exception as exc:
            errors.append(str(exc))

    detail = '；'.join(error for error in errors if error)[:360]
    suffix = f'（{detail}）' if detail else ''
    raise ValueError(f'{OCR_UNAVAILABLE_MESSAGE}{suffix}')


def _meaningful_character_count(text):
    return len(re.sub(r'\s+', '', str(text or '')))


def _openai_vision_enabled():
    if not os.getenv('OPENAI_API_KEY', '').strip():
        return False
    return os.getenv('OPENAI_PDF_VISION_ENABLED', '1').strip().lower() not in {'0', 'false', 'no'}


def _agnes_vision_enabled():
    if not os.getenv('AGNES_API_KEY', '').strip():
        return False
    return os.getenv('AGNES_PDF_VISION_ENABLED', '1').strip().lower() not in {'0', 'false', 'no'}


def _call_openai_pdf_vision(file_path, filename):
    file_size = os.path.getsize(file_path)
    maximum_size = int(os.getenv('OPENAI_PDF_MAX_BYTES', str(50 * 1024 * 1024)))
    if file_size > maximum_size:
        raise ValueError('PDF 超过视觉识别允许的文件大小。')

    with open(file_path, 'rb') as pdf_stream:
        encoded_pdf = base64.b64encode(pdf_stream.read()).decode('ascii')

    payload = {
        'model': os.getenv('OPENAI_ANALYSIS_MODEL', 'gpt-5.6'),
        'reasoning': {'effort': os.getenv('OPENAI_ANALYSIS_REASONING_EFFORT', 'low')},
        'input': [
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'input_file',
                        'filename': filename or 'document.pdf',
                        'file_data': f'data:application/pdf;base64,{encoded_pdf}',
                        'detail': os.getenv('OPENAI_PDF_DETAIL', 'low'),
                    },
                    {
                        'type': 'input_text',
                        'text': (
                            '请完整提取这份招标 PDF 中可见的中文和英文文本。按页面阅读顺序输出，'
                            '保留标题、条款编号、表格行列含义、金额、日期、资质要求和评分规则。'
                            '不要总结、解释或补充不存在的内容；无法辨认处标记为【无法辨认】。'
                        ),
                    },
                ],
            }
        ],
        'max_output_tokens': int(os.getenv('OPENAI_PDF_MAX_OUTPUT_TOKENS', '12000')),
    }
    request = urllib.request.Request(
        'https://api.openai.com/v1/responses',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f"Bearer {os.getenv('OPENAI_API_KEY', '').strip()}",
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=int(os.getenv('OPENAI_PDF_TIMEOUT', '60')),
        ) as response:
            response_payload = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'OpenAI 文件识别请求失败（{exc.code}）') from exc

    if isinstance(response_payload.get('output_text'), str):
        return response_payload['output_text']

    chunks = []
    for item in response_payload.get('output', []):
        for content in item.get('content', []):
            if isinstance(content.get('text'), str):
                chunks.append(content['text'])
    return ''.join(chunks)


def _call_agnes_pdf_vision(file_path, filename):
    page_images = _extract_scan_page_images(file_path)
    if not page_images:
        raise RuntimeError('Agnes AI 未找到可识别的扫描页图片')

    batch_size = max(1, int(os.getenv('AGNES_PDF_PAGES_PER_REQUEST', '4')))
    results = []
    for offset in range(0, len(page_images), batch_size):
        batch = page_images[offset : offset + batch_size]
        content = [
            {
                'type': 'text',
                'text': (
                    f'请完整提取扫描版招标文件“{filename or "document.pdf"}”以下页面中的可见文字。'
                    '严格按页码和阅读顺序输出，保留标题、条款编号、表格含义、金额、日期、'
                    '资质要求和评分规则。不要总结或补充；无法辨认处标记为【无法辨认】。'
                ),
            }
        ]
        for page_number, mime_type, encoded_image in batch:
            content.extend(
                [
                    {'type': 'text', 'text': f'第{page_number}页：'},
                    {
                        'type': 'image_url',
                        'image_url': {'url': f'data:{mime_type};base64,{encoded_image}'},
                    },
                ]
            )

        payload = {
            'model': os.getenv('AGNES_ANALYSIS_MODEL', 'agnes-2.0-flash'),
            'messages': [{'role': 'user', 'content': content}],
            'temperature': 0,
        }
        base_url = os.getenv('AGNES_API_BASE', 'https://apihub.agnes-ai.com/v1').rstrip('/')
        request = urllib.request.Request(
            f'{base_url}/chat/completions',
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers={
                'Authorization': f"Bearer {os.getenv('AGNES_API_KEY', '').strip()}",
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=int(os.getenv('AGNES_PDF_TIMEOUT', '90')),
            ) as response:
                response_payload = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='ignore')[:240]
            raise RuntimeError(f'Agnes AI 图片识别请求失败（{exc.code}）{detail}') from exc

        try:
            result = response_payload['choices'][0]['message']['content']
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError('Agnes AI 图片识别响应中没有文本') from exc
        if isinstance(result, list):
            result = ''.join(
                item.get('text', '') for item in result if isinstance(item, dict)
            )
        result = str(result or '').strip()
        if not result:
            raise RuntimeError('Agnes AI 图片识别响应为空')
        results.append(result)

    return '\n\n'.join(results)


def _extract_scan_page_images(file_path):
    reader = PdfReader(file_path)
    maximum_pages = max(1, int(os.getenv('AGNES_PDF_MAX_PAGES', '60')))
    maximum_bytes = int(os.getenv('AGNES_PDF_MAX_IMAGE_BYTES', str(30 * 1024 * 1024)))
    page_images = []
    total_bytes = 0

    if len(reader.pages) > maximum_pages:
        raise ValueError(f'扫描版 PDF 超过 Agnes AI 最多 {maximum_pages} 页的识别限制。')

    for page_number, page in enumerate(reader.pages, start=1):
        images = list(page.images)
        if not images:
            continue
        page_image = max(images, key=lambda item: len(item.data))
        image_bytes, mime_type = _normalise_image(page_image.image, page_image.data)
        total_bytes += len(image_bytes)
        if total_bytes > maximum_bytes:
            raise ValueError('扫描版 PDF 图片总量超过 Agnes AI 识别限制。')
        page_images.append(
            (page_number, mime_type, base64.b64encode(image_bytes).decode('ascii'))
        )

    return page_images


def _normalise_image(image, original_bytes):
    image_format = str(getattr(image, 'format', '') or '').upper()
    mime_types = {'JPEG': 'image/jpeg', 'JPG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp'}
    if image_format in mime_types:
        return original_bytes, mime_types[image_format]

    output = io.BytesIO()
    if image.mode not in {'RGB', 'L'}:
        image = image.convert('RGB')
    image.save(output, format='PNG')
    return output.getvalue(), 'image/png'
