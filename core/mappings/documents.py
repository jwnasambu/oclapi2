from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from pydash import get

from core.mappings.models import Mapping


@registry.register_document
class MappingDocument(Document):
    class Index:
        name = 'mappings'
        settings = {'number_of_shards': 1, 'number_of_replicas': 0}

    class Django:
        model = Mapping
        fields = [
            'external_id'
        ]

    last_update = fields.DateField(attr='updated_at')
    owner = fields.KeywordField(attr='owner_name', normalizer="lowercase")
    owner_type = fields.KeywordField(attr='owner_type')
    source = fields.KeywordField(attr='source', normalizer="lowercase")
    retired = fields.KeywordField(attr='retired')
    is_active = fields.KeywordField(attr='is_active')
    is_latest_version = fields.KeywordField(attr='is_latest_version')
    map_type = fields.KeywordField(attr='map_type', normalizer="lowercase")
    from_concept = fields.ListField(fields.KeywordField())
    to_concept = fields.ListField(fields.KeywordField())
    concept = fields.ListField(fields.KeywordField())
    concept_source = fields.ListField(fields.KeywordField())
    concept_owner = fields.ListField(fields.KeywordField())
    from_concept_owner = fields.KeywordField(attr='from_source_owner')
    to_concept_owner = fields.KeywordField(attr='to_source_owner')
    concept_owner_type = fields.ListField(fields.KeywordField(attr='to_source_owner'))
    from_concept_owner_type = fields.KeywordField(attr='from_source_owner_type')
    to_concept_owner_type = fields.KeywordField(attr='to_source_owner_type')
    from_concept_source = fields.KeywordField(attr='from_source_name')
    to_concept_source = fields.KeywordField(attr='to_source_name')
    source_version = fields.ListField(fields.KeywordField())
    collection_version = fields.ListField(fields.KeywordField())
    collection = fields.ListField(fields.KeywordField())
    collection_owner_url = fields.ListField(fields.KeywordField())
    public_can_view = fields.BooleanField(attr='public_can_view')
    id = fields.KeywordField(attr='mnemonic', normalizer="lowercase")
    extras = fields.ObjectField()

    @staticmethod
    def prepare_from_concept(instance):
        from_concept_name = get(instance, 'from_concept_name') or get(instance, 'from_concept.display_name')
        return [instance.from_concept_url, instance.from_concept_code, from_concept_name]

    @staticmethod
    def prepare_to_concept(instance):
        return [instance.get_to_concept_code(), instance.get_to_concept_name()]

    def prepare_concept(self, instance):
        return self.prepare_from_concept(instance) + self.prepare_to_concept(instance)

    @staticmethod
    def prepare_concept_source(instance):
        return [instance.from_source_name, instance.to_source_name]

    @staticmethod
    def prepare_concept_owner(instance):
        return [instance.from_source_owner, instance.to_source_owner]

    @staticmethod
    def prepare_concept_owner_type(instance):
        return [instance.from_source_owner_type, instance.to_source_owner_type]

    @staticmethod
    def prepare_source_version(instance):
        return list(instance.sources.values_list('version', flat=True))

    @staticmethod
    def prepare_collection_version(instance):
        return list(instance.collection_set.values_list('version', flat=True))

    @staticmethod
    def prepare_collection(instance):
        return list(set(list(instance.collection_set.values_list('mnemonic', flat=True))))

    @staticmethod
    def prepare_collection_owner_url(instance):
        return list({coll.parent_url for coll in instance.collection_set.select_related('user', 'organization')})

    @staticmethod
    def prepare_extras(instance):
        return instance.extras or {}
