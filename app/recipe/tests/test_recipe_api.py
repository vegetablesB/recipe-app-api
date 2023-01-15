""" Tests for the recipe API """
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer, TagSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """ Return recipe detail URL """
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """ Helper function to create a recipe """
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': Decimal('5.00'),
        'description': 'Sample description',
        'link': 'http://www.google.com',
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


def create_user(**params):
    """ Helper function to create a user """
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    """ Test unauthenticated recipe API access """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """ Test that authentication is required """
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """ Test authenticated recipe API access """

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='password')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """ Test retrieving a list of recipes """
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """ Test retrieving recipes for user """
        user2 = create_user(email='test@example.com', password='password123')
        create_recipe(user=user2)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """ Test viewing a recipe detail """
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """ Test creating recipe """
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': Decimal('5.00'),
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_partial_update_recipe(self):
        """ Test updating a recipe with patch """
        original_link = 'http://www.google.com'
        new_link = 'http://www.yahoo.com'
        recipe = create_recipe(
            user=self.user, title='Sampel title', link=original_link)
        payload = {'title': 'New title', 'link': new_link}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, new_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        """ Test updating a recipe with put """
        recipe = create_recipe(
            user=self.user,
            title='Sampel title',
            link='http://www.google.com',
            description='Sample description'
        )
        payload = {
            'title': 'New title',
            'link': 'http://www.yahoo.com',
            'time_minutes': 10,
            'price': Decimal('5.00'),
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, payload['link'])
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """ Test that updating user returns error """
        recipe = create_recipe(user=self.user)
        new_user = create_user(email='tt@example.com', password='password123')
        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        # self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(recipe.user, self.user)
        self.assertNotEqual(recipe.user, new_user)

    def test_delete_recipe(self):
        """ Test deleting a recipe """
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_recipe_returns_error(self):
        """ Test deleting a recipe returns error """
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        self.client.delete(url)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe_error(self):
        """ Test deleting other user's recipe """
        user2 = create_user(email='tt@example.com', password='password123')
        recipe = create_recipe(user=user2)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """ Test creating a recipe with new tags """
        payload = {
            'title': 'Avocado lime cheesecake',
            'tags': [{'name': 'Vegan'}, {'name': 'Desert'}],
            'time_minutes': 60,
            'price': Decimal('20.00'),
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        recipe = recipes[0]

        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            self.assertTrue(recipe.tags.filter(name=tag['name']).exists())

    def test_create_recipe_with_existing_tags(self):
        """ Test creating a recipe with existing tags """
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 60,
            'price': Decimal('20.00'),
            'tags': [{'name': 'Vegan'}, {'name': 'Desert'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag1, recipe.tags.all())
        for tag in payload['tags']:
            self.assertTrue(recipe.tags.filter(name=tag['name']).exists())

    def test_create_tag_on_update(self):
        """ Test creating a tag on update """
        recipe = create_recipe(user=self.user)
        payload = {
            'tags': [{'name': 'Lunch'}],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(name='Lunch')
        # no need to use refresh_from_db() in many to many fields,
        # because it is using subquery to retrieve fresh objects
        # that are not in the cache
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tags(self):
        """ Test updating a recipe with tags """
        recipe = create_recipe(user=self.user)
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        recipe.tags.add(tag1)

        tag2 = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag2, recipe.tags.all())
        self.assertNotIn(tag1, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """ Test clearing tags from recipe """
        recipe = create_recipe(user=self.user)
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        recipe.tags.add(tag1)

        payload = {'tags': []}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
