from pydash import get
from rest_framework.fields import CharField, JSONField, IntegerField, DateTimeField
from rest_framework.serializers import ModelSerializer

from core.common.constants import MAPPING_LOOKUP_CONCEPTS, MAPPING_LOOKUP_SOURCES, MAPPING_LOOKUP_FROM_CONCEPT, \
    MAPPING_LOOKUP_TO_CONCEPT, MAPPING_LOOKUP_FROM_SOURCE, MAPPING_LOOKUP_TO_SOURCE, INCLUDE_EXTRAS_PARAM
from core.concepts.serializers import ConceptListSerializer, ConceptDetailSerializer
from core.mappings.models import Mapping
from core.sources.serializers import SourceListSerializer, SourceDetailSerializer


class MappingListSerializer(ModelSerializer):
    id = CharField(source='mnemonic', required=False)
    uuid = CharField(source='id', read_only=True)
    source = CharField(source='parent_resource', read_only=True)
    owner = CharField(source='owner_name', read_only=True)
    update_comment = CharField(source='comment', required=False, allow_null=True, allow_blank=True)
    url = CharField(required=False, source='versioned_object_url')
    version = CharField(read_only=True)
    version_created_on = DateTimeField(source='created_at', read_only=True)
    from_concept = ConceptListSerializer()
    to_concept = ConceptListSerializer()
    from_source = SourceListSerializer()
    to_source = SourceListSerializer()
    from_concept_name_resolved = CharField(source='from_concept.display_name', read_only=True)
    to_concept_name_resolved = CharField(source='to_concept.display_name', read_only=True)

    class Meta:
        model = Mapping
        fields = (
            'external_id', 'retired', 'map_type', 'source', 'owner', 'owner_type',
            'from_concept_code', 'from_concept_name', 'from_concept_url',
            'to_concept_code', 'to_concept_name', 'to_concept_url',
            'from_source_owner', 'from_source_owner_type', 'from_source_url', 'from_source_name',
            'to_source_owner', 'to_source_owner_type', 'to_source_url', 'to_source_name',
            'url', 'version', 'id', 'versioned_object_id', 'versioned_object_url',
            'is_latest_version', 'update_comment', 'version_url', 'uuid', 'version_created_on',
            'from_source_version', 'to_source_version', 'from_concept', 'to_concept', 'from_source', 'to_source',
            'from_concept_name_resolved', 'to_concept_name_resolved', 'extras',
        )

    def __init__(self, *args, **kwargs):
        params = get(kwargs, 'context.request.query_params')
        self.query_params = params.dict() if params else dict()
        self.include_from_source = self.query_params.get(MAPPING_LOOKUP_FROM_SOURCE) in ['true', True]
        self.include_to_source = self.query_params.get(MAPPING_LOOKUP_TO_SOURCE) in ['true', True]
        self.include_sources = self.query_params.get(MAPPING_LOOKUP_SOURCES) in ['true', True]
        self.include_from_concept = self.query_params.get(MAPPING_LOOKUP_FROM_CONCEPT) in ['true', True]
        self.include_to_concept = self.query_params.get(MAPPING_LOOKUP_TO_CONCEPT) in ['true', True]
        self.include_concepts = self.query_params.get(MAPPING_LOOKUP_CONCEPTS) in ['true', True]

        self.include_extras = self.query_params.get(INCLUDE_EXTRAS_PARAM) in ['true', True]

        if not self.include_concepts:
            if not self.include_from_concept:
                self.fields.pop('from_concept')
            if not self.include_to_concept:
                self.fields.pop('to_concept')

        if not self.include_sources:
            if not self.include_from_source:
                self.fields.pop('from_source')
            if not self.include_to_source:
                self.fields.pop('to_source')

        if not self.include_extras and self.__class__.__name__ in [
            'MappingListSerializer', 'MappingVersionListSerializer'
        ]:
            self.fields.pop('extras', None)

        super().__init__(*args, **kwargs)


class MappingVersionListSerializer(MappingListSerializer):
    previous_version_url = CharField(read_only=True, source='prev_version_uri')

    class Meta:
        model = Mapping
        fields = MappingListSerializer.Meta.fields + ('previous_version_url',)


class MappingDetailSerializer(MappingListSerializer):
    type = CharField(source='resource_type', read_only=True)
    uuid = CharField(source='id', read_only=True)
    extras = JSONField(required=False, allow_null=True)
    created_by = CharField(source='created_by.username', read_only=True)
    updated_by = CharField(source='created_by.username', read_only=True)
    parent_id = IntegerField(required=True)
    map_type = CharField(required=True)
    to_concept_url = CharField(required=False)
    from_concept_url = CharField(required=False)
    previous_version_url = CharField(read_only=True, source='prev_version_uri')
    from_concept = ConceptDetailSerializer()
    to_concept = ConceptDetailSerializer()
    from_source = SourceDetailSerializer()
    to_source = SourceDetailSerializer()
    created_on = DateTimeField(source='created_at', read_only=True)
    updated_on = DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Mapping
        fields = MappingListSerializer.Meta.fields + (
            'type', 'uuid', 'extras', 'created_on', 'updated_on',
            'created_by', 'updated_by', 'parent_id', 'previous_version_url',
        )
        extra_kwargs = {'parent_id': {'write_only': True}}

    def create(self, validated_data):
        mapping = Mapping.persist_new(data=validated_data, user=self.context.get('request').user)
        if mapping.errors:
            self._errors.update(mapping.errors)
        return mapping

    def update(self, instance, validated_data):
        errors = Mapping.create_new_version_for(instance, validated_data, self.context.get('request').user)
        if errors:
            self._errors.update(errors)
        return instance
