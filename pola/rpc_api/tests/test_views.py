import io
import json

import requests
from django.test import override_settings
from test_plus.test import TestCase

from ai_pics.factories import AIAttachmentFactory
from ai_pics.models import AIAttachment, AIPics
from product.factories import ProductFactory
from product.models import Product
from report.factories import ReportFactory
from report.models import Attachment, Report


class JsonRequestMixin:
    def json_request(self, url, data=None, **kwargs):
        body = json.dumps(data)
        return self.client.post(url, body, content_type="application/json", **kwargs)


def _create_image(width=100, height=None, color='blue', image_format='JPEG', image_palette='RGB'):
    # ImageField (both django's and factory_boy's) require PIL.
    # Try to import it along one of its known installation paths.
    from PIL import Image

    height = height or width

    thumb_io = io.BytesIO()
    with Image.new(image_palette, (width, height), color) as thumb:
        thumb.save(thumb_io, format=image_format)
    return thumb_io.getvalue()


class TestGetAiPics(TestCase):
    url = '/a/v3/get_ai_pics'

    @override_settings(AI_SHARED_SECRET='good-secret')
    def test_should_block_on_missing_secret(self):
        response = self.client.post(self.url)
        self.assertEqual(403, response.status_code)

    @override_settings(AI_SHARED_SECRET='good-secret')
    def test_should_block_on_invalid_secret(self):
        response = self.client.post(self.url, {'shared_secret': 'invalid-secret'})
        self.assertEqual(403, response.status_code)

    @override_settings(AI_SHARED_SECRET='good-secret')
    def test_should_return_empty_set(self):
        response = self.client.post(self.url, {'shared_secret': 'good-secret'})
        self.assertEqual(200, response.status_code)
        self.assertEqual({'aipics': []}, response.json())

    @override_settings(AI_SHARED_SECRET='good-secret')
    def test_should_return_one_item(self):
        ai_attachment = AIAttachmentFactory(ai_pics__is_valid=True)
        response = self.client.post(self.url, {'shared_secret': 'good-secret'})
        self.assertEqual(200, response.status_code)
        expected_response = {
            'aipics': [
                {
                    'ai_pics_id': ai_attachment.ai_pics.pk,
                    'code': ai_attachment.ai_pics.product.code,
                    'company_id': ai_attachment.ai_pics.product.company_id,
                    'product_name': ai_attachment.ai_pics.product.name,
                    'url': ai_attachment.get_absolute_url(),
                }
            ]
        }
        self.assertEqual(expected_response, response.json())

    @override_settings(AI_SHARED_SECRET='good-secret')
    def test_should_ignore_invalid(self):
        AIAttachmentFactory(ai_pics__is_valid=False)

        response = self.client.post(self.url, {'shared_secret': 'good-secret'})

        self.assertEqual(200, response.status_code)
        self.assertEqual(len(response.json()['aipics']), 0)

    @override_settings(AI_SHARED_SECRET='good-secret', AI_PICS_PAGE_SIZE=10)
    def test_should_support_pagination(self):
        AIAttachmentFactory.create_batch(15, ai_pics__is_valid=True)
        self.assertEqual(AIAttachment.objects.count(), 15)

        response = self.client.post(self.url, {'shared_secret': 'good-secret'})

        self.assertEqual(200, response.status_code)
        self.assertEqual(len(response.json()['aipics']), 10)

        response = self.client.post(self.url + "?page=1", {'shared_secret': 'good-secret'})

        self.assertEqual(200, response.status_code)
        self.assertEqual(len(response.json()['aipics']), 5)


