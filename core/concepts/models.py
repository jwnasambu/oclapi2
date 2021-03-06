from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError, transaction
from django.db.models import F
from pydash import get, compact

from core.common.constants import ISO_639_1, INCLUDE_RETIRED_PARAM
from core.common.mixins import SourceChildMixin
from core.common.models import VersionedModel
from core.common.utils import reverse_resource, parse_updated_since_param, generate_temp_version
from core.concepts.constants import CONCEPT_TYPE, LOCALES_FULLY_SPECIFIED, LOCALES_SHORT, LOCALES_SEARCH_INDEX_TERM, \
    CONCEPT_WAS_RETIRED, CONCEPT_IS_ALREADY_RETIRED, CONCEPT_IS_ALREADY_NOT_RETIRED, CONCEPT_WAS_UNRETIRED, \
    PERSIST_CLONE_ERROR, PERSIST_CLONE_SPECIFY_USER_ERROR, ALREADY_EXISTS
from core.concepts.mixins import ConceptValidationMixin


class LocalizedText(models.Model):
    class Meta:
        db_table = 'localized_texts'

    id = models.BigAutoField(primary_key=True)
    internal_reference_id = models.CharField(max_length=255, null=True, blank=True)
    external_id = models.TextField(null=True, blank=True)
    name = models.TextField()
    type = models.TextField(null=True, blank=True)
    locale = models.TextField()
    locale_preferred = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.internal_reference_id and self.id:
            self.internal_reference_id = str(self.id)
        super().save(force_insert, force_update, using, update_fields)

    def clone(self):
        return LocalizedText(
            external_id=self.external_id,
            name=self.name,
            type=self.type,
            locale=self.locale,
            locale_preferred=self.locale_preferred
        )

    @classmethod
    def build(cls, params, used_as='name'):
        instance = None
        if used_as == 'name':
            instance = cls.build_name(params)
        if used_as == 'description':
            instance = cls.build_description(params)

        return instance

    @classmethod
    def build_name(cls, params):
        _type = params.pop('type', None)
        name_type = params.pop('name_type', None)
        if not name_type or name_type == 'ConceptName':
            name_type = _type

        return cls(
            **{**params, 'type': name_type}
        )

    @classmethod
    def build_description(cls, params):
        _type = params.pop('type', None)
        description_type = params.pop('description_type', None)
        if not description_type or description_type == 'ConceptDescription':
            description_type = _type

        description_name = params.pop('description', None) or params.pop('name', None)
        return cls(
            **{
                **params,
                'type': description_type,
                'name': description_name,
            }
        )

    @classmethod
    def build_locales(cls, locale_params, used_as='name'):
        if not locale_params:
            return []

        return [cls.build(locale, used_as) for locale in locale_params]

    @property
    def is_fully_specified(self):
        return self.type in LOCALES_FULLY_SPECIFIED

    @property
    def is_short(self):
        return self.type in LOCALES_SHORT

    @property
    def is_search_index_term(self):
        return self.type in LOCALES_SEARCH_INDEX_TERM


