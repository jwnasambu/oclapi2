import uuid

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from pydash import get
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from core.common.constants import NAMESPACE_REGEX, INCLUDE_SUBSCRIBED_ORGS
from .models import UserProfile


class UserListSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = (
            'username', 'name', 'url'
        )


class UserCreateSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='resource_type', read_only=True)
    uuid = serializers.CharField(source='id', read_only=True)
    username = serializers.CharField(required=True, validators=[
        RegexValidator(regex=NAMESPACE_REGEX),
        UniqueValidator(queryset=UserProfile.objects.all(), message='A user with this username already exists')
    ])
    name = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False, write_only=True)
    last_name = serializers.CharField(required=False, write_only=True)
    email = serializers.CharField(required=True, validators=[
        UniqueValidator(queryset=UserProfile.objects.all(), message='A user with this email already exists')
    ])
    password = serializers.CharField(required=False, write_only=True)
    company = serializers.CharField(required=False)
    location = serializers.CharField(required=False)
    preferred_locale = serializers.CharField(required=False)
    orgs = serializers.IntegerField(read_only=True, source='orgs_count')
    created_on = serializers.DateTimeField(source='created_at', read_only=True)
    updated_on = serializers.DateTimeField(source='updated_at', read_only=True)
    created_by = serializers.CharField(read_only=True)
    updated_by = serializers.CharField(read_only=True)
    extras = serializers.JSONField(required=False, allow_null=True)
    token = serializers.CharField(required=False, read_only=True)
    verified = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = UserProfile
        fields = (
            'type', 'uuid', 'username', 'name', 'email', 'company', 'location', 'preferred_locale', 'orgs',
            'public_collections', 'public_sources', 'created_on', 'updated_on', 'created_by', 'updated_by',
            'url', 'extras', 'password', 'token', 'verified', 'first_name', 'last_name'
        )

    def create(self, validated_data):
        requesting_user = self.context['request'].user
        if requesting_user and requesting_user.is_anonymous:
            requesting_user = None
        username = validated_data.get('username')
        existing_profile = UserProfile.objects.filter(username=username)
        if existing_profile.exists():
            self._errors['username'] = 'User with username %s already exists.' % username
            user = existing_profile.first()
            user.token = user.get_token()
            return user

        user = UserProfile(
            username=username, email=validated_data.get('email'), company=validated_data.get('company', None),
            location=validated_data.get('location', None), extras=validated_data.get('extras', None),
            preferred_locale=validated_data.get('preferred_locale', None),
            first_name=validated_data.get('name', None) or validated_data.get('first_name'),
            last_name=validated_data.get('last_name', '')
        )
        password = validated_data.get('password', None)

        try:
            validate_password(password)
        except ValidationError as ex:
            self._errors['password'] = ex.messages
            return user

        user.set_password(password)

        if requesting_user:
            user.created_by = user.updated_by = requesting_user
        if 'verified' in validated_data:
            user.verified = validated_data['verified']
            if not user.verified:
                user.verification_token = uuid.uuid4()

        user.save()
        user.token = user.get_token()
        user.send_verification_email()

        return user


class UserDetailSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='resource_type', read_only=True)
    uuid = serializers.CharField(source='id', read_only=True)
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    company = serializers.CharField(required=False)
    website = serializers.CharField(required=False)
    location = serializers.CharField(required=False)
    preferred_locale = serializers.CharField(required=False)
    orgs = serializers.IntegerField(read_only=True, source='orgs_count')
    created_on = serializers.DateTimeField(source='created_at', read_only=True)
    updated_on = serializers.DateTimeField(source='updated_at', read_only=True)
    created_by = serializers.CharField(read_only=True)
    updated_by = serializers.CharField(read_only=True)
    extras = serializers.JSONField(required=False, allow_null=True)
    subscribed_orgs = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = (
            'type', 'uuid', 'username', 'name', 'email', 'company', 'location', 'preferred_locale', 'orgs',
            'public_collections', 'public_sources', 'created_on', 'updated_on', 'created_by', 'updated_by',
            'url', 'organizations_url', 'extras', 'sources_url', 'collections_url', 'website', 'last_login',
            'logo_url', 'subscribed_orgs', 'is_superuser', 'is_staff', 'first_name', 'last_name', 'verified',
        )

    def __init__(self, *args, **kwargs):
        params = get(kwargs, 'context.request.query_params')
        self.include_subscribed_orgs = False
        if params:
            self.query_params = params.dict()
            self.include_subscribed_orgs = self.query_params.get(INCLUDE_SUBSCRIBED_ORGS) in ['true', True]
        if not self.include_subscribed_orgs:
            self.fields.pop('subscribed_orgs')

        super().__init__(*args, **kwargs)

    def get_subscribed_orgs(self, obj):
        if self.include_subscribed_orgs:
            from core.orgs.serializers import OrganizationListSerializer
            return OrganizationListSerializer(obj.organizations.all(), many=True).data

        return None

    def update(self, instance, validated_data):
        request_user = self.context['request'].user
        instance.email = validated_data.get('email', instance.email)
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.company = validated_data.get('company', instance.company)
        instance.website = validated_data.get('website', instance.website)
        instance.location = validated_data.get('location', instance.location)
        instance.preferred_locale = validated_data.get('preferred_locale', instance.preferred_locale)
        instance.extras = validated_data.get('extras', instance.extras)
        instance.updated_by = request_user
        instance.save()
        return instance
