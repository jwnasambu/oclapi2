from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from core.pins.models import Pin


class PinUpdateSerializer(serializers.ModelSerializer):
    order = serializers.IntegerField(required=False)
    resource = SerializerMethodField()

    class Meta:
        model = Pin
        fields = (
            'id', 'created_at', 'resource_uri', 'user_id', 'organization_id',
            'resource', 'uri', 'order'
        )

    def update(self, instance, validated_data):
        instance.to(validated_data.get('order', instance.order))
        return instance

    @staticmethod
    def get_resource(obj):
        resource = obj.resource
        if not resource:
            return None
        resource_type = resource.resource_type.lower()
        if resource_type == 'source':
            from core.sources.serializers import SourceDetailSerializer
            return SourceDetailSerializer(resource).data
        if resource_type == 'collection':
            from core.collections.serializers import CollectionDetailSerializer
            return CollectionDetailSerializer(resource).data
        if resource_type == 'organization':
            from core.orgs.serializers import OrganizationDetailSerializer
            return OrganizationDetailSerializer(resource).data

        return None


class PinSerializer(serializers.ModelSerializer):
    resource_type = serializers.CharField(required=True, write_only=True)
    resource_id = serializers.IntegerField(required=True, write_only=True)
    user_id = serializers.IntegerField(required=False, allow_null=True)
    organization_id = serializers.IntegerField(required=False, allow_null=True)
    resource = SerializerMethodField()

    class Meta:
        model = Pin
        fields = (
            'id', 'created_at', 'resource_uri', 'user_id', 'organization_id', 'resource_type', 'resource_id',
            'resource', 'uri', 'order'
        )

    def create(self, validated_data):
        resource_type = validated_data.get('resource_type', '')
        resource_id = validated_data.get('resource_id', '')
        resource = Pin.get_resource(resource_type, resource_id)
        item = Pin(
            user_id=validated_data.get('user_id', None),
            organization_id=validated_data.get('organization_id', None),
            resource=resource,
        )

        if not resource:
            self._errors['resource'] = 'Resource type %s with id %s does not exists.' % (resource_type, resource_id)
            return item

        try:
            item.full_clean()
            item.save()
        except (ValidationError, IntegrityError):
            self._errors.update(dict(__all__='This pin already exists.'))

        return item

    @staticmethod
    def get_resource(obj):
        resource = obj.resource
        if not resource:
            return None
        resource_type = resource.resource_type.lower()
        if resource_type == 'source':
            from core.sources.serializers import SourceDetailSerializer
            return SourceDetailSerializer(resource).data
        if resource_type == 'collection':
            from core.collections.serializers import CollectionDetailSerializer
            return CollectionDetailSerializer(resource).data
        if resource_type == 'organization':
            from core.orgs.serializers import OrganizationDetailSerializer
            return OrganizationDetailSerializer(resource).data

        return None
