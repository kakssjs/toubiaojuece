import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from tenders.services.pdf_parser import extract_pdf_content


class PdfParserTests(SimpleTestCase):
    def test_uses_local_text_without_openai_for_text_pdf(self):
        local_text = '招标文件正文' * 40

        with patch('tenders.services.pdf_parser.extract_pdf_text', return_value=local_text):
            result = extract_pdf_content('unused.pdf')

        self.assertEqual(result['method'], 'local_text')
        self.assertFalse(result['used_vision'])
        self.assertEqual(result['text'], local_text)

    def test_uses_openai_vision_for_scanned_pdf(self):
        response_payload = {
            'output': [
                {
                    'content': [
                        {'type': 'output_text', 'text': '扫描件识别出的招标正文和评分规则。' * 20},
                    ]
                }
            ]
        }
        response = MagicMock()
        response.read.return_value = json.dumps(response_payload).encode('utf-8')
        response.__enter__.return_value = response
        response.__exit__.return_value = False

        with TemporaryDirectory() as directory:
            pdf_path = Path(directory) / 'scan.pdf'
            pdf_path.write_bytes(b'%PDF-1.4 scanned document')
            with (
                patch('tenders.services.pdf_parser.extract_pdf_text', return_value=''),
                patch.dict(
                    'os.environ',
                    {
                        'OPENAI_API_KEY': 'sk-test-key-for-pdf-vision',
                        'OPENAI_API_BASE': 'https://relay.example.com/v1',
                        'OPENAI_PDF_VISION_ENABLED': '1',
                    },
                    clear=False,
                ),
                patch('tenders.services.pdf_parser.urllib.request.urlopen', return_value=response) as urlopen,
            ):
                result = extract_pdf_content(str(pdf_path), 'scan.pdf')

        self.assertEqual(result['method'], 'openai_vision')
        self.assertEqual(urlopen.call_args.args[0].full_url, 'https://relay.example.com/v1/responses')
        self.assertEqual(
            urlopen.call_args.args[0].get_header('User-agent'),
            'Mozilla/5.0 (compatible; Cebiao/1.0)',
        )
        self.assertTrue(result['used_vision'])
        self.assertIn('扫描件识别', result['text'])
        request_payload = json.loads(urlopen.call_args.args[0].data.decode('utf-8'))
        file_item = request_payload['input'][0]['content'][0]
        self.assertEqual(file_item['type'], 'input_file')
        self.assertTrue(file_item['file_data'].startswith('data:application/pdf;base64,'))

    def test_rejects_limited_local_text_when_vision_is_disabled(self):
        with (
            patch('tenders.services.pdf_parser.extract_pdf_text', return_value='文件标题'),
            patch.dict('os.environ', {'OPENAI_API_KEY': '', 'OPENAI_PDF_VISION_ENABLED': '0'}, clear=False),
        ):
            with self.assertRaisesRegex(ValueError, 'OCR'):
                extract_pdf_content('unused.pdf')

    def test_rejects_limited_local_text_when_vision_request_fails(self):
        with (
            patch('tenders.services.pdf_parser.extract_pdf_text', return_value='文件标题'),
            patch.dict(
                'os.environ',
                {'OPENAI_API_KEY': 'sk-test-key-for-pdf-vision', 'OPENAI_PDF_VISION_ENABLED': '1'},
                clear=False,
            ),
            patch('tenders.services.pdf_parser._call_openai_pdf_vision', side_effect=RuntimeError('429')),
        ):
            with self.assertRaisesRegex(ValueError, 'OCR'):
                extract_pdf_content('unused.pdf')

    def test_falls_back_to_agnes_when_openai_vision_fails(self):
        agnes_text = 'Agnes识别出的扫描招标正文、资质要求和评分规则。' * 20
        with (
            patch('tenders.services.pdf_parser.extract_pdf_text', return_value=''),
            patch.dict(
                'os.environ',
                {
                    'OPENAI_API_KEY': 'sk-test-key-for-pdf-vision',
                    'OPENAI_PDF_VISION_ENABLED': '1',
                    'AGNES_API_KEY': 'agnes-test-key',
                    'AGNES_PDF_VISION_ENABLED': '1',
                },
                clear=False,
            ),
            patch('tenders.services.pdf_parser._call_openai_pdf_vision', side_effect=RuntimeError('429')),
            patch('tenders.services.pdf_parser._call_agnes_pdf_vision', return_value=agnes_text) as agnes,
        ):
            result = extract_pdf_content('unused.pdf', 'scan.pdf')

        agnes.assert_called_once_with('unused.pdf', 'scan.pdf')
        self.assertEqual(result['method'], 'agnes_vision')
        self.assertTrue(result['used_vision'])
        self.assertEqual(result['text'], agnes_text)

    def test_rejects_scan_when_openai_and_agnes_both_fail(self):
        with (
            patch('tenders.services.pdf_parser.extract_pdf_text', return_value='文件标题'),
            patch.dict(
                'os.environ',
                {
                    'OPENAI_API_KEY': 'sk-test-key-for-pdf-vision',
                    'OPENAI_PDF_VISION_ENABLED': '1',
                    'AGNES_API_KEY': 'agnes-test-key',
                    'AGNES_PDF_VISION_ENABLED': '1',
                },
                clear=False,
            ),
            patch('tenders.services.pdf_parser._call_openai_pdf_vision', side_effect=RuntimeError('429')),
            patch('tenders.services.pdf_parser._call_agnes_pdf_vision', side_effect=RuntimeError('503')),
        ):
            with self.assertRaisesRegex(ValueError, 'OCR'):
                extract_pdf_content('unused.pdf')
