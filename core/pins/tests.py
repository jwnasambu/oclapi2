from django.core.exceptions import ValidationError
from mock import Mock

from core.collections.tests.factories import OrganizationCollectionFactory
from core.common.tests import OCLTestCase, OCLAPITestCase
from core.orgs.models import Organization
from core.orgs.tests.factories import OrganizationFactory
from core.pins.models import Pin
from core.sources.models import Source
from core.sources.tests.factories import OrganizationSourceFactory
from core.users.tests.factories import UserProfileFactory


class PinTest(OCLTestCase):
    def test_clean(self):
        org = OrganizationFactory()
        pin = Pin(resource=org)
        with self.assertRaises(ValidationError) as ex:
            pin.full_clean()

        self.assertEqual(
            ex.exception.message_dict, dict(parent=['Pin needs to be owned by a user or an organization.'])
        )

        pin.organization = org
        pin.full_clean()

    def test_resource_uri(self):
        self.assertEqual(Pin(resource=Organization(uri='/orgs/foo/')).resource_uri, '/orgs/foo/')
        self.assertEqual(Pin(resource=Source(uri='/orgs/foo/sources/bar/')).resource_uri, '/orgs/foo/sources/bar/')

    def test_get_resource(self):
        org = OrganizationFactory()
        source = OrganizationSourceFactory(organization=org)
        collection = OrganizationCollectionFactory(organization=org)

        self.assertEqual(Pin.get_resource(resource_type='Source', resource_id=source.id), source)
        self.assertEqual(Pin.get_resource(resource_type='collection', resource_id=collection.id), collection)
        self.assertEqual(Pin.get_resource(resource_type='org', resource_id=org.id), org)
        self.assertEqual(Pin.get_resource(resource_type='organization', resource_id=org.id), org)
        self.assertEqual(Pin.get_resource(resource_type='organization', resource_id=123), None)
        self.assertEqual(Pin.get_resource(resource_type='foobar', resource_id=123), None)

    def test_parent(self):
        org = OrganizationFactory()
        user = UserProfileFactory()

        self.assertEqual(Pin().parent, None)
        self.assertEqual(Pin(organization=org).parent, org)
        self.assertEqual(Pin(user=user).parent, user)
        self.assertEqual(Pin(user=user, organization=org).parent, org)

    def test_uri(self):
        org = OrganizationFactory(mnemonic='org-1')
        user = UserProfileFactory(username='user-1')

        self.assertEqual(Pin().uri, None)
        self.assertEqual(Pin(id=1, organization=org).uri, '/orgs/org-1/pins/1/')
        self.assertEqual(Pin(id=2, user=user).uri, '/users/user-1/pins/2/')

    def test_soft_delete(self):
        pin = Pin()
        pin.delete = Mock(return_value=True)

        self.assertEqual(pin.soft_delete(), True)
        pin.delete.assert_called_once()


class PinListViewTest(OCLAPITestCase):
    def tearDown(self):
        Pin.objects.all().delete()
        super().tearDown()

    def test_get_200(self):
        source = OrganizationSourceFactory()
        user = UserProfileFactory()
        org = OrganizationFactory()
        token = user.get_token()

        response = self.client.get(
            user.uri + 'pins/',
            HTTP_AUTHORIZATION='Token ' + token,
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        pin1 = user.pins.create(resource=source)
        pin2 = org.pins.create(resource=source)

        response = self.client.get(
            user.uri + 'pins/',
            HTTP_AUTHORIZATION='Token ' + token,
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['resource_uri'], source.uri)
        self.assertEqual(response.data[0]['id'], pin1.id)
        self.assertIsNotNone(response.data[0]['uri'])
        self.assertIsNone(response.data[0]['organization_id'])

        response = self.client.get(
            org.uri + 'pins/',
            HTTP_AUTHORIZATION='Token ' + token,
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['resource_uri'], source.uri)
        self.assertEqual(response.data[0]['id'], pin2.id)
        self.assertEqual(response.data[0]['organization_id'], org.id)
        self.assertIsNotNone(response.data[0]['uri'])
        self.assertIsNone(response.data[0]['user_id'])

    def test_post_201(self):
        source = OrganizationSourceFactory()
        user = UserProfileFactory()
        org = OrganizationFactory()
        token = user.get_token()

        response = self.client.post(
            user.uri + 'pins/',
            dict(resource_type='Source', resource_id=source.id),
            HTTP_AUTHORIZATION='Token ' + token,
            format='json'
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['resource_uri'], source.uri)
        self.assertEqual(response.data['user_id'], user.id)
        self.assertIsNone(response.data['organization_id'])
        self.assertIsNotNone(response.data['resource'])
        self.assertIsNotNone(response.data['uri'])

        response = self.client.post(
            org.uri + 'pins/',
            dict(resource_type='Source', resource_id=source.id),
            HTTP_AUTHORIZATION='Token ' + token,
            format='json'
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['resource_uri'], source.uri)
        self.assertEqual(response.data['organization_id'], org.id)
        self.assertIsNone(response.data['user_id'])
        self.assertIsNotNone(response.data['resource'])
        self.assertIsNotNone(response.data['uri'])

    def test_post_400(self):
        user = UserProfileFactory()
        token = user.get_token()

        response = self.client.post(
            user.uri + 'pins/',
            dict(resource_type='Source', resource_id=1209),
            HTTP_AUTHORIZATION='Token ' + token,
            format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, dict(resource='Resource type Source with id 1209 does not exists.'))


class PinRetrieveDestroyViewTest(OCLAPITestCase):
    def setUp(self):
        self.user = UserProfileFactory()
        self.org = OrganizationFactory()
        self.token = self.user.get_token()
        self.source = OrganizationSourceFactory()
        self.user_pin = self.user.pins.create(resource=self.source)
        self.org_pin = self.org.pins.create(resource=self.source)

    def test_get_200(self):
        response = self.client.get(
            self.user.uri + 'pins/' + str(self.user_pin.id) + '/',
            HTTP_AUTHORIZATION='Token ' + self.token,
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['resource_uri'], self.source.uri)
        self.assertEqual(response.data['resource']['id'], self.source.mnemonic)
        self.assertEqual(response.data['user_id'], self.user.id)

        response = self.client.get(
            self.org.uri + 'pins/' + str(self.org_pin.id) + '/',
            HTTP_AUTHORIZATION='Token ' + self.token,
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['resource_uri'], self.source.uri)
        self.assertEqual(response.data['resource']['id'], self.source.mnemonic)
        self.assertEqual(response.data['organization_id'], self.org.id)

    def test_delete_204(self):
        response = self.client.delete(
            self.org.uri + 'pins/' + str(self.org_pin.id) + '/',
            HTTP_AUTHORIZATION='Token ' + self.token,
            format='json'
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.org.pins.count(), 0)

        response = self.client.delete(
            self.user.uri + 'pins/' + str(self.user_pin.id) + '/',
            HTTP_AUTHORIZATION='Token ' + self.token,
            format='json'
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.user.pins.count(), 0)
