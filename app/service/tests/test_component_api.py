from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Components, Service
from service.serializers import ComponentSerializers


COMPONENT_URLS = reverse('service:components-list')

class PublicComponentsAPITests(TestCase):
    """ Test this publicly avaliable API """

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """ Test the login is required for retrieving api """

        res = self.client.get(COMPONENT_URLS)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateComponentsApiTests(TestCase):
    """  Test the authorized user """

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@gmail.com',
            'testpassword'
        )
        
        self.client.force_authenticate(self.user)

    def test_retrieve_componentss(self):
        """  Test Retrieving Tags """
        Components.objects.create(user=self.user, name='Fittingjob')
        Components.objects.create(user=self.user, name='Fanrepairing')

        res= self.client.get(COMPONENT_URLS)

        components = Components.objects.all().order_by('-name')

        serializer = ComponentSerializers(components, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_components_limited_to_user(self):
        """  Test thetags that are not authenticated user """

        user2 = get_user_model().objects.create_user(

            'info@test.com',
            'testpassword'
        )
        Components.objects.create(user=user2, name='Fan')
        components = Components.objects.create(user=self.user, name='Shortcut')

        res = self.client.get(COMPONENT_URLS)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

        self.assertEqual(res.data[0]['name'], components.name)

    def test_create_component_successfull(self):
        """ Test Creating a New Componet """

        payload = {'name': 'Test Components'}

        self.client.post(COMPONENT_URLS, payload)

        exists = Components.objects.filter(
            user=self.user,
            name=payload['name']

        ).exists()

        self.assertTrue(exists)

    def test_create_component_invalid(self):
        """ Test Creating a new componet with invalid payload """

        payload = {'name' : ''}
        res = self.client.post(COMPONENT_URLS, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_components_assigned_to_services(self):
        """  Test retrieve components to services """

        component1 = Components.objects.create(user=self.user, name='testcomponent')
        component2 = Components.objects.create(user=self.user, name='testcomponent2')

        services = Service.objects.create(
            title='Testing service',
            price=5.00,
            user=self.user
        )

        services.components.add(component1)
        
        res = self.client.get(COMPONENT_URLS, {'assigned_only': 1})

        serializer1 = ComponentSerializers(component1)
        serializer2 = ComponentSerializers(component2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_components_assigned_with_unique(self):
        """ Test Filtering components by assiged return unique items """

        component = Components.objects.create(user=self.user, name='testtag')
        Components.objects.create(user=self.user, name='testtag2' )
        services1 = Service.objects.create(
            title='testing unique test',
            price=50.00,
            user=self.user
        )
        services1.components.add(component)
        services2 = Service.objects.create(
            title='testing unique test',
            price=10.00,
            user=self.user
        )
        services2.components.add(component)

        res = self.client.get(COMPONENT_URLS, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