class TestAddAiPics(TestCase, JsonRequestMixin):
    url = '/a/v3/add_ai_pics'

    def test_should_create_simple_report(self):
        p = ProductFactory.create(ai_pics_count=0)

        response = self.json_request(
            self.url + "?device_id=TEST-DEVICE-ID",
            data={
                'product_id': p.pk,
                'files_count': 1,
                'file_ext': "png",
                "mime_type": 'image/jpeg',
                'original_width': 1000,
                'original_height': 2000,
                'width': 100,
                'height': 200,
                'device_name': 'TEST-device',
                'flash_used': True,
                'was_portrait': False,
            },
        )

        self.assertEqual(200, response.status_code)
        response_data = response.json()
        self.assertEqual(len(response_data['signed_requests']), 1)
        signed_url: str = response_data['signed_requests'][0]
        self.assertTrue(signed_url.startswith("http://minio:9000"))

        # Valid signed URL
        response = requests.put(
            signed_url, data=_create_image(), headers={"x-amz-acl": "public-read", 'Content-Type': 'image/jpeg'}
        )
        self.assertEqual(200, response.status_code, response.text)

        # Assert AIPics
        self.assertEqual(AIPics.objects.count(), 1)
        ai_pics: AIPics = AIPics.objects.first()
        self.assertEqual(p.pk, ai_pics.product_id)
        self.assertEqual("TEST-DEVICE-ID", ai_pics.client)
        self.assertEqual(1000, ai_pics.original_width)
        self.assertEqual(2000, ai_pics.original_height)
        self.assertEqual(100, ai_pics.width)
        self.assertEqual(200, ai_pics.height)
        self.assertEqual(True, ai_pics.flash_used)
        self.assertEqual(False, ai_pics.was_portrait)

        # Assert AIAttachment
        self.assertEqual(1, AIAttachment.objects.count())
        ai_attachment: AIAttachment = AIAttachment.objects.first()
        self.assertTrue(ai_attachment.attachment.name.endswith("png"))
        self.assertEqual(0, ai_attachment.file_no)
        self.assertEqual(200, requests.get(ai_attachment.get_absolute_url()).status_code)

        # Assert product
        self.assertEqual(1, Product.objects.get(pk=p.pk).ai_pics_count)

    def test_should_limit_file_count(self):
        p = ProductFactory.create(ai_pics_count=0)

        response = self.json_request(
            self.url + "?device_id=TEST-DEVICE-ID",
            data={
                'product_id': p.pk,
                'files_count': 50,
                'file_ext': "png",
                "mime_type": 'image/jpeg',
                'original_width': 1000,
                'original_height': 2000,
                'width': 100,
                'height': 200,
                'device_name': 'TEST-device',
                'flash_used': True,
                'was_portrait': False,
            },
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Forbidden", response.reason_phrase)


class TestGetByCodeV3(TestCase, JsonRequestMixin):
    url = '/a/v3/get_by_code'

    def test_should_return_200_for_non_ean_13(self):
        response = self.json_request(self.url + "?device_id=TEST-DEVICE-ID&code=123",)
        self.assertEqual(200, response.status_code)

    def test_should_return_200_when_ai_not_supported(self):
        response = self.json_request(self.url + "?device_id=TEST-DEVICE-ID&code=123&noai=false",)
        self.assertEqual(200, response.status_code)

    def test_should_return_200_when_polish_product(self):
        response = self.json_request(self.url + "?device_id=TEST-DEVICE-ID&code=5900049011829")
        self.assertEqual(200, response.status_code, response.content)

    def test_should_return_200_when_product_without_company(self):
        p = Product(code=5900049011829)
        p.name = "test-product"
        p.save()

        response = self.json_request(self.url + "?device_id=TEST-DEVICE-ID&code=" + str(p.code))
        self.assertEqual(200, response.status_code, response.content)

    def test_should_return_200_when_polish_and_known_product(self):
        p = ProductFactory.create(
            code=5900049011829,
            company__plCapital=100,
            company__plWorkers=0,
            company__plRnD=100,
            company__plRegistered=100,
            company__plNotGlobEnt=100,
            company__description="TEST",
            company__sources="TEST|BBBB",
            company__verified=True,
            company__is_friend=True,
            company__plCapital_notes="AAA",
            company__plWorkers_notes="BBB",
            company__plRnD_notes="CCC",
            company__plRegistered_notes="DDD",
            company__plNotGlobEnt_notes="EEE",
        )
        response = self.json_request(self.url + "?device_id=TEST-DEVICE-ID&code=" + str(p.code))
        self.assertEqual(200, response.status_code, response.content)


class TestCreateReportV3(TestCase, JsonRequestMixin):
    url = '/a/v3/create_report'

    def test_should_create_report(self):
        p = ProductFactory.create(ai_pics_count=0)

        response = self.json_request(
            self.url + "?device_id=TEST-DEVICE-ID",
            data={
                'description': "test-description",
                'product_id': p.pk,
                'files_count': 1,
                'file_ext': 'jpg',
                'mime_type': 'image/jpeg',
            },
        )
        self.assertEqual(200, response.status_code)
        response_data = response.json()
        self.assertEqual(len(response_data['signed_requests']), 1)
        signed_url: str = response_data['signed_requests'][0]
        self.assertTrue(signed_url.startswith("http://minio:9000"))

        # Valid signed URL
        response = requests.put(
            signed_url, data=_create_image(), headers={"x-amz-acl": "public-read", 'Content-Type': 'image/jpeg'}
        )
        self.assertEqual(200, response.status_code, response.text)

        # Assert Report
        self.assertEqual(Report.objects.count(), 1)
        report: Report = Report.objects.get(pk=response_data['id'])
        self.assertEqual(p.pk, report.product_id)
        self.assertEqual("test-description", report.description)
        self.assertEqual("TEST-DEVICE-ID", report.client)
        self.assertEqual(Report.OPEN, report.status())

        # Assert Attachment
        self.assertEqual(1, Attachment.objects.count())
        report = Attachment.objects.first()
        self.assertTrue(report.attachment.name.endswith("jpg"))
        self.assertEqual(200, requests.get(report.get_absolute_url()).status_code)

    def test_should_limit_file_count(self):
        p = ProductFactory.create(ai_pics_count=0)

        response = self.json_request(
            self.url + "?device_id=TEST-DEVICE-ID",
            data={
                'description': "test-description",
                'product_id': p.pk,
                'files_count': 50,
                'file_ext': 'jpg',
                'mime_type': 'image/jpeg',
            },
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Forbidden", response.reason_phrase)


class TestGetByCodeV2(TestCase, JsonRequestMixin):
    url = '/a/v2/get_by_code'

    def test_should_return_200_for_non_ean_13(self):
        response = self.json_request(self.url + "?device_id=TEST-DEVICE-ID&code=123",)
        self.assertEqual(200, response.status_code)

    def test_should_return_200_when_polish_and_known_product(self):
        p = ProductFactory.create(
            code=5900049011829,
            company__plCapital=100,
            company__plWorkers=0,
            company__plRnD=100,
            company__plRegistered=100,
            company__plNotGlobEnt=100,
            company__description="KOTEK",
            company__sources="KOTEK|BBBB",
            company__verified=True,
            company__is_friend=True,
            company__plCapital_notes="AA",
            company__plWorkers_notes="BBB",
            company__plRnD_notes="CCC",
            company__plRegistered_notes="DDD",
            company__plNotGlobEnt_notes="EEEE",
        )
        response = self.json_request(self.url + "?device_id=TEST-DEVICE-ID&code=" + str(p.code))
        self.assertEqual(200, response.status_code)


class TestCreateReportV2(TestCase, JsonRequestMixin):
    url = '/a/v2/create_report'

    def test_should_return_200_for_non_ean_13(self):
        response = self.json_request(
            self.url + "?device_id=TEST-DEVICE-ID&report_id=123", data={'description': "test-description"}
        )
        self.assertEqual(200, response.status_code)


class TestUpdateReportV2(TestCase, JsonRequestMixin):
    url = '/a/v2/update_report'

    def test_should_return_200_for_non_ean_13(self):
        report = ReportFactory.create(client="TEST-DEVICE-ID")

        response = self.json_request(
            self.url + "?device_id=TEST-DEVICE-ID&&report_id=" + str(report.pk),
            data={'description': "test-description"},
        )
        self.assertEqual(200, response.status_code)


class TestAttachFileV2(TestCase, JsonRequestMixin):
    url = '/a/v2/attach_file'

    def test_should_return_200_for_non_ean_13(self):
        report = ReportFactory.create(client="TEST-DEVICE-ID")
        response = self.json_request(
            self.url + "?device_id=TEST-DEVICE-ID&report_id=" + str(report.pk),
            data={'file_ext': 'png', 'mime_type': 'AAA'},
        )
        self.assertEqual(200, response.status_code)