class Concept(ConceptValidationMixin, SourceChildMixin, VersionedModel):  # pylint: disable=too-many-public-methods
    class Meta:
        db_table = 'concepts'
        unique_together = ('mnemonic', 'version', 'parent')

    external_id = models.TextField(null=True, blank=True)
    concept_class = models.TextField()
    datatype = models.TextField()
    names = models.ManyToManyField(LocalizedText, related_name='name_locales')
    descriptions = models.ManyToManyField(LocalizedText, related_name='description_locales')
    comment = models.TextField(null=True, blank=True)
    parent = models.ForeignKey('sources.Source', related_name='concepts_set', on_delete=models.CASCADE)
    sources = models.ManyToManyField('sources.Source', related_name='concepts')
    versioned_object = models.ForeignKey(
        'self', related_name='versions_set', null=True, blank=True, on_delete=models.CASCADE
    )
    logo_path = None

    OBJECT_TYPE = CONCEPT_TYPE
    ALREADY_RETIRED = CONCEPT_IS_ALREADY_RETIRED
    ALREADY_NOT_RETIRED = CONCEPT_IS_ALREADY_NOT_RETIRED
    WAS_RETIRED = CONCEPT_WAS_RETIRED
    WAS_UNRETIRED = CONCEPT_WAS_UNRETIRED

    @property
    def concept(self):  # for url kwargs
        return self.mnemonic  # pragma: no cover

    @staticmethod
    def get_resource_url_kwarg():
        return 'concept'

    @staticmethod
    def get_version_url_kwarg():
        return 'concept_version'

    @property
    def display_name(self):
        return get(self.preferred_locale, 'name')

    @property
    def display_locale(self):
        return get(self.preferred_locale, 'locale')

    @property
    def preferred_locale(self):
        return self.__get_parent_default_locale_name() or self.__get_parent_supported_locale_name() or \
               self.__get_system_default_locale() or self.__get_preferred_locale() or self.__get_last_created_locale()

    def __get_system_default_locale(self):
        system_default_locale = settings.DEFAULT_LOCALE

        return get(
            self.__names_qs(dict(locale=system_default_locale, locale_preferred=True), 'created_at', 'desc'), '0'
        ) or get(
            self.__names_qs(dict(locale=system_default_locale), 'created_at', 'desc'), '0'
        )

    def __get_parent_default_locale_name(self):
        parent_default_locale = self.parent.default_locale
        return get(
            self.__names_qs(dict(locale=parent_default_locale, locale_preferred=True), 'created_at', 'desc'), '0'
        ) or get(
            self.__names_qs(dict(locale=parent_default_locale), 'created_at', 'desc'), '0'
        )

    def __get_parent_supported_locale_name(self):
        parent_supported_locales = self.parent.supported_locales
        return get(
            self.__names_qs(dict(locale__in=parent_supported_locales, locale_preferred=True), 'created_at', 'desc'), '0'
        ) or get(
            self.__names_qs(dict(locale__in=parent_supported_locales), 'created_at', 'desc'), '0'
        )

    def __get_last_created_locale(self):
        return get(self.__names_qs(dict(), 'created_at', 'desc'), '0')

    def __get_preferred_locale(self):
        return get(
            self.__names_qs(dict(locale_preferred=True), 'created_at', 'desc'), '0'
        )

    def __names_qs(self, filters, order_by=None, order='desc'):
        if getattr(self, '_prefetched_objects_cache', None) and \
           'names' in self._prefetched_objects_cache:  # pragma: no cover
            return self.__names_from_prefetched_object_cache(filters, order_by, order)

        return self.__names_from_db(filters, order_by, order)

    def __names_from_db(self, filters, order_by=None, order='desc'):
        names = self.names.filter(
            **filters
        )
        if order_by:
            if order:
                order_by = '-' + order_by if order.lower() == 'desc' else order_by

            names = names.order_by(order_by)

        return names

    def __names_from_prefetched_object_cache(self, filters, order_by=None, order='desc'):  # pragma: no cover
        def is_eligible(name):
            return all([get(name, key) == value for key, value in filters.items()])

        names = list(filter(is_eligible, self.names.all()))
        if order_by:
            names = sorted(names, key=lambda name: get(name, order_by), reverse=(order.lower() == 'desc'))
        return names

    @property
    def default_name_locales(self):
        return self.get_default_locales(self.names)

    @property
    def default_description_locales(self):
        return self.get_default_locales(self.descriptions)

    @staticmethod
    def get_default_locales(locales):
        return locales.filter(locale=settings.DEFAULT_LOCALE)

    @property
    def names_for_default_locale(self):
        return list(self.default_name_locales.values_list('name', flat=True))

    @property
    def descriptions_for_default_locale(self):
        return list(self.default_description_locales.values_list('name', flat=True))

    @property
    def iso_639_1_locale(self):
        return get(self.__names_qs(dict(type=ISO_639_1)), '0.name')

    @property
    def custom_validation_schema(self):
        return get(self, 'parent.custom_validation_schema')

    @property
    def versions_url(self):
        return reverse_resource(self, 'concept-version-list')

    @property
    def all_names(self):
        return list(self.names.values_list('name', flat=True))

    @property
    def saved_unsaved_descriptions(self):
        unsaved_descriptions = get(self, 'cloned_descriptions', [])
        if self.id:
            return compact([*list(self.descriptions.all()), *unsaved_descriptions])
        return unsaved_descriptions

    @property
    def saved_unsaved_names(self):
        unsaved_names = get(self, 'cloned_names', [])

        if self.id:
            return compact([*list(self.names.all()), *unsaved_names])

        return unsaved_names

    @classmethod
    def get_base_queryset(cls, params, distinct_by='updated_at'):  # pylint: disable=too-many-branches
        queryset = cls.objects.filter(is_active=True)
        user = params.get('user', None)
        org = params.get('org', None)
        collection = params.get('collection', None)
        source = params.get('source', None)
        container_version = params.get('version', None)
        concept = params.get('concept', None)
        concept_version = params.get('concept_version', None)
        is_latest = params.get('is_latest', None) in [True, 'true']
        uri = params.get('uri', None)
        include_retired = params.get(INCLUDE_RETIRED_PARAM, None) in [True, 'true']
        updated_since = parse_updated_since_param(params)

        if collection:
            queryset = queryset.filter(cls.get_iexact_or_criteria('collection_set__mnemonic', collection))
            if user:
                queryset = queryset.filter(cls.get_iexact_or_criteria('collection_set__user__username', user))
            if org:
                queryset = queryset.filter(cls.get_iexact_or_criteria('collection_set__organization__mnemonic', org))
            if container_version:
                queryset = queryset.filter(cls.get_iexact_or_criteria('collection_set__version', container_version))
        if source:
            queryset = queryset.filter(cls.get_iexact_or_criteria('sources__mnemonic', source))
            if user:
                queryset = queryset.filter(cls.get_iexact_or_criteria('parent__user__username', user))
            if org:
                queryset = queryset.filter(cls.get_iexact_or_criteria('parent__organization__mnemonic', org))
            if container_version:
                queryset = queryset.filter(cls.get_iexact_or_criteria('sources__version', container_version))

        if concept:
            queryset = queryset.filter(mnemonic__iexact=concept)
        if concept_version:
            queryset = queryset.filter(cls.get_iexact_or_criteria('version', concept_version))
        if is_latest:
            queryset = queryset.filter(is_latest_version=True)
        if not include_retired and not concept:
            queryset = queryset.filter(retired=False)
        if updated_since:
            queryset = queryset.filter(updated_at__gte=updated_since)
        if uri:
            queryset = queryset.filter(uri__icontains=uri)

        if distinct_by:
            queryset = queryset.distinct(distinct_by)

        return queryset

    def clone(self):
        concept_version = Concept(
            mnemonic=self.mnemonic,
            version=generate_temp_version(),
            public_access=self.public_access,
            external_id=self.external_id,
            concept_class=self.concept_class,
            datatype=self.datatype,
            retired=self.retired,
            released=self.released,
            extras=self.extras or dict(),
            parent=self.parent,
            is_latest_version=self.is_latest_version,
            parent_id=self.parent_id,
            versioned_object_id=self.versioned_object_id,
        )
        concept_version.cloned_names = self.__clone_name_locales()
        concept_version.cloned_descriptions = self.__clone_description_locales()

        return concept_version

    @classmethod
    def version_for_concept(cls, concept, version_label, parent_version=None):
        version = concept.clone()
        version.version = version_label
        version.created_by_id = concept.created_by_id
        version.updated_by_id = concept.updated_by_id
        if parent_version:
            version.parent = parent_version
        version.released = False

        return version

    @classmethod
    def create_initial_version(cls, concept, **kwargs):
        initial_version = cls.version_for_concept(concept, generate_temp_version())
        initial_version.save(**kwargs)
        initial_version.version = initial_version.id
        initial_version.released = True
        initial_version.is_latest_version = True
        initial_version.save()
        return initial_version

    @classmethod
    def create_new_version_for(cls, instance, data, user):
        instance.concept_class = data.get('concept_class', instance.concept_class)
        instance.datatype = data.get('datatype', instance.datatype)
        instance.extras = data.get('extras', instance.extras)
        instance.external_id = data.get('external_id', instance.external_id)
        instance.comment = data.get('update_comment') or data.get('comment')
        instance.retired = data.get('retired', instance.retired)

        new_names = LocalizedText.build_locales(data.get('names', []))
        new_descriptions = LocalizedText.build_locales(data.get('descriptions', []), 'description')

        instance.cloned_names = compact(new_names)
        instance.cloned_descriptions = compact(new_descriptions)

        return cls.persist_clone(instance, user)

    def set_locales(self):
        if not self.id:
            return  # pragma: no cover

        names = get(self, 'cloned_names', [])
        descriptions = get(self, 'cloned_descriptions', [])

        for name in names:
            name.save()
        for desc in descriptions:
            desc.save()

        self.names.set(names)
        self.descriptions.set(descriptions)
        self.cloned_names = []
        self.cloned_descriptions = []

    def remove_locales(self):
        self.names.all().delete()
        self.descriptions.all().delete()

    def __clone_name_locales(self):
        return self.__clone_locales(self.names)

    def __clone_description_locales(self):
        return self.__clone_locales(self.descriptions)

    @staticmethod
    def __clone_locales(locales):
        return [locale.clone() for locale in locales.all()]

    def is_existing_in_parent(self):
        return self.parent.concepts_set.filter(mnemonic__iexact=self.mnemonic).exists()

    @classmethod
    def persist_new(cls, data, user=None, create_initial_version=True):
        names = [
            name if isinstance(name, LocalizedText) else LocalizedText.build(
                name
            ) for name in data.pop('names', []) or []
        ]
        descriptions = [
            desc if isinstance(desc, LocalizedText) else LocalizedText.build(
                desc, 'description'
            ) for desc in data.pop('descriptions', []) or []
        ]
        concept = Concept(**data)
        concept.version = generate_temp_version()
        if user:
            concept.created_by = concept.updated_by = user
        concept.errors = dict()
        if concept.is_existing_in_parent():
            concept.errors = dict(__all__=[ALREADY_EXISTS])
            return concept

        try:
            concept.cloned_names = names
            concept.cloned_descriptions = descriptions
            concept.full_clean()
            concept.save()
            concept.versioned_object_id = concept.id
            concept.version = str(concept.id)
            concept.is_latest_version = not create_initial_version
            concept.save()
            concept.set_locales()
            parent_resource = concept.parent
            parent_resource_head = parent_resource.head

            if create_initial_version:
                initial_version = cls.create_initial_version(concept)
                initial_version.set_locales()
                initial_version.sources.set([parent_resource, parent_resource_head])

            concept.sources.set([parent_resource, parent_resource_head])
            concept.update_mappings()
        except ValidationError as ex:
            concept.errors.update(ex.message_dict)
        except IntegrityError as ex:
            concept.errors.update(dict(__all__=ex.args))

        return concept

    def update_versioned_object(self):
        concept = self.versioned_object
        concept.extras = self.extras
        concept.names.set(self.names.all())
        concept.descriptions.set(self.descriptions.all())
        concept.concept_class = self.concept_class
        concept.datatype = self.datatype
        concept.retired = self.retired
        concept.external_id = self.external_id or concept.external_id
        concept.save()

    @classmethod
    def persist_clone(cls, obj, user=None, **kwargs):  # pylint: disable=too-many-statements
        errors = dict()
        if not user:
            errors['version_created_by'] = PERSIST_CLONE_SPECIFY_USER_ERROR
            return errors
        obj.created_by = user
        obj.updated_by = user
        obj.version = obj.version or generate_temp_version()
        parent = obj.parent
        parent_head = parent.head
        persisted = False
        latest_version = None
        try:
            with transaction.atomic():
                cls.pause_indexing()

                obj.is_latest_version = True
                obj.save(**kwargs)
                if obj.id:
                    obj.version = str(obj.id)
                    obj.save()
                    obj.set_locales()
                    obj.clean()  # clean here to validate locales that can only be saved after obj is saved
                    obj.update_versioned_object()
                    versioned_object = obj.versioned_object
                    latest_version = versioned_object.versions.exclude(id=obj.id).filter(is_latest_version=True).first()
                    if latest_version:
                        latest_version.is_latest_version = False
                        latest_version.save()

                    obj.sources.set(compact([parent, parent_head]))
                    persisted = True
                    cls.resume_indexing()

                    def index_all():
                        if latest_version:
                            latest_version.save()
                        obj.save()

                    transaction.on_commit(index_all)
        except ValidationError as err:
            errors.update(err.message_dict)
        finally:
            cls.resume_indexing()
            if not persisted:
                if latest_version:
                    latest_version.is_latest_version = True
                    latest_version.save()
                if obj.id:
                    obj.remove_locales()
                    obj.sources.remove(parent_head)
                    obj.delete()
                errors['non_field_errors'] = [PERSIST_CLONE_ERROR]

        return errors

    def get_unidirectional_mappings(self):
        return self.__get_mappings_from_relation('mappings_from')

    def get_latest_unidirectional_mappings(self):
        return self.__get_mappings_from_relation('mappings_from', True)

    def get_indirect_mappings(self):
        return self.__get_mappings_from_relation('mappings_to')

    def __get_mappings_from_relation(self, relation_manager, is_latest=False):
        queryset = getattr(self, relation_manager).filter(parent_id=self.parent_id)

        if self.is_versioned_object:
            latest_version = self.get_latest_version()
            if latest_version:
                queryset |= getattr(latest_version, relation_manager).filter(parent_id=self.parent_id)
        if self.is_latest_version:
            versioned_object = self.versioned_object
            if versioned_object:
                queryset |= getattr(versioned_object, relation_manager).filter(parent_id=self.parent_id)

        if is_latest:
            return queryset.filter(is_latest_version=True)

        return queryset.filter(id=F('versioned_object_id')).order_by('-updated_at').distinct('updated_at')

    def get_bidirectional_mappings(self):
        queryset = self.get_unidirectional_mappings() | self.get_indirect_mappings()

        return queryset.distinct()

    @staticmethod
    def get_latest_versions_for_queryset(concepts_qs):
        """Takes any concepts queryset and returns queryset of latest_version of each of those concepts"""

        if concepts_qs is None or not concepts_qs.exists():
            return Concept.objects.none()

        criteria_fields = list(concepts_qs.values('parent_id', 'mnemonic'))
        criterion = [models.Q(**attrs, is_latest_version=True) for attrs in criteria_fields]
        query = criterion.pop()
        for criteria in criterion:
            query |= criteria

        return Concept.objects.filter(query)

    def update_mappings(self):
        from core.mappings.models import Mapping
        parent_uris = compact([self.parent.uri, self.parent.canonical_url])
        for mapping in Mapping.objects.filter(
                to_concept_code=self.mnemonic, to_source_url__in=parent_uris, to_concept__isnull=True
        ):
            mapping.to_concept = self
            mapping.save()

        for mapping in Mapping.objects.filter(
                from_concept_code=self.mnemonic, from_source_url__in=parent_uris, from_concept__isnull=True
        ):
            mapping.from_concept = self
            mapping.save()
