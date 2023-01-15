"""
Serializers for the recipe app
"""
from rest_framework import serializers

from core.models import Recipe
from core.models import Tag


class TagSerializer(serializers.ModelSerializer):
    """ Serializer for tag objects """

    class Meta:
        model = Tag

        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    """ Serializer for tag objects """
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Recipe

        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags']
        read_only_fields = ['id']

    def _get_or_create_tags(self, recipe, tags):
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag
            )
            recipe.tags.add(tag_obj)

    def create(self, validated_data):
        """ Create a new recipe """
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(recipe, tags)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(instance, tags)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """ Serializer for recipe detail """

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
