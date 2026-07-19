import os
import re
from pathlib import Path

from vercel.blob import BlobClient


BLOB_PATH_PREFIX = 'tender-documents/'
CLIENT_BLOB_PATH_PREFIX = 'client-tender-documents/'


def blob_storage_configured():
    return bool(os.getenv('BLOB_READ_WRITE_TOKEN', '').strip())


def persist_pdf(file_path, original_name, project_id):
    if not blob_storage_configured():
        return {
            'backend': 'local',
            'persistent': not bool(os.getenv('VERCEL')),
            'pathname': str(file_path),
            'warning': '对象存储未配置，文件仅保存在当前运行环境。' if os.getenv('VERCEL') else '',
        }

    filename = _safe_pdf_name(original_name)
    pathname = f'{BLOB_PATH_PREFIX}{project_id}/{filename}'
    client = BlobClient(token=os.getenv('BLOB_READ_WRITE_TOKEN', '').strip())
    try:
        with open(file_path, 'rb') as pdf_stream:
            result = client.put(
                pathname,
                pdf_stream.read(),
                access='private',
                content_type='application/pdf',
                add_random_suffix=True,
                cache_control_max_age=3600,
            )
    finally:
        client.close()

    return {
        'backend': 'vercel_blob',
        'persistent': True,
        'pathname': result.pathname,
        'warning': '',
    }


def read_private_blob(pathname):
    if not blob_storage_configured():
        raise RuntimeError('对象存储凭据未配置。')

    client = BlobClient(token=os.getenv('BLOB_READ_WRITE_TOKEN', '').strip())
    try:
        result = client.get(pathname, access='private', use_cache=True)
    finally:
        client.close()
    if result is None:
        raise FileNotFoundError('对象存储中未找到该文件。')
    return result.content


def is_blob_path(pathname):
    value = str(pathname or '')
    return value.startswith(BLOB_PATH_PREFIX) or value.startswith(CLIENT_BLOB_PATH_PREFIX)


def is_client_blob_path(pathname):
    return str(pathname or '').startswith(CLIENT_BLOB_PATH_PREFIX)


def _safe_pdf_name(filename):
    source = Path(str(filename or 'document.pdf')).name
    stem = Path(source).stem[:28]
    safe_stem = re.sub(r'[^A-Za-z0-9._-]+', '-', stem).strip('-._') or 'document'
    return f'{safe_stem}.pdf'
